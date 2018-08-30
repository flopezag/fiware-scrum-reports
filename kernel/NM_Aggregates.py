import re
from datetime import date
from operator import attrgetter
from collections import Counter
from itertools import accumulate
from calendar import monthrange
from kernel.NM_Issue import extRequest, eRequest, Monitor, WorkItem, Epic, Feature, Story, Bug, Risk, iWorkItem, iBug
from kernel.IssuesModel import backlogIssuesModel
from kernel.Calendar import calendar as FWcalendar

__author__ = "Manuel Escriche <mev@tid.es>"

_IssueTypes = {
    'Epic': Epic, 'Feature': Feature, 'Story': Story, 'Bug': Bug,
    'WorkItem': WorkItem, 'Risk':Risk,
    'extRequest':extRequest, 'eRequest':eRequest, 'Monitor': Monitor
}


# Help Desk


class _Deck(list):
    def __init__(self):
        super().__init__()

    @property
    def status(self):
        count = Counter([issue.status for issue in self])
        return {status:count[status] for status in ('Open', 'In Progress', 'Impeded', 'Answered', 'Closed') }

    @property
    def issueType(self):
        count = Counter([issue.issueType for issue in self])
        return {type:count[type] for type in self._issueTypes}

    @property
    def unresolved(self):
        return [issue for issue in self if not issue.resolved]

    @property
    def resolved(self):
        return [issue for issue in self if issue.resolved]

    @property
    def resolution(self):
        return Counter([issue.resolution for issue in self.resolved])

    @property
    def lastResolved(self):
        issues = [issue for issue in [issue for issue in self if issue.resolved]
                  if (date.today() - issue.resolutionDate).days <= 60
                  ]

        return sorted(issues, key=attrgetter('resolutionDate'), reverse=True)

    @property
    def resolution_level(self):
        # assert len(self) == 0, 'empty deck'
        try:
            result = len(self.unresolved) / len(self)
        except:
            raise
        else:
            return result

    @property
    def monthly_evolution_graph_data(self):
        month_length = monthrange(date.today().year, date.today().month)[1]
        month, year = FWcalendar.monthBook[FWcalendar.currentMonth[1]].split('-')
        createdIssues = Counter([issue.created.day for issue in self
                                 if issue.created.month == int(month) and issue.created.year == int(year)])
        createdData = list(accumulate([createdIssues[day] for day in range(1, date.today().day+1)]))

        resolvedIssues = Counter([issue.resolutionDate.day for issue in self
                                  if issue.resolved and issue.resolutionDate.month == int(month) and issue.resolutionDate.year == int(year)])
        progressData = [resolvedIssues[day] for day in range(1, date.today().day+1)]
        resolvedData = list(accumulate(progressData))

        categories = [day for day in range(1, month_length+1)]
        outdata = dict()
        outdata['categories'] = categories
        outdata['ncategories'] = len(categories) - 1
        outdata['created'] = dict()
        outdata['created']['type'] = 'spline'
        outdata['created']['name'] = 'Created'
        outdata['created']['data'] = createdData
        outdata['resolved'] = dict()
        outdata['resolved']['type'] = 'spline'
        outdata['resolved']['name'] = 'Resolved'
        outdata['resolved']['data'] = resolvedData
        outdata['progress'] = dict()
        outdata['progress']['type'] = 'column'
        outdata['progress']['name'] = 'Progress'
        outdata['progress']['data'] = progressData
        return outdata

    @property
    def monthly_resolutionTime_graph_data(self):
        month, year = FWcalendar.monthBook[FWcalendar.currentMonth[1]].split('-')
        issues_set = [issue for issue in self
                                 if (issue.resolved and
                                     issue.resolutionDate.month == int(month) and
                                     issue.resolutionDate.year == int(year)) or
                                 not issue.resolved]

        count = Counter([issue.age for issue in issues_set])
        if not count: return {}
        _min,_max = min(count.keys()), max(count.keys())

        pending_count = Counter([issue.age for issue in issues_set if not issue.resolved ])
        pending_data = [pending_count[k] for k in range(_min,_max+1)]

        data_count = Counter([issue.age for issue in issues_set if issue.resolved])
        data = [data_count[k] for k in range(_min,_max+1)]

        outdata = {}
        outdata['categories'] = [k for k in range(_min,_max+1)]
        outdata['time'] = dict()
        outdata['time']['type'] = 'column'
        outdata['time']['name'] = 'Solved Issues'
        outdata['time']['data'] = data
        outdata['age'] = dict()
        outdata['age']['type'] = 'column'
        outdata['age']['name'] = "Pending issues"
        outdata['age']['color'] = '#ff4040'
        outdata['age']['data'] = pending_data
        return outdata


class Deck(_Deck):
    _issueTypes = ('extRequest', 'eRequest', 'Monitor')

    def __init__(self, data, timestamp, source):
        super().__init__()
        self.data = data
        self.timestamp = timestamp
        self.source = source
        for item in data:
            _type = item['fields']['issuetype']['name']

            if _type not in ('extRequest', 'eRequest', 'Monitor'):
                continue

            try:
                self.append(_IssueTypes[_type](item))
            except Exception as error:
                raise Exception('Error while creating issue')


