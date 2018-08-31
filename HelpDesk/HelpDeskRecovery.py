__author__ = "Manuel Escriche <mev@tid.es>"

import os, base64, requests, xlsxwriter, re
from datetime import date, datetime
from xlsxwriter.utility import xl_range
from operator import attrgetter
from collections import namedtuple
from _Kernel.Settings import settings
from _Kernel.SheetFormats import SpreadsheetFormats
from Kernel.TrackerBook import trackersBookByKey
from Kernel.IssuesList import IssuesList


class Connector:

    url_api = {
        'session': '/rest/auth/1/session',
        'project': '/rest/api/latest/project',
        'component': '/rest/api/latest/component/',
        'search': '/rest/api/latest/search'
    }
    _singlenton = None

    def __new__(cls, *args, **kwargs):
        if not cls._singlenton:
            cls._singlenton = super(Connector, cls).__new__(cls, *args, **kwargs)
        return cls._singlenton

    def __init__(self):
        self.jiraSession = self._connect(settings.server['JIRA'])
        self.jiraTestSession = self._connect(settings.server['JIRATEST'])

    def _connect(self, server):
        username = server.username
        password = server.password
        auth = '{}:{}'.format(username, password)
        keyword = base64.b64encode(bytes(auth,'utf-8'))
        access_key = str(keyword)[2:-1]
        headers = {'Content-Type': 'application/json', "Authorization": "Basic {}".format(access_key)}
        root_url = 'http://{}'.format(server.domain)

        session = requests.session()

        url = '{}{}'.format(root_url, Connector.url_api['session'])
        try:
            session.get(url, headers = headers, verify=False)
        except Exception:
            raise Exception

        session.headers.update({'Content-Type': 'application/json'})
        return session

    def _search(self, server, params):
        root_url = 'http://{}'.format(server.domain)
        url = '{}{}'.format(root_url, Connector.url_api['search'])
        try:
            answer = self.jiraSession.get(url, params=params, verify=False)
        except Exception:
            raise Exception
        return answer.json()

    def search(self, server, params):
        data = self._search(settings.server[server], params)
        return data


class IssuesFactory:
    fields = 'summary,status,project,components,priority,issuetype,description,reporter,' \
             'resolution,assignee,created,updated,duedate,resolutiondate,fixVersions,releaseDate,issuelinks'
    _singlenton = None

    def __new__(cls, *args, **kwargs):
        if not cls._singlenton:
            cls._singlenton = super(IssuesFactory, cls).__new__(cls, *args, **kwargs)
        return cls._singlenton

    def __init__(self):
        self.connector = Connector()

    def get_helpdesk(self, request):
        tracker = trackersBookByKey['HELP'].keystone
        startAt = 0
        if request == 'recovery':
            payloadTest = { 'fields': IssuesFactory.fields,
                        'maxResults':1000, 'startAt':startAt,
                        'jql':"created >= 2015-03-04 AND created <= 2015-05-12 AND project = {}".format(tracker) }
            payloadMain = { 'fields': IssuesFactory.fields,
                        'maxResults':1000, 'startAt':startAt,
                        'jql':"project = {}".format(tracker) }
            try:
                # raise Exception
                data = self.connector.search('JIRATEST',payloadTest)
                testHelpDeskRecoveryList = IssuesList.fromData('helpdesktest.recovery', data['issues'])

                data = self.connector.search('JIRA', payloadMain)
                totalIssues, receivedIssues = data['total'], len(data['issues'])
                while totalIssues > receivedIssues:
                    payloadMain['startAt'] = receivedIssues
                    try:
                        data['issues'].extend(self.connector.search('JIRA', payloadMain)['issues'])
                    except Exception: raise Exception
                    receivedIssues = len(data['issues'])

                actualHelpDeskRecoveryList = IssuesList.fromData('helpdesk.recovery', data['issues'])
            except Exception:
                testHelpDeskRecoveryList = IssuesList.fromFile('helpdesktest.recovery')
                actualHelpDeskRecoveryList = IssuesList.fromFile('helpdesk.recovery')

        return actualHelpDeskRecoveryList, testHelpDeskRecoveryList

    def get_coachhelpdesk(self, request):
        tracker = 'HELC'
        startAt = 0
        if request == 'recovery':
            payloadTest = { 'fields': IssuesFactory.fields,
                        'maxResults':1000, 'startAt':startAt,
                        'jql':"created >= 2015-03-04 AND created <= 2015-05-12 AND project = {}".format(tracker) }
            payloadMain = { 'fields': IssuesFactory.fields,
                        'maxResults':1000, 'startAt':startAt,
                        'jql':"project = {}".format(tracker) }
            try:
                # raise Exception
                data = self.connector.search('JIRATEST',payloadTest)
                testHelpDeskRecoveryList = IssuesList.fromData('coachhelpdesktest.recovery', data['issues'])

                data = self.connector.search('JIRA', payloadMain)
                totalIssues, receivedIssues = data['total'], len(data['issues'])
                while totalIssues > receivedIssues:
                    payloadMain['startAt'] = receivedIssues
                    try:
                        data['issues'].extend(self.connector.search('JIRA', payloadMain)['issues'])
                    except Exception: raise Exception
                    receivedIssues = len(data['issues'])

                actualHelpDeskRecoveryList = IssuesList.fromData('coachhelpdesk.recovery', data['issues'])
            except Exception:
                testHelpDeskRecoveryList = IssuesList.fromFile('coachhelpdesktest.recovery')
                actualHelpDeskRecoveryList = IssuesList.fromFile('coachhelpdesk.recovery')

        return actualHelpDeskRecoveryList, testHelpDeskRecoveryList


