import os
import pickle
import re
import pprint
from datetime import date, datetime
from collections import namedtuple
from operator import attrgetter
from kernel.Settings import settings
from kernel.ComponentsBook import tComponentsBook, helpdeskCompBook
from kernel.TrackerBook import trackersBook
from kernel.NodesBook import tHelpDeskNodesBook
from kernel.Connector import Connector
from kernel.Jira import JIRA

__author__ = "Manuel Escriche <mev@tid.es>"


class LinkedIssue(dict):
    def __init__(self, item):
        super().__init__()
        _type = [key for key in ('inwardIssue', 'outwardIssue') if key in item][0]
        self['type'] = _type
        self['status'] = item[_type]['fields']['status']['name']
        self['key'] = item[_type]['key']
        self['url'] = 'https://jira.fiware.org/browse/{}'.format(self['key'])

    @property
    def type(self): return self['type']

    @property
    def status(self): return self['status']

    @property
    def key(self): return self['key']

    @property
    def url(self): return self['url']

    def __str__(self):
        return self['key']

    def __repr__(self):
        return self['key']


class SimpleIssue(dict):
    def __init__(self, issue):
        super().__init__()
        # pprint.pprint(issue)
        self['key'] = issue['key']
        self['id'] = issue['id']
        self['project'] = issue['fields']['project']['key']
        self['component'] = [item['id'] for item in issue['fields']['components']]
        self['summary'] = issue['fields']['summary'].strip()
        self['status'] = issue['fields']['status']['name']
        self['description'] = issue['fields']['description']

        try:
            self['priority'] = issue['fields']['priority']['name']
        except:
            self['priority'] = 'Major'

        self['issueType'] = issue['fields']['issuetype']['name']
        self['reporter'] = issue['fields']['reporter']['displayName']

        if issue['fields']['resolution'] != None:
            self['resolution'] = issue['fields']['resolution']['name'] \
            if 'name' in issue['fields']['resolution'] else None
        else:
            self['resolution'] = None

        if issue['fields']['assignee'] != None:
            self['assignee'] = issue['fields']['assignee']['displayName'] \
                if 'displayName' in issue['fields']['assignee'] else None
        else:
            self['assignee'] = None

        if 'duedate' in issue['fields']:
            self['duedate'] = datetime.strptime(issue['fields']['duedate'][:10], '%Y-%m-%d').date() \
                if issue['fields']['duedate'] else None
        else:
            self['duedate'] = None

        self['created'] = datetime.strptime(issue['fields']['created'][:10], '%Y-%m-%d').date()
        self['updated'] = datetime.strptime(issue['fields']['updated'][:10], '%Y-%m-%d').date()

        if 'resolutiondate' in issue['fields']:
            self['resolved'] = datetime.strptime(issue['fields']['resolutiondate'][:10], '%Y-%m-%d').date()  \
                if issue['fields']['resolutiondate'] else None
        else:
            self['resolved'] = None

        self['version'] = 'Unscheduled'
        self['nVersions'] = 0
        if 'fixVersions' in issue['fields']:
            self['nVersions'] = len(issue['fields']['fixVersions'])
            if len(issue['fields']['fixVersions']) > 0:
                self['version'] = issue['fields']['fixVersions'][0]['name']
                self['releaseDate'] = \
                    datetime.strptime(issue['fields']['fixVersions'][0]['releaseDate'][:10], '%Y-%m-%d').date()

        self['jurl'] = "http://jira.fiware.org/browse/{}".format(issue['key'])
        # print(self['jurl'])

        # self['cmpName'] = helpdeskBook.get_compName(self['component'])
        if not len(self['component']):
            self['cmpName'] = 'Unassigned'
        else:
            try:
                self['cmpName'] = tComponentsBook[self['component'][0]].name
            except:
                self['cmpName'] = 'Unknown'
        # print(self['component'], self['cmpName'])

        _version = self['version'].split()

        if len(_version) == 1:
            version = 'Unscheduled'
        else:
            version = _version[1]

        self['links'] = None
        if 'issuelinks' in issue['fields']:
            if len(issue['fields']['issuelinks']) > 0:
                self['links'] = [LinkedIssue(item) for item in issue['fields']['issuelinks']]

    def name_test(self):
        chunks = self['summary'].split('.')
        if len(chunks) < 3: return False
        project = chunks[0]
        issueType = chunks[1]
        return True if project == 'FIWARE' and issueType == self['issueType'] else False

    @property
    def links(self):
        return self['links']

    @property
    def key(self):
        return self['key']

    @property
    def nkey(self):
        return int(self['key'].split('-')[1])

    @property
    def name(self):
        return self.shortReference if self.name_test() else self.reference

    @property
    def shortReference(self):
        _name = self['summary'].split('.')
        return '.'.join(_name[2:])

    @property
    def reference(self):
        return self['summary']

    @property
    def description(self):
        return self['description']

    @property
    def reporter(self):
        return self['reporter']

    @property
    def issueType(self):
        return self['issueType']

    @property
    def priority(self):
        return self['priority']

    @property
    def status(self):
        return self['status']

    @property
    def resolution(self):
        return self['resolution']

    @property
    def resolved(self):
        return self['resolved']

    @property
    def updated(self):
        return self['updated']

    @property
    def created(self):
        return self['created']

    @property
    def nVersions(self):
        return self['nVersions']

    @property
    def timeSlot(self):
        return self['version']

    @property
    def nTimeSlot(self):
        return self['version'].split()[1]

    @property
    def assignee(self):
        return self['assignee'] if self['assignee'] else 'None'

    @property
    def age_(self):
        if self['resolved']:
            return self['resolved'] - self['created']
        else: return date.today() - self['created']

    @property
    def age(self):
        if self['resolved']:
            return (self['resolved'] - self['created']).days
        else:
            return (date.today() - self['created']).days

    @property
    def duedate(self):
        return self['duedate']

    @property
    def delay(self):
        if self['resolved'] and self['duedate']:
            return (self['resolved'] - self['duedate']).days
        return (date.today() - self.duedate).days

    @property
    def upcoming(self):
        return (self.duedate - date.today()).days

    @property
    def project(self):
        return self['project']

    @property
    def components(self):
        return self['component']

    @property
    def cmpName(self):
        return self['cmpName']

    @property
    def node(self):
        return tHelpDeskNodesBook.getNode(self.assignee)

    @property
    def url(self):
        return self['jurl']