class EnablerDeck(Deck):
    def __init__(self, enabler, data, timestamp, source):
        indata = list()
        for item in data:
            try:
                if item['fields']['customfield_11105']['value'] == enabler.name: indata.append(item)
            except: continue
        super().__init__(indata, timestamp, source)
        self.enabler = enabler

        pattern = r'FIWARE\.(Request|Question)\.Tech\.{}\.{}(\.[A-Z][\w\-]+)'.format(self.enabler.chapter,
                                                                                     self.enabler.backlogKeyword) \
                 + r'{2,}$'
        for issue in self:
            issue.OkTestName = True if re.match(pattern, issue.summary) else False


class ChapterDeck(Deck):
    def __init__(self, chapter, data, timestamp, source):
        self.chapter = chapter
        indata = list()
        for item in data:
            try:
                if item['fields']['customfield_11103']['value'] == chapter.name:
                    indata.append(item)
            except:
                continue

        super().__init__(indata, timestamp, source)
        #pattern = re.compile(r'FIWARE\.(Request|Question)\.Tech\.{}\.'.format(self.chapter.name))
        pattern = r'FIWARE\.(Request|Question)\.Tech\.{}(\.[A-Z][\w\-]+)'.format(self.chapter.name) + r'{2,}$'
        for issue in self:
            issue.OkTestName = True if re.match(pattern, issue.summary) else False


class NodeDeck(Deck):
    def __init__(self, node, data, timestamp, source):
        self.node = node
        super().__init__(data, timestamp, source)
        pattern = r'FIWARE\.(Request|Question)\.Lab\.{}(\.[A-Z][\w\-]+)'.format(self.node.name) + r'{2,}$'

        for issue in self:
            issue.OkTestName = True if re.match(pattern, issue.summary) else False


class ChannelDeck(Deck):
    '''External help desk channel'''
    def __init__(self, channel, data, timestamp, source):
        self.channel = channel
        super().__init__(data, timestamp, source)

    #@property
    #def issueType(self):
    #    return Counter([issue.issueType for issue in self])
        #return {type:count[type] for type in count}


class DeskDeck(Deck):
    '''External help desk channel'''
    def __init__(self, desk, data, timestamp, source):
        self.desk = desk
        super().__init__(data, timestamp, source)


class iDeck(_Deck):
    _IssueTypes = { 'Bug': iBug, 'WorkItem': iWorkItem}
    _issueTypes = ('Bug', 'WorkItem')

    def __init__(self, data, timestamp, source):
        super().__init__()
        self.data = data
        self.timestamp = timestamp
        self.source = source
        for item in data:
            _type = item['fields']['issuetype']['name']
            if not _type in iDeck._issueTypes: continue
            try:
                self.append(iDeck._IssueTypes[_type](item))
            except Exception as error:
                raise Exception('Error while creating issue')


class InnChannel(iDeck):
    '''Inner Help Desk Channel '''
    def __init__(self, data, timestamp, source):
        super().__init__(data, timestamp, source)


class DeskiDeck(iDeck):
    '''External help desk channel'''
    def __init__(self, desk, data, timestamp, source):
        self.desk = desk
        super().__init__(data, timestamp, source)


# Backlogs
class Backlog(list):
    Perspectives = ('Implemented', 'Working On', 'Foreseen')

    def __init__(self, timestamp, source):
        super().__init__()
        self.timestamp = timestamp
        self.source = source

    @property
    def issueType(self):
        count = Counter([issue.issueType for issue in self])
        return {type:count[type] for type in self._issueTypes}

    @property
    def perspective(self):
        count = Counter([issue.frame for issue in self])
        return {frame:count[frame] for frame in self.Perspectives}

    @property
    def status(self):
        count = Counter([issue.status for issue in self if issue.frame == 'Working On'])
        return {status:count[status] for status in count }

    @property
    def sprint_status(self):
        count = Counter([issue.status for issue in self
                         if issue.frame == 'Working On' and issue.issueType in backlogIssuesModel.shortTermTypes])
        return {status:count[status] for status in count}


class WorkBacklog(Backlog):
    _issueTypes = ('WorkItem',)

    def __init__(self, data, timestamp, source):
        super().__init__(timestamp, source)
        for item in data:
            _type = item['fields']['issuetype']['name']
            if not _type in WorkBacklog._issueTypes: continue
            try:
                self.append(_IssueTypes[_type](item))
            except Exception:
                raise Exception('Error while creating issue')


class RiskBacklog(Backlog):
    _issueTypes = ('WorkItem', 'Risk')

    def __init__(self, data, timestamp, source):
        super().__init__(timestamp, source)

        for item in data:
            _type = item['fields']['issuetype']['name']
            if not _type in RiskBacklog._issueTypes: continue
            try:
                self.append(_IssueTypes[_type](item))
            except Exception:
                print(item)
                raise Exception('Error while creating issue')


class DevBacklog(Backlog):
    _issueTypes = ('Epic', 'Feature', 'Story', 'Bug', 'WorkItem')

    def __init__(self, data, timestamp, source):
        super().__init__(timestamp, source)
        for item in data:
            _type = item['fields']['issuetype']['name']
            if not _type in DevBacklog._issueTypes: continue
            try:
                self.append(_IssueTypes[_type](item))
            except Exception:
                raise Exception('Error while creating issue')


class WorkGroupBacklog(Backlog):
    _issueTypes = ('Feature', 'Story', 'Bug', 'WorkItem')

    def __init__(self, data, timestamp, source):
        super().__init__(timestamp, source)
        for item in data:
            _type = item['fields']['issuetype']['name']

            if not _type in DevBacklog._issueTypes:
                continue

            try:
                self.append(_IssueTypes[_type](item))
            except Exception:
                raise Exception('Error while creating issue')


if __name__ == "__main__":
    pass