class Report:

    channels = {'Lab':  'Fiware-lab-help',
                'Tech': 'Fiware-tech-help',
                'General': 'Fiware-general-help',
                'Feedback': 'Fiware-feedback',
                'Collaboration': 'Fiware-collaboration-request',
                'Speakers': 'Fiware-speakers-request',
                'Ops': 'Fiware-ops-help',
                'Coach': 'Fiware[\w-]+coaching',
                'Other': '.',
                'CEED Tech': 'Fiware-ceedtech-coaching',
                'CreatiFI': 'Fiware-creatifi-coaching',
                'EuropeanPioneers': 'Fiware-europeanpioneers-coaching',
                'FABulous': 'Fiware-fabulous-coaching',
                'FI-ADOPT': 'Fiware-fiadopt-coaching',
                'FI-C3': 'Fiware-fic3-coaching',
                'FICHe': 'fiware-fiche-coaching',
                'Finish': 'Fiware-finish-coaching',
                'FINODEX': 'Fiware-finodex-coaching',
                'FRACTALS': 'Fiware-fractals-coaching',
                'FrontierCities': 'Fiware-frontiercities-coaching',
                'IMPACT': 'Fiware-impact-coaching',
                'INCENSe': 'Fiware-incense-coaching',
                'SmartAgriFood2': 'Fiware-smartagrifood-coaching',
                'SOUL-FI': 'Fiware-soulfi-coaching',
                'SpeedUp Europe': 'Fiware-speedup-coaching'}

    class Issue:
        def __init__(self, item, where):
            self.lid = '{}-{}'.format(where, item.key)
            self.key = item.key
            self.created = item.created
            self.instance = where
            self.reference = re.sub(r'\s+',' ',item.reference)
            self.description = item.description
            self.assignee = item.assignee
            self.url = item.url
            self.reporter = item.reporter
            # print(self.reporter)
            self.status = item.status
            try:
                self.channel = [channel for channel in Report.channels
                                if re.search(r'\[{}\]'.format(Report.channels[channel]), item.reference)][0]
            except Exception: self.channel = 'Other'
            channelPattern = Report.channels[self.channel]
            try:
                self.type = 'NewIssue' if not re.search(r'T?R[VeE]?:\s+.*\[{}\]'.format(channelPattern), item.reference) else 'Comment'
            except Exception: self.type = 'NewIssue'
            # print(self.reference)
            topic = re.sub(r'T?R[VeE]?:|AW:|I:','', self.reference)
            topic = re.sub(r'F[Ww]d?:','', topic)
            topic = re.sub(r'\[FI-WARE-JIRA\]|\[FIWARE Lab\]','', topic)
            self.topic = re.sub(r'(\[Fiware.*?\])*', '', topic).strip()
            # print(self.topic)
            # self.topic = self.topic.strip()
            # print(self.topic, '\n' )
            self.sender = self.reporter
            if self.reporter == 'FW External User':
                try:
                    self.sender = self._getCreatedByInNew(item.description) \
                        if self.type == 'NewIssue' \
                        else self._getCreatedByinComment(item.description)
                except Exception:
                    pass
                    # print(item.reference, item.reporter)
                    # print(item)
            self.sons = []
            self.father = []
            self.p_sons = []
            self.p_fathers = []

        def __repr__(self):
            return '{}'.format(self.lid)

        def _getCreatedByInNew(self, data):
            # print(type(data))
            mfilter = re.compile(r'\[Created via e-mail received from:\s+(?P<sender>.*)\s+<(?P<email>.*@.*)>\]')

            if mfilter.search(data):
                sender = mfilter.search(data).group('sender')
                email = mfilter.search(data).group('email')
                output = [email]
            else:
                pass

            output = self._getCreatedByinComment(data)

        # print(output)

            return output

        def _getCreatedByinComment(self, data):
            mfilter = re.compile(r'[^ :<+="\t\r\n\]\[]+@[\w.-]+\.[a-zA-Z]+')
            output = re.findall(mfilter, data)
            if len(output):
                output = [item for item in output if not 'gif' in item ]
                output = [item for item in output if not 'fi-ware' in item]
                output = [item for item in output if not 'fiware' in item]
                output = [item for item in output if not 'github' in item]
                # output = [item for item in output if not 'carrillo' in item]
                output = list(set(output))
            else:
                raise Exception
            return output

    def __init__(self):
        self.factory = IssuesFactory()
        data = self.factory.get_helpdesk('recovery')
        # data = self.factory.get_coachhelpdesk('recovery')
        self.actualInstanceData = data[0]
        self.testInstanceData = data[1]
        self.data = [Report.Issue(item, 'MAIN') for item in data[0]]
        self.data += [Report.Issue(item, 'TEST') for item in data[1]]
        # for item in self.data:
        #     print (item)
        # print(len(self.data))

    def _report_channel(self, channel):
        data = [item for item in self.data if item.channel == channel]
        __data = {item.lid:item for item in data}
        ws = self.workbook.add_worksheet(channel)
        ws.set_zoom(80)
        ws.set_column(0, 0, 12)
        ws.set_column(1, 1, 5)
        ws.set_column(2, 3, 10)
        ws.set_column(4, 5, 200)
        ws.set_column(6, 10, 15)
        row, col = 0, 0

        ws.merge_range(xl_range(row, 0, row, 5), "HELP DESK Recovery Report", self.spFormats.chapter_title)
        ws.set_row(0, 40)
        ws.insert_image(0, 4, settings.logoAzul, {'x_scale': 0.75, 'y_scale': 0.75, 'x_offset': 400, 'y_offset': 5})
        row += 1
        ws.write(row, 0, 'Report Date:', self.spFormats.bold_right)
        ws.write(row, 1, date.today().strftime('%d-%m-%Y'))
        row += 1
        ws.write(row, 0, 'CHANNEL = ', self.spFormats.bold_right)
        # ws.write(row, 1, channel, self.spFormats.bold_red)
        ws.merge_range(xl_range(row, 1, row, 2), channel, self.spFormats.bold_red)
        row += 1
        ws.write(row, 0, 'MAIN =', self.spFormats.bold_right)
        ws.write(row, 1, '# {} issues'.format(len([item for item in data if item.instance == 'MAIN'])))
        row += 1
        ws.write(row, 0, 'TEST =', self.spFormats.red_bold_right)
        ws.write(row, 1, '# {} issues'.format(len([item for item in data if item.instance == 'TEST'])))
        row += 1
        # ws.write(row, 1, 'NEW = ', self.spFormats.red_bold_right)
        ws.merge_range(xl_range(row, 0, row, 1), 'NEW = ', self.spFormats.red_bold_right)
        ws.write(row, 2, '# {} issues'
                 .format(len([item for item in data if item.instance == 'TEST' and item.type == 'NewIssue'])))

        row += 1
        # ws.write(row, 1, 'COMMENTS =', self.spFormats.blue)
        ws.merge_range(xl_range(row, 0, row, 1), 'COMMENTS =', self.spFormats.right_bold_green)
        ws.write(row, 2, '# {} issues'
                 .format(len([item for item in data if item.instance == 'TEST' and item.type == 'Comment'])))

        row += 1
        issuesInTestInstance = [item for item in data if item.instance == 'TEST' and item.type == 'NewIssue']
        commentsInTestInstance = [item for item in data if item.instance == 'TEST' and item.type == 'Comment']
        print(channel, len(data), ' Issues =',len(issuesInTestInstance), ' Comments= ', len(commentsInTestInstance))

        comments = [item for item in data if item.type == 'Commnent']
        newIssues = [item for item in data if item.type == 'NewIssue']

        for item in issuesInTestInstance:
            item.sons = [_item for _item in comments if item.topic == _item.topic and any(email in _item.sender for email in item.sender )]
            if len(item.sons):
                for _item in item.sons: _item.father = [item,]
            else:
                item.p_sons = \
                    [_item for _item in comments if item.topic == _item.topic and item.created <= _item.created]

        for item in [item for item in commentsInTestInstance if not len(item.father)]:
            item.p_fathers = \
                [_item for _item in newIssues if _item.topic == item.topic and _item.created <= item.created]

            if len(item.p_fathers):
                item.father = \
                    [_item for _item in item.p_fathers if  any(email in _item.sender for email in item.sender)]

                for _item in item.father:
                    if _item.sons:
                        _item.sons.append(item)
                    else:
                        _item.sons = [item,]

        issuesToMigrate = []
        issuesToMigrate.extend([item for item in issuesInTestInstance if not len(item.sons)])
        issuesToMigrate.extend([item for item in commentsInTestInstance if not len(item.father)])
        for item in [item for item in commentsInTestInstance if len(item.father)]:
            # issuesToMigrate.append(item)
            for _item in item.father:
                if _item.instance == 'TEST':
                    issuesToMigrate.append(_item)

        row += 3
        ws.merge_range(xl_range(row, 0, row, 5),'ISSUES TO MIGRATE', self.spFormats.bigSection)
        row += 1
        ws.write_row(row, 0, ('Created', 'Where', 'Key', 'Status', 'Summary'), self.spFormats.column_heading)
        row += 1
        k = 0
        for k, item in enumerate(sorted(issuesToMigrate, key=attrgetter('created')), start=1):
            row += 1
            self._write_out(ws, row, item)
        row += 1
        ws.write(row, 0, '#items = {}'.format(k), self.spFormats.red)

        row += 3
        ws.merge_range(xl_range(row, 0, row, 5), 'FINDINGS', self.spFormats.bigSection)
        row += 1
        ws.write_row(row, 0, ('Created', 'Where', 'Key', 'Status', 'Summary'), self.spFormats.column_heading)
        k = 0
        for k, item in enumerate(sorted([item for item in issuesInTestInstance], key=attrgetter('created')), start=1):
            row += 1
            self._write_out(ws, row, item)
            for _item in item.sons:
                if _item.instance == 'TEST': continue
                row += 1
                self._write_out(ws, row, _item)
        row += 1
        ws.write(row, 0, '#items = {}'.format(k), self.spFormats.red)
        row += 2

        ws.write_row(row, 0, ('Created', 'Where', 'Key', 'Status', 'Summary'), self.spFormats.column_heading)
        k = 0
        for k, item in enumerate(sorted([item for item in commentsInTestInstance if len(item.father)], key=attrgetter('created')), start=1):
            row += 1
            self._write_out(ws, row, item)
            for _item in item.father:
                row += 1
                self._write_out(ws, row, _item)
            if not len(item.father):
                for _item in item.p_fathers:
                    row += 1
                    self._write_out(ws, row, _item, False)
            row += 1
        row += 1
        ws.write(row, 0, '#items = {}'.format(k), self.spFormats.red)
        row += 2

        ws.write_row(row, 0, ('Created', 'Where', 'Key', 'Status', 'Summary'), self.spFormats.column_heading)
        row += 1
        k = 0
        for k, item in enumerate(sorted([item for item in commentsInTestInstance if not len(item.father)], key=attrgetter('created')), start=1):
            row += 1
            self._write_out(ws, row, item)
            # for _item in item.p_fathers:
            #    row += 1
            #    self._write_out(ws, row, _item, False)
        row += 1
        ws.write(row, 0, '#items = {}'.format(k), self.spFormats.red)


        return
        seed = 'Henning Sprang'
        for item in data:
            match = re.search(seed, item.description)
            if match:
                print(item.lid, item.key)

    def _write_out(self, ws, row, item, p=True):
        get_link = lambda a: 'http://130.206.80.89/browse/{}'.format(a)
        black = self.workbook.add_format({'font_color': 'black'}) \
            if p else self.workbook.add_format({'font_color': 'black', 'bg_color': 'yellow'})

        ws.write(row, 0, item.created.strftime("%d-%m-%Y"), black)

        if item.instance == 'TEST':
            ws.write(row, 1, item.instance, self.spFormats.red)
            ws.write_url(row, 2, get_link(item.key), self.spFormats.link, item.key)
            if item.type == 'Comment':
                ws.write(row, 3, 'Comment', self.spFormats.green)
            elif item.type == 'NewIssue':
                ws.write(row, 3, 'New', self.spFormats.red)
            else: pass
        else:
            ws.write(row, 1, item.instance)
            ws.write_url(row, 2, item.url, self.spFormats.link, item.key)
            ws.write(row, 3, item.status)
        ws.write(row, 4, '{}\nCreated on {} by {}\nFather = {}, Sons = {}'
                 .format(item.reference, item.created, item.sender, item.father, item.sons))

    def _verify_channel(self, channel):
        data = [item for item in self.data if item.channel == channel]
        __data = {item.lid: item for item in data}
        ws = self.workbook.add_worksheet(channel)
        ws.set_zoom(80)
        ws.set_column(0, 0, 3)
        ws.set_column(1, 1, 10)
        ws.set_column(2, 4, 10)
        ws.set_column(5, 5, 200)
        ws.set_column(6, 10, 15)
        row, col = 0, 0

        ws.merge_range(xl_range(row, 0, row, 5), "HELP DESK Recovery Report", self.spFormats.chapter_title)
        ws.set_row(0, 40)
        ws.insert_image(0, 4, settings.logoAzul, {'x_scale': 0.75, 'y_scale': 0.75, 'x_offset': 400, 'y_offset': 5})
        row += 1
        ws.write(row, 0, 'Report Date:', self.spFormats.bold_right)
        ws.write(row, 1, date.today().strftime('%d-%m-%Y'))
        row += 1
        ws.write(row, 0, 'CHANNEL = ', self.spFormats.bold_right)
        # ws.write(row, 1, channel, self.spFormats.bold_red)
        ws.merge_range(xl_range(row, 1, row, 2), channel, self.spFormats.bold_red)
        row += 1
        ws.write(row, 0, 'MAIN =', self.spFormats.bold_right)
        ws.write(row, 1, '# {} issues'.format(len([item for item in data if item.instance == 'MAIN'])))
        row += 1
        ws.write(row, 0, 'TEST =', self.spFormats.red_bold_right)
        ws.write(row, 1, '# {} issues'.format(len([item for item in data if item.instance == 'TEST'])))
        row += 1
        # ws.write(row, 1, 'NEW = ', self.spFormats.red_bold_right)
        ws.merge_range(xl_range(row, 0, row, 1), 'NEW = ', self.spFormats.red_bold_right)
        ws.write(row, 2, '# {} issues'
                 .format(len([item for item in data if item.instance == 'TEST' and item.type == 'NewIssue'])))

        row += 1
        # ws.write(row, 1, 'COMMENTS =', self.spFormats.blue)
        ws.merge_range(xl_range(row, 0, row, 1), 'COMMENTS =', self.spFormats.right_bold_green)
        ws.write(row, 2, '# {} issues'
                 .format(len([item for item in data if item.instance == 'TEST' and item.type == 'Comment'])))

        row += 1
        issuesInTestInstance = [item for item in data if item.instance == 'TEST' and item.type == 'NewIssue']
        commentsInTestInstance = [item for item in data if item.instance == 'TEST' and item.type == 'Comment']
        print(channel, len(data), ' Issues =', len(issuesInTestInstance), ' Comments= ', len(commentsInTestInstance))

        comments = [item for item in data if item.type == 'Commnent']
        newIssues = [item for item in data if item.type == 'NewIssue']


        _selection = [item for item in data if item.assignee == 'Pietropaolo Alfonso']
        _topics = [item.topic for item in _selection]
        mydata = [_item for item in _selection for _item in data if _item.topic in _topics and any([email in _item.sender for email in item.sender]) ]

        mydata = list(set(mydata))
        _itemsList = sorted(mydata, key=attrgetter('created'))
        _itemsList.sort(key=attrgetter('topic'))

        row += 3
        ws.merge_range(xl_range(row, 0, row, 5),'ISSUES by TOPIC', self.spFormats.bigSection)
        row += 1
        ws.write_row(row, 0, ('#','Created', 'Instance', 'Key', 'Status', 'Summary'), self.spFormats.column_heading)
        row += 1
        k = 0
        for k,item in enumerate(_itemsList, start=1):
            row += 1
            self._write_out2(k, ws, row, item)
        row += 1
        ws.write(row, 0, '#items = {}'.format(k), self.spFormats.red)

        return

    def _write_out2(self, k, ws, row, item):
        get_link = lambda a: 'http://130.206.80.89/browse/{}'.format(a)
        ws.write(row, 0, k)
        ws.write(row, 1, item.created.strftime("%d-%m-%Y"))
        if item.instance == 'TEST':
            ws.write(row, 2, item.instance, self.spFormats.red)
            ws.write_url(row, 3, get_link(item.key), self.spFormats.link, item.key)
            if item.type == 'Comment':
                ws.write(row, 4, 'Comment', self.spFormats.green)
            elif item.type == 'NewIssue':
                ws.write(row, 4, 'New', self.spFormats.red)
            else:
                pass
        else:
            ws.write(row, 2, item.instance)
            ws.write_url(row, 3, item.url, self.spFormats.link, item.key)
            ws.write(row, 4, item.status)

        ws.write(row, 5, 'Topic: {}\nReference: {}\nSender: {}\nReporter: {}\nAssignee:{}'
                 .format(item.topic, item.reference, item.sender,item.reporter, item.assignee))
        # ws.write(row, 4, 'Sender: {}\nReporter: {}\nAssignee:{}'.format(item.sender,item.reporter, item.assignee))

    def _helpdesk_report(self):
        channels = ('Lab', 'Tech', 'General', 'Feedback', 'Collaboration', 'Speakers', 'Ops')
        # channels = ('All', 'Lab', 'Tech')
        for channel in channels:
            #self._report_channel(channel)
            self._verify_channel(channel)
        # self._report_channel('All')

    def _coachhelpdesk_report(self):
        channels = ('CEED Tech', 'CreatiFI', 'EuropeanPioneers', 'FABulous', 'FI-ADOPT', 'FI-C3', 'FICHe', 'Finish',
                    'FINODEX', 'FRACTALS', 'FrontierCities', 'IMPACT', 'INCENSe', 'SmartAgriFood2', 'SOUL-FI',
                    'SpeedUp Europe')

        for channel in channels:
            # self._report_channel(channel)
            self._verify_channel(channel)

    def __call__(self, *args, **kwargs):
        print("Help Desk Recovery Report")
        _date = datetime.now().strftime("%Y%m%d-%H%M")
        filename = 'FIWARE.helpdesk.recovery.'+ _date + '.xlsx'
        # filename = 'FIWARE.coachhelpdesk.recovery.'+ _date + '.xlsx'
        myfile = os.path.join(settings.outHome, filename)
        self.workbook = xlsxwriter.Workbook(myfile)
        self.spFormats = SpreadsheetFormats(self.workbook)
        self._helpdesk_report()
        # self._coachhelpdesk_report()
        print(': W:' + myfile)
        self.workbook.close()


if __name__ == "__main__":
    report = Report()
    report()
