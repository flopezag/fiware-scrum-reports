import os
import re
import pickle

from datetime import date, datetime
from collections import Counter, defaultdict, namedtuple
from operator import attrgetter

from kernel.Settings import settings
from kernel.Calendar import agileCalendar
from kernel.TrackerBook import trackersBookByName, trackersBook, chaptersBookByKey
from kernel.ComponentsBook import coordinationBook, enablersBookByKey, enablersBook, toolsBook
from kernel.Connector import Connector
from kernel.Reviewer import Reviewer
from kernel.Publisher import Publisher
from kernel.DataFactory import DataEngine

__author__ = "Manuel Escriche <mev@tid.es>"


class TestRecord:
    def __init__(self):
        self.test = defaultdict(lambda: 'NT')
        self.status = defaultdict(lambda: 'NT')

    @property
    def gStatus(self):
        return 'OK' if all([v == 'OK' for v in self.status.values() if v != 'NT']) else 'KO'
#

class Issue(dict):
    _timeFrames = ('Foreseen', 'Working On', 'Implemented')

    def __init__(self, issue):
        super().__init__()
        # print(issue['fields'])
        self.backlog = None
        self.openDescription = None
        self.project = 'FIWARE'
        self.test = TestRecord()

        self['key'] = issue['key']

        self['tracker_key'] = issue['fields']['project']['key']
        # print(issue['fields']['project']['key'])
        # self.tracker = trackersBook.getTracker(self['_project'])
        # print(self.tracker)
        try:
            self['cmp_key'] = [item['id'] for item in issue['fields']['components']][0]
        except Exception:
            self['cmp_key'] = None
        # self.enabler = enablersBook.get_enabler(self['component']) if len(self['component']) > 0 else None
        # self.enabler = enablersBook.getEnabler(self.tracker.keystone, self['component']) \
        #    if len(self['component']) > 0 and self.tracker else None
        # print(issue['fields']['project'])


        self['summary'] = issue['fields']['summary'].strip()
        self['status'] = issue['fields']['status']['name']

        try:
            self['priority'] = issue['fields']['priority']['name']
        except TypeError:
            print(issue)

        self['issueType'] = issue['fields']['issuetype']['name']
        self['description'] = issue['fields']['description']

        self['dissemination'] = enablersBookByKey[self['cmp_key']].dissemination \
            if self['issueType'] in ('Feature', 'Epic') and self['cmp_key'] in enablersBookByKey else 'Private'

        self['reporter'] = issue['fields']['reporter']['displayName']

        if issue['fields']['resolution'] != None:
            self['resolution'] = issue['fields']['resolution']['name'] \
            if 'name' in issue['fields']['resolution'] else None
        else:
            self['resolution'] = None

        if issue['fields']['assignee'] != None:
            self['assignee'] = issue['fields']['assignee']['displayName'] \
                if 'displayName' in issue['fields']['assignee'] else None
        else: self['assignee'] = None

        if 'duedate' in issue['fields']:
            self['duedate'] = datetime.strptime(issue['fields']['duedate'][:10], '%Y-%m-%d').date() \
                if issue['fields']['duedate'] else None
        else:
            self['duedate'] = None

        self['created'] =  datetime.strptime(issue['fields']['created'][:10], '%Y-%m-%d').date()
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
                self['releaseDate'] = datetime.strptime(issue['fields']['fixVersions'][0]['releaseDate'][:10], '%Y-%m-%d').date()

        self['jurl'] = "http://jira.fiware.org/browse/{}".format(issue['key'])
        self['purl'] = "http://forge.fiware.org/plugins/mediawiki/wiki/fiware/index.php/{}".format(self['summary']) \
            if self['dissemination'] == 'Open' else None


        _version = self['version'].split()
        if len(_version) == 1:
            version = 'Unscheduled'
        else:
            version = _version[1]

        if version == 'Unscheduled':
            self['frame'] = 'Foreseen'
        elif version in agileCalendar.pastTimeSlots:
            self['frame'] = 'Implemented'
        elif version in agileCalendar.currentTimeSlots():
            self['frame'] = 'Working On'
        elif version in agileCalendar.futureTimeSlots:
            self['frame'] = 'Foreseen'
        else:
            self['frame'] = 'Unknown'

        self.father = None
        self.sons = None

    def name_test(self):
        chunks = self['summary'].split('.')
        if len(chunks) < 3: return False
        project = chunks[0]
        issueType = chunks[1]
        return True if project == 'FIWARE' and issueType == self['issueType'] else False

    @property
    def key(self):
        return self['key']

    @property
    def nkey(self):
        return int(self['key'].split('-')[1])

    @property
    def frame(self):
        return self['frame']

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
    def created(self):
        return self['created']

    @property
    def resolved(self):
        return self['resolved']

    @property
    def updated(self):
        return self['updated']

    @property
    def released(self):
        return self['releaseDate']

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
        return self['assignee']

    @property
    def age(self):
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
    def tracker(self):
        return self['tracker_key']

    @property
    def chapter(self):
        return chaptersBookByKey[self['tracker_key']].name

    @property
    def component(self):
        return self['cmp_key']

    @property
    def dissemination(self):
        return self['dissemination']

    @property
    def url(self):
        return self['jurl']

    @property
    def p_url(self):
        return self['purl']

    @property
    def OKtests(self):
        return self.test.gStatus == 'OK'

    @property
    def getErrorMessage(self):
        # print('getErrorMessage')
        broken_rule = None
        broken_test = None

        rules = list(self.backlog.reviewer.testBook.store) + list(self.backlog.publisher.testBook.store)
        # print(rules)

        for rule in rules:
            if self.test.status[rule] == 'KO':
                broken_rule = rule
                break
        # print(broken_rule)

        for test in sorted(self.test.test[broken_rule], key=lambda x:x):
            if self.test.test[broken_rule][test] == 'KO':
                broken_test = test
                break
        # print(broken_test)

        if broken_rule in self.backlog.reviewer.testBook.store:
            return  '>>> {} > {}'.format(broken_test, self.backlog.reviewer.testBook.store[broken_rule][broken_test])
        if broken_rule in self.backlog.publisher.testBook.store:
            return '>>> {} > {}'.format(broken_test, self.backlog.publisher.testBook.store[broken_rule][broken_test])
        return '>>> rule not found'

    def __repr__(self):
        return '{1},{0.key},{2}'.format(self, self['tracker_key'], self['cmp_key'])