class IssuesList(list):
    _sortDict = {'keyn': lambda x: x.nkey,
                 'key': lambda x: x.key,
                 'issueType': lambda x: x.issueType,
                 'name': lambda x: x.name,
                 'status': lambda x: x.status,
                 'priority': lambda x: x.priority,
                 'timeSlot': lambda x: x.timeSlot,
                 'assignee': lambda x: x.assignee,
                 'duedate': lambda x: x.duedate,
                 'age': lambda x: x.age,
                 'delay': lambda x: x.delay,
                 'upcoming': lambda x: x.upcoming,
                 'cmpName': lambda x: x.cmpName,
                 'node': lambda x: x.node}

    def __init__(self, name, issuesList):
        super().__init__()
        self.listName = name
        self.timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        self.filename = 'FIWARE.issuesList.' + self.listName + '.' + self.timestamp + '.pkl'
        # print('+', self.filename)
        if issuesList:
            for issue in issuesList:
                self.append(issue)
        # set up reviewers
        self.save()
        self.clean()

    @property
    def unresolved(self):
        return [issue for issue in self if not issue.resolved]

    @property
    def recent(self):
        issues = [issue for issue in [issue for issue in self if issue.resolved]
                  if (date.today() - issue.resolved).days <= 60 ]
        return sorted(issues, key=attrgetter('resolved'), reverse=True)

    @classmethod
    def fromData(cls, name, data):
        issuesList = [SimpleIssue(issue) for issue in data]
        # print(name)
        return cls(name, issuesList)

    @property
    def sortDict(self):
        return IssuesList._sortDict

    def save(self):
        longFilename = os.path.join(settings.storeHome, self.filename)
        with open(longFilename, 'wb') as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)

    @classmethod
    def fromFile(cls, name):
        fileList = os.listdir(settings.storeHome)

        mfilter = \
            re.compile(r'\bFIWARE[.]issuesList[.](?P<name>[\w\.\-\d]+)[.](?P<day>\d{8})[-](?P<time>\d{4})[.]pkl\b')

        record = namedtuple('record', 'filename, day, time')
        filelist = [record(mfilter.match(f).group(0),
                           mfilter.match(f).group('day'),
                           mfilter.match(f).group('time')) for f in fileList if mfilter.match(f)
                    if mfilter.match(f).group('name') == name]
        filelist.sort(key=attrgetter('day', 'time'), reverse=True)
        filename = filelist[0].filename
        # print('load-fromFile', filename)
        with open(os.path.join(settings.storeHome, filename), 'rb') as f:
            return pickle.load(f)

    def clean(self):
        fileList = os.listdir(settings.storeHome)

        mfilter = \
            re.compile(r'\bFIWARE[.]issuesList[.](?P<name>[\w\.\-\d]+)[.](?P<day>\d{8})[-](?P<time>\d{4})[.]pkl\b')

        record = namedtuple('record', 'filename, day, time')
        filelist = [record(mfilter.match(f).group(0),
                           mfilter.match(f).group('day'),
                           mfilter.match(f).group('time')) for f in fileList if mfilter.match(f)
                    if mfilter.match(f).group('name') == self.listName]

        filelist.sort(key=attrgetter('day', 'time'), reverse=True)
        toRemove = filelist[5:]
        if len(toRemove) > 0:
            for item in toRemove:
                os.remove(os.path.join(settings.storeHome, item.filename))


