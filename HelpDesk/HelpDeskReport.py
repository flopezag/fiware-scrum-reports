__author__ = "Manuel Escriche <mev@tid.es>"
import os, base64, requests, xlsxwriter, re
from datetime import date, datetime
from xlsxwriter.utility import xl_range
from operator import attrgetter
from collections import namedtuple
from kernel.Settings import settings
from kernel.SheetFormats import SpreadsheetFormats
from kernel.TrackerBook import trackersBookByKey
from kernel.IssuesList import IssuesList

class Connector:

    url_api = {
        'session':'/rest/auth/1/session',
        'project':'/rest/api/latest/project',
        'component':'/rest/api/latest/component/',
        'search':'/rest/api/latest/search'
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
        #print(self.root_url)
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
        #print('search')
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
        if request == 'report':
            payloadMain = {'fields': IssuesFactory.fields,
                           'maxResults': 1000, 'startAt': startAt,
                           'jql': "project = {}".format(tracker)}
            try:
                # raise Exception
                data = self.connector.search('JIRA', payloadMain)
                totalIssues, receivedIssues = data['total'], len(data['issues'])
                while totalIssues > receivedIssues:
                    payloadMain['startAt'] = receivedIssues
                    try:
                        data['issues'].extend(self.connector.search('JIRA', payloadMain)['issues'])
                    except Exception: raise Exception
                    receivedIssues = len(data['issues'])
            #print('total=', totalIssues, ' received=', receivedIssues)
                actualHelpDeskRecoveryList = IssuesList.fromData('helpdesk.report', data['issues'])
            except Exception:
                actualHelpDeskRecoveryList = IssuesList.fromFile('helpdesk.report')

        return actualHelpDeskRecoveryList

    def get_coachhelpdesk(self, request):
        tracker = 'HELC'
        startAt = 0
        if request == 'report':
            payloadMain = { 'fields': IssuesFactory.fields,
                        'maxResults':1000, 'startAt':startAt,
                        'jql':"project = {}".format(tracker) }
            try:
                data = self.connector.search('JIRA', payloadMain)
                totalIssues, receivedIssues = data['total'], len(data['issues'])
                while totalIssues > receivedIssues:
                    payloadMain['startAt'] = receivedIssues
                    try:
                        data['issues'].extend(self.connector.search('JIRA', payloadMain)['issues'])
                    except Exception: raise Exception
                    receivedIssues = len(data['issues'])
            #print('total=', totalIssues, ' received=', receivedIssues)
                actualHelpDeskRecoveryList = IssuesList.fromData('coachhelpdesk.report', data['issues'])
            except Exception:
                actualHelpDeskRecoveryList = IssuesList.fromFile('coachhelpdesk.report')

        return actualHelpDeskRecoveryList

class Report:

    channels = {'Lab':  'Fiware-lab-help',
                'Tech': 'Fiware-tech-help',
                'General': 'Fiware-general-help',
                'Feedback': 'Fiware-feedback',
                'Collaboration':'Fiware-collaboration-request',
                'Speakers':'Fiware-speakers-request',
                'Ops':'Fiware-ops-help',
                'Coach': 'Fiware[\w-]+coaching',
                'Other': '.',
                'CEED Tech': 'Fiware-ceedtech-coaching',
                'CreatiFI': 'Fiware-creatifi-coaching',
                'EuropeanPioneers':'Fiware-europeanpioneers-coaching',
                'FABulous':'Fiware-fabulous-coaching',
                'FI-ADOPT':'Fiware-fiadopt-coaching',
                'FI-C3':'Fiware-fic3-coaching',
                'FICHe':'fiware-fiche-coaching',
                'Finish':'Fiware-finish-coaching',
                'FINODEX':'Fiware-finodex-coaching',
                'FRACTALS':'Fiware-fractals-coaching',
                'FrontierCities':'Fiware-frontiercities-coaching',
                'IMPACT':'Fiware-impact-coaching',
                'INCENSe':'Fiware-incense-coaching',
                'SmartAgriFood2':'Fiware-smartagrifood-coaching',
                'SOUL-FI':'Fiware-soulfi-coaching',
                'SpeedUp Europe':'Fiware-speedup-coaching'}
    class Issue:
        def __init__(self, item):
            self.key = item.key
            self.created = item.created
            self.assignee = item.assignee
            self.reference = re.sub(r'\s+',' ',item.reference)
            self.description = item.description
            self.url = item.url
            self.reporter = item.reporter
            #print(self.reporter)
            self.status = item.status
            try:
                self.channel = [channel for channel in Report.channels
                                if re.search(r'\[{}\]'.format(Report.channels[channel]), item.reference)][0]
            except Exception: self.channel = 'Other'
            channelPattern = Report.channels[self.channel]
            try:
                self.type = 'NewIssue' if not re.search(r'T?R[VeE]?:\s+.*\[{}\]'.format(channelPattern), item.reference) else 'Comment'
            except Exception: self.type = 'NewIssue'
            #print(self.reference)
            topic = re.sub(r'T?R[VeE]?:|AW:|I:','', self.reference)
            topic = re.sub(r'F[Ww]d?:','', topic)
            topic = re.sub(r'\[FI-WARE-JIRA\]|\[FIWARE Lab\]','', topic)
            self.topic = re.sub(r'(\[Fiware.*?\])*', '', topic).strip()
            #print(self.topic)
            #self.topic = self.topic.strip()
            #print(self.topic, '\n' )
            self.sender = self.reporter
            if self.reporter == 'FW External User':
                try:
                    self.sender = self._getCreatedByInNew(item.description) \
                        if self.type == 'NewIssue' \
                        else self._getCreatedByinComment(item.description)
                except Exception:
                    pass
                    #print(item.reference, item.reporter)
                    #print(item)
        def __repr__(self):
            return '{}'.format(self.key)
        def _getCreatedByInNew(self, data):
            #print(type(data))
            mfilter = re.compile(r'\[Created via e-mail received from:\s+(?P<sender>.*)\s+<(?P<email>.*@.*)>\]')
            if mfilter.search(data):
                sender = mfilter.search(data).group('sender')
                email = mfilter.search(data).group('email')
                output = [email]
            else:
                output =  self._getCreatedByinComment(data)
        #print(output)
            return output
        def _getCreatedByinComment(self, data):
            mfilter = re.compile(r'[^ :<+="\t\r\n\]\[]+@[\w.-]+\.[a-zA-Z]+')
            output = re.findall(mfilter, data)
            if len(output):
                output = [item for item in output if not 'gif' in item ]
                output = [item for item in output if not 'fi-ware' in item]
                output = [item for item in output if not 'fiware' in item]
                output = [item for item in output if not 'github' in item]
                #output = [item for item in output if not 'carrillo' in item]
                output = list(set(output))
            else:
                raise Exception
            return output

    def __init__(self):
        self.factory = IssuesFactory()
        data = self.factory.get_helpdesk('report')
        #data = self.factory.get_coachhelpdesk('recovery')
        self.actualInstanceData = data
        self.data = [Report.Issue(item) for item in data]
        #for item in self.data:
        #    print (item)
        #print(len(self.data))


    def _report_channel(self, channel):
        data = [item for item in self.data if item.channel == channel]
        __data = {item.key:item for item in data}
        ws = self.workbook.add_worksheet(channel)
        ws.set_zoom(80)
        ws.set_column(0, 0, 5)
        ws.set_column(1, 1, 12)
        ws.set_column(2, 3, 10)
        ws.set_column(4, 5, 200)
        ws.set_column(6, 10, 15)
        row, col = 0, 0

        ws.merge_range(xl_range(row, 0, row, 5), "HELP DESK Report", self.spFormats.chapter_title)
        ws.set_row(0, 40)
        ws.insert_image(0, 4, settings.logoAzul, {'x_scale': 0.75, 'y_scale': 0.75, 'x_offset': 400, 'y_offset': 5})
        row += 1
        ws.write(row, 0, 'Report Date:', self.spFormats.bold_right)
        ws.write(row, 1, date.today().strftime('%d-%m-%Y'))
        row += 1
        ws.write(row, 0, 'CHANNEL = ', self.spFormats.bold_right)
        #ws.write(row, 1, channel, self.spFormats.bold_red)
        ws.merge_range(xl_range(row, 1, row, 2), channel, self.spFormats.bold_red)
        row += 1
        ws.write(row, 0, 'MAIN =', self.spFormats.bold_right)
        ws.write(row, 1, '# {} issues'.format(len(data)))
        row += 1
        #ws.write(row, 1, 'NEW = ', self.spFormats.red_bold_right)
        ws.merge_range(xl_range(row, 0, row, 1), 'NEW = ', self.spFormats.red_bold_right)
        ws.write(row, 2, '# {} issues'.format(len([item for item in data if item.type == 'NewIssue'])))
        row += 1
        #ws.write(row, 1, 'COMMENTS =', self.spFormats.blue)
        ws.merge_range(xl_range(row, 0, row, 1), 'COMMENTS =', self.spFormats.right_bold_green)
        ws.write(row, 2, '# {} issues'.format(len([item for item in data if item.type == 'Comment'])))
        row += 1

        _selection = [item for item in data if item.assignee == 'Pietropaolo Alfonso']
        _topics = [item.topic for item in _selection]
        mydata = [item for item in data if item.topic in _topics]
        _itemsList = sorted(mydata, key=attrgetter('created'))
        _itemsList.sort(key=attrgetter('topic'))

        row += 3
        ws.merge_range(xl_range(row, 0, row, 5),'ISSUES by TOPIC', self.spFormats.bigSection)
        row += 1
        ws.write_row(row, 0, ('#','Created', 'Key', 'Status', 'Summary'), self.spFormats.column_heading)
        row += 1
        k = 0
        for k,item in enumerate(_itemsList, start=1):
            row += 1
            self._write_out(k, ws, row, item)
        row += 1
        ws.write(row, 0, '#items = {}'.format(k), self.spFormats.red)


        return

    def _write_out(self, k, ws, row, item):
        ws.write(row, 0, k)
        ws.write(row, 1, item.created.strftime("%d-%m-%Y"))
        ws.write_url(row, 2, item.url, self.spFormats.link, item.key)
        ws.write(row, 3, item.status)
        ws.write(row, 4, 'Topic: {}\nReference: {}\nSender: {}\nReporter: {}\nAssignee:{}'.format(item.topic, item.reference, item.sender,item.reporter, item.assignee))
        #ws.write(row, 4, 'Sender: {}\nReporter: {}\nAssignee:{}'.format(item.sender,item.reporter, item.assignee))

    def _helpdesk_report(self):
        channels = ('Lab', 'Tech', 'General', 'Feedback', 'Collaboration', 'Speakers', 'Ops')
        #channels = ('All', 'Lab', 'Tech')
        for channel in channels:
            self._report_channel(channel)
        #self._report_channel('All')
    def _coachhelpdesk_report(self):
        channels = ('CEED Tech', 'CreatiFI', 'EuropeanPioneers', 'FABulous', 'FI-ADOPT', 'FI-C3', 'FICHe', 'Finish',
                    'FINODEX', 'FRACTALS', 'FrontierCities','IMPACT', 'INCENSe', 'SmartAgriFood2', 'SOUL-FI', 'SpeedUp Europe')
        for channel in channels:
            self._report_channel(channel)

    def __call__(self, *args, **kwargs):
        print("Help Desk Report")
        _date = datetime.now().strftime("%Y%m%d-%H%M")
        filename = 'FIWARE.helpdesk.report.'+ _date + '.xlsx'
        #filename = 'FIWARE.coachhelpdesk.recovery.'+ _date + '.xlsx'
        myfile = os.path.join(settings.outHome, filename)
        self.workbook = xlsxwriter.Workbook(myfile)
        self.spFormats = SpreadsheetFormats(self.workbook)
        self._helpdesk_report()
        #self._coachhelpdesk_report()
        print(': W:' + myfile)
        self.workbook.close()


if __name__ == "__main__":
    report = Report()
    report()