class Backlog(list):
    _sortDict = {'keyn': lambda x:x.nkey,
                 'key': lambda x:x.key,
                 'issueType': lambda x:x.issueType,
                 'name': lambda x:x.name,
                 'status': lambda x:x.status,
                 'priority': lambda x:x.priority,
                 'timeSlot': lambda x:x.timeSlot,
                 'assignee': lambda x:x.assignee,
                 'duedate': lambda x:x.duedate,
                 'age': lambda x:x.age,
                 'delay': lambda x:x.delay}

    _issueTypes = ('Epic','Feature','Story','WorkItem','Bug')
    _perspectives = ('Implemented', 'Working On', 'Foreseen')

    def __init__(self, issuesList, timestamp=None):
        super().__init__()
        if issuesList:
            for issue in issuesList:
                issue.backlog = self
                self.append(issue)
        # set up reviewers
        self.timestamp = timestamp if timestamp else datetime.now().strftime("%Y%m%d-%H%M")
        self.reviewer = Reviewer()
        self.publisher = Publisher()
        self.rules = list(self.reviewer.testBook.store) + list(self.publisher.testBook.store)

    @classmethod
    def fromData(cls, data, timestamp=None):
        issuesList = list()
        for issue in data: issuesList.append(Issue(issue))
        return cls(issuesList, timestamp)

    def review(self):
        # print('review')
                ### build hierarchy
        for item in self:
            item.father = [item1 for item1 in self if item.shortReference.rpartition('.')[0] == item1.shortReference]
            item.sons = [item1 for item1 in self if item.shortReference == item1.shortReference.rpartition('.')[0]]

        for issue in self:
            # print(issue.reference)
            for rule in self.reviewer.testBook:
                self.reviewer.testBook[rule](issue)
            if issue.OKtests and issue.dissemination == 'Open':
                for rule in self.publisher.testBook:
                    self.publisher.testBook[rule](issue)
            # print(issue.reference)
            # print(issue.test.status)
            # print(issue.test.test)

    @property
    def impeded(self):
        return Backlog([issue for issue in self if issue.status == 'Impeded'])

    @property
    def blockers(self):
        return Backlog([issue for issue in self if issue.priority == 'Blocker'])

    @property
    def epics(self):
        return Backlog([issue for issue in self if issue.issueType == 'Epic'])

    @property
    def operativeIssues(self):
        return Backlog([issue for issue in self if issue.issueType != 'Epic'])

    @property
    def wrong(self):
        return [issue for issue in self if not issue.OKtests]

    @property
    def sortDict(self):
        return Backlog._sortDict

    @property
    def issueType(self):
        count = Counter([issue.issueType for issue in self])
        return {issueType:count[issueType] for issueType in Backlog._issueTypes}

    @property
    def perspective(self):
        count = Counter([issue.frame for issue in self])
        return {frame:count[frame] for frame in Backlog._perspectives}

    @property
    def status(self):
        count = Counter([issue.status for issue in self if issue.frame == 'Working On'])
        return {status:count[status] for status in count }

    @property
    def testStatus(self):
        return {rule: all([issue.test.status[rule] == 'OK' for issue in self
                           if issue.test.status[rule] != 'NT'])
                for rule in self.rules }

    @property
    def testMetrics(self):
        metrics = dict()
        metrics['OK'] = Counter([rule for issue in self for rule in issue.test.test
                            for test in issue.test.test[rule]
                            if issue.test.test[rule][test] == 'OK'])
        metrics['KO'] = Counter([rule for issue in self for rule in issue.test.test
                            for test in issue.test.test[rule]
                            if issue.test.test[rule][test] == 'KO'])
        return metrics

    def getChapter(self, chaptername):
        # print('backlog -> getChapter', chaptername)
        return Backlog([issue for issue in self if issue.chapter == chaptername])

    def getEnabler(self, enablername):
        # print('backlog -> getEnabler', enablername)
        issues = []
        for issue in self:
            if issue.enabler:
                if issue.enabler[0].name == enablername:
                    issues.append(issue)
        return Backlog(issues)