class IssuesFactory:
    _fields = '*navigable'
    fields = 'summary,status,project,components,priority,issuetype,description,reporter,' \
             'resolution,assignee,created,updated,duedate,resolutiondate,fixVersions,releaseDate,issuelinks'

    instance = None

    jql = {'lab.accounts'           : 'project=FLUA',
           'lab.accounts.unresolved': 'project=FLUA AND resolution = Unresolved'}

    @classmethod
    def getInstance(cls):
        if cls.instance is None:
             cls.instance = IssuesFactory()
        return cls.instance

    def __init__(self):
        self.connector = Connector.getInstance()

    def getAllHelpDeskIssues(self, request):
        startAt = 0
        if request == 'main':
            payload = {'fields': IssuesFactory.fields,
                       'maxResults': 1000, 'startAt': startAt,
                       'jql': 'project=HELP'}
            try:
                data = self.connector.search(payload)
            except:
                raise Exception

            totalIssues, receivedIssues = data['total'], len(data['issues'])

            while totalIssues > receivedIssues:
                payload['startAt'] = receivedIssues
                try:
                    _data = self.connector.search(payload)
                except:
                    raise Exception

                data['issues'].extend(_data['issues'])
                receivedIssues = len(data['issues'])

            return IssuesList.fromData('helpdesk.main', data['issues'])

        if request == 'main.lab':
            labId = helpdeskCompBook['Lab'].key
            payload = {'fields': IssuesFactory.fields,
                       'maxResults': 1000, 'startAt': startAt,
                       'jql': 'component={}'.format(labId)}
            try:
                data = self.connector.search(payload)
            except: raise Exception

            totalIssues, receivedIssues = data['total'], len(data['issues'])

            while totalIssues > receivedIssues:
                payload['startAt'] = receivedIssues
                data['issues'].extend(self.connector.search(payload)['issues'])
                receivedIssues = len(data['issues'])
            return IssuesList.fromData('helpdesk.main.lab', data['issues'])

        if request == 'main.tech':
            labId = helpdeskCompBook['Tech'].key
            payload = {'fields': IssuesFactory.fields,
                       'maxResults': 1000, 'startAt': startAt,
                       'jql': 'component={}'.format(labId)}
            try:
                data = self.connector.search(payload)
            except:
                raise Exception

            totalIssues, receivedIssues = data['total'], len(data['issues'])

            while totalIssues > receivedIssues:
                payload['startAt'] = receivedIssues
                data['issues'].extend(self.connector.search(payload)['issues'])
                receivedIssues = len(data['issues'])

            return IssuesList.fromData('helpdesk.main.tech', data['issues'])

        if request == 'coaches':
            payload = {'fields': IssuesFactory.fields,
                       'maxResults': 1000, 'startAt': startAt,
                       'jql': 'project=HELC'}
            try:
                data = self.connector.search(payload)
            except:
                raise Exception

            totalIssues, receivedIssues = data['total'], len(data['issues'])

            while totalIssues > receivedIssues:
                payload['startAt'] = receivedIssues
                data['issues'].extend(self.connector.search(payload)['issues'])
                receivedIssues = len(data['issues'])

            return IssuesList.fromData('helpdesk.coaches', data['issues'])

        if request == 'tools':
            payload = {'fields': IssuesFactory.fields,
                       'maxResults': 1000, 'startAt': startAt,
                       'jql': 'project=SUPP'}
            try:
                data = self.connector.search(payload)
            except:
                raise Exception

            totalIssues, receivedIssues = data['total'], len(data['issues'])

            while totalIssues > receivedIssues:
                payload['startAt'] = receivedIssues
                data['issues'].extend(self.connector.search(payload)['issues'])
                receivedIssues = len(data['issues'])

            return IssuesList.fromData('helpdesk.tools', data['issues'])

    def getUnresolvedHelpDeskIssues(self, request):
        startAt = 0
        if request == 'main':
            payload = {'fields': IssuesFactory.fields,
                       'maxResults': 1000, 'startAt': startAt,
                       'jql': 'project=HELP AND resolution = Unresolved'}
            try:
                data = self.connector.search(payload)
            except:
                raise Exception

            unresolvedIssues = IssuesList.fromData('helpdesk.main.unresolved', data['issues'])

            return unresolvedIssues

        if request == 'main.lab':
            labId = helpdeskCompBook['Lab'].key
            payload = {'fields': IssuesFactory.fields,
                       'maxResults': 1000, 'startAt': startAt,
                       'jql': 'component={} AND resolution = Unresolved'.format(labId)}
            try:
                data = self.connector.search(payload)
            except:
                raise Exception

            unresolvedIssues = IssuesList.fromData('helpdesk.main.lab.unresolved', data['issues'])

            return unresolvedIssues

        if request == 'main.tech':
            techId = helpdeskCompBook['Tech'].key
            payload = {'fields': IssuesFactory.fields,
                       'maxResults': 1000, 'startAt': startAt,
                       'jql': 'component={} AND resolution = Unresolved'.format(techId)}
            try:
                data = self.connector.search(payload)
            except:
                raise Exception

            unresolvedIssues = IssuesList.fromData('helpdesk.main.tech.unresolved', data['issues'])

            return unresolvedIssues

        if request == 'coaches':
            payload = {'fields': IssuesFactory.fields,
                       'maxResults': 1000, 'startAt': startAt,
                       'jql': 'project=HELC AND resolution = Unresolved' }
            try:
                data = self.connector.search(payload)
            except:
                raise Exception

            unresolvedIssues = IssuesList.fromData('helpdesk.coaches.unresolved', data['issues'])

            return unresolvedIssues

        if request == 'tools':
            payload = {'fields': IssuesFactory.fields,
                       'maxResults': 1000, 'startAt': startAt,
                       'jql': 'project=SUPP AND resolution = Unresolved'}
            try:
                data = self.connector.search(payload)
            except:
                raise Exception

            unresolvedIssues = IssuesList.fromData('helpdesk.tools.unresolved', data['issues'])

            return unresolvedIssues

    def getUrgentIssues(self, request):
        trackers = ','.join(trackersBook[tracker].keystone for tracker in trackersBook)
        # print(trackers)
        startAt = 0
        if request == 'upcoming':
            payload = {'fields': IssuesFactory.fields,
                       'maxResults': 1000, 'startAt': startAt,
                       'jql': "duedate >= 0d AND duedate <= 7d AND status != Closed AND project in ({})"
                       .format(trackers)}

            # print(payload)
            try:
                data = self.connector.search(payload)
            except Exception:
                raise Exception

            issues_list = IssuesList.fromData('urgent.upcoming', data['issues'])

            return issues_list

        if request == 'impeded':
            payload = {'fields': IssuesFactory.fields,
                       'maxResults': 1000, 'startAt': startAt,
                       'jql': 'status = Impeded AND project in ({})'.format(trackers)}
            try:
                data = self.connector.search(payload)
            except:
                raise Exception

            impeded_list = IssuesList.fromData('urgent.impeded', data['issues'])

            return impeded_list

        if request == 'blockers':
            payload = {'fields': IssuesFactory.fields,
                       'maxResults': 1000, 'startAt': startAt,
                       'jql': 'issueType not in (Risk, eRequest) AND priority in '
                              '(Blocker, Critical) AND status != Closed AND project in ({})'
                       .format(trackers)}

            try:
                data = self.connector.search(payload)
            except:
                raise Exception

            blocker_list = IssuesList.fromData('urgent.blockers', data['issues'])

            return blocker_list

        if request == 'overdue':
            payload = {'fields': IssuesFactory.fields,
                       'maxResults': 1000, 'startAt': startAt,
                       'jql': 'duedate < now() AND status != Closed AND project in ({})'
                       .format(trackers)}
            try:
                data = self.connector.search(payload)
            except:
                raise Exception

            overdue_list = IssuesList.fromData('urgent.overdue', data['issues'])

            return overdue_list

        if request == 'aged':
            payload = {'fields': IssuesFactory.fields,
                       'maxResults': 1000, 'startAt': startAt,
                       'jql': 'created < -100d AND issuetype not in (Epic, Feature) '
                              'and status not in (Closed, Done, Dismissed) '
                              'and fixVersion = EMPTY AND project in ({})'.format(trackers)}
            try:
                data = self.connector.search(payload)
            except:
                raise Exception

            aged_list = IssuesList.fromData('urgent.aged', data['issues'])

            return aged_list

    def getIssuesFromRequest(self, request):
        jira = JIRA()
        # print('getIssuesFromRequest', request)
        startAt = 0
        payload = {'fields': IssuesFactory.fields,
                   'maxResults': 1000, 'startAt': startAt,
                   'jql': IssuesFactory.jql[request]}

        # print(payload)
        try:
            data = jira.search(payload)
        except Exception:
            raise Exception('Failure connecting JIRA')

        issues_list = IssuesList.fromData(request, data['issues'])
        return issues_list


if __name__ == "__main__":
    pass