class BacklogFactory:
    _fields = '*navigable'
    fields = 'summary,status,project,components,priority,issuetype,description,reporter,' \
             'resolution,assignee,created,updated,duedate,resolutiondate,fixVersions,releaseDate'

    instance = None

    @classmethod
    def getInstance(cls):
        if cls.instance is None:
             cls.instance = BacklogFactory()
        return cls.instance

    def __init__(self):

        self.connector = Connector.getInstance()

    def getCoordinationBacklog(self, chaptername):
        return self._getComponentBacklog(coordinationBook[chaptername].key)

    def getChaptersBacklog(self):
        return self._getTrackersBacklog('CHAPTER')

    def getChapterBacklog(self, chaptername):
        return self._getTrackerBacklog(chaptername)

    def getEnablersBacklog(self):
        components = ','.join(enablersBook[enabler].key for enabler in enablersBook)
        return self._getComponentsBacklog(components)

    def getEnablerBacklog(self, enablername):
        enabler = enablersBook[enablername]
        return self._getComponentBacklog(enabler.key)

    def getToolBacklog(self, toolname):
        tool = toolsBook[toolname]
        return self._getComponentBacklog(tool.key)


    def _getComponentsBacklog(self, comp_ids):
        # print('_getComponentsBacklog')
        startAt = 0
        payload = {'fields': BacklogFactory.fields,
                    'maxResults': 1000, 'startAt': startAt,
                    'jql': 'component in ({})'.format(comp_ids)}
        try:
            data = self.connector.search(payload)
        except:
            raise Exception

        totalIssues, receivedIssues = data['total'], len(data['issues'])
        while totalIssues > receivedIssues:
            payload['startAt'] = receivedIssues
            data['issues'].extend(self.connector.search(payload)['issues'])
            receivedIssues = len(data['issues'])
            # print('total=', totalIssues, ' received=', receivedIssues)
        return Backlog.fromData(data['issues'])

    def _getComponentBacklog(self, comp_id):
        # print('_getComponentBacklog')
        startAt = 0
        payload = {'fields': BacklogFactory.fields,
                   'maxResults': 1000, 'startAt': startAt,
                   'jql': 'component={}'.format(comp_id)}

        try:
            data = self.connector.search(payload)
        except:
            raise Exception

        totalIssues, receivedIssues = data['total'], len(data['issues'])
        while totalIssues > receivedIssues:
            payload['startAt'] = receivedIssues
            data['issues'].extend(self.connector.search(payload)['issues'])
            receivedIssues = len(data['issues'])

        # print(len(data['issues']))
        return Backlog.fromData(data['issues'])

    def _getTrackersBacklog(self, trackertype):
        # print('_getTrackersBacklog')
        trackers = ','.join(trackersBook[tracker].keystone for tracker in trackersBook if trackersBook[tracker].type == trackertype)
        startAt = 0
        payload = {'fields': BacklogFactory.fields,
                    'maxResults': 1000, 'startAt': startAt,
                    'jql': 'project in ({})'.format(trackers)}
        try:
            data = self.connector.search(payload)
        except:
            raise Exception

        totalIssues, receivedIssues = data['total'], len(data['issues'])

        while totalIssues > receivedIssues:
            payload['startAt'] = receivedIssues
            try:
                data['issues'].extend(self.connector.search(payload)['issues'])
            except:
                raise Exception

            receivedIssues = len(data['issues'])
        return Backlog.fromData(data['issues'])

    def _getTrackerBacklog(self, trackername):
        # print('_getTrackerBacklog')
        tracker = trackersBook[trackername]
        startAt = 0
        payload = {'fields': BacklogFactory.fields,
                   'maxResults': 1000, 'startAt': startAt,
                   'jql': 'project={}'.format(tracker.keystone)}
        try:
            data = self.connector.search(payload)
        except:
            raise Exception

        totalIssues, receivedIssues = data['total'], len(data['issues'])
        # print('total=', totalIssues, ' received=', receivedIssues)
        while totalIssues > receivedIssues:
            payload['startAt'] = receivedIssues
            try:
                data['issues'].extend(self.connector.search(payload)['issues'])
            except:
                raise Exception

            receivedIssues = len(data['issues'])
            # print('total=', totalIssues, ' received=', receivedIssues)
        if 'issues' not in data:
            return

        return Backlog.fromData(data['issues'])


class LocalBacklogFactory:

    instance = None

    @classmethod
    def getInstance(cls):
        if cls.instance is None:
            cls.instance = LocalBacklogFactory()

        return cls.instance

    def __init__(self):
        self.trackersData = dict()
        for trackername in trackersBook:
            trackerkey = trackersBook[trackername].key
            self.trackersData[trackerkey] = self.load(trackername)
            self.clean(trackername)

    def getCoordinationBacklog(self, chaptername):
        cmp = trackersBookByName[chaptername].coordination
        trackerData, timestamp = self.trackersData[cmp.tracker]
        data = list()
        for item in trackerData:
            try:
                _id = item['fields']['components'][0]['id']
            except Exception:
                continue

            if cmp.key == _id:
                data.append(item)

        return Backlog.fromData(data, timestamp)

    def getEnablerBacklog(self, enablername):
        enabler = enablersBook[enablername]
        trackerData, timestamp = self.trackersData[enabler.tracker]
        data = list()
        for item in trackerData:
            try:
                _id = item['fields']['components'][0]['id']
            except Exception:
                continue

            if enabler.key == _id: data.append(item)

        return Backlog.fromData(data, timestamp)

    def getToolBacklog(self, toolname):
        tool = toolsBook[toolname]
        trackerData, timestamp = self.trackersData[tool.tracker]
        data = list()
        for item in trackerData:
            try:
                _id = item['fields']['components'][0]['id']
            except Exception:
                continue

            if tool.key == _id:
                data.append(item)

        return Backlog.fromData(data, timestamp)

    def load(self, trackername):
        # fileList = os.listdir(settings.storeHome)
        # mfilter = re.compile(r'\bFIWARE\.tracker\.(?P<tracker>[\w\-]+)\.(?P<day>\d{8})[-](?P<hour>\d{4})\.pkl\b')
        # record = namedtuple('record','tracker, filename, day, time')
        # files = [record(mfilter.match(f).group('tracker'),
        #                           mfilter.match(f).group(0),
        #                           mfilter.match(f).group('day'),
        #                           mfilter.match(f).group('hour'))
        #                    for f in fileList if mfilter.match(f) if mfilter.match(f).group('tracker') == trackername]
        #    #print(files)
        # files.sort(key = lambda e:(e.day, e.time), reverse=True)
        # filename= files[0].filename
        # _timestamp = '{}-{}'.format(files[0].day, files[0].time)
        # timestamp = datetime.strptime(_timestamp, '%Y%m%d-%H%M').strftime("%Y%m%d-%H%M")
        # with open(os.path.join(settings.storeHome, filename), 'rb') as f:
        #    data = pickle.load(f)
        # return data, timestamp

        dataEngine = DataEngine(settings.storeHome)
        trackerkey = trackersBook[trackername].key

        return dataEngine.getTrackerData(trackerkey)


        # print(timestamp)



    def clean(self, tracker):
        fileList = os.listdir(settings.storeHome)
        mfilter = re.compile(r'\bFIWARE\.tracker\.(?P<tracker>[\w\-]+)\.(?P<day>\d{8})[-](?P<hour>\d{4})\.pkl\b')
        record = namedtuple('record', 'filename, tracker, day, hour')
        filelist = [record(mfilter.match(f).group(0),
                           mfilter.match(f).group('tracker'),
                           mfilter.match(f).group('day'),
                           mfilter.match(f).group('hour')) for f in fileList if mfilter.match(f)
                    if mfilter.match(f).group('tracker') == tracker]
        filelist.sort(key=attrgetter('day', 'hour'), reverse=True)
        toRemove = filelist[5:]
        if len(toRemove) > 0:
            for item in toRemove:
                os.remove(os.path.join(settings.storeHome, item.filename))


if __name__ == "__main__":
    pass
