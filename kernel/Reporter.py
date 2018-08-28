from datetime import date
from itertools import accumulate
from calendar import monthrange

from collections import Counter
from kernel.ComponentsBook import enablersBook, toolsBook
from kernel.TrackerBook import chaptersBook
from kernel.Backlog import Backlog, Issue
from kernel.IssuesModel import backlogIssuesModel
from kernel.Calendar import calendar as FWcalendar

__author__ = "Manuel Escriche <mev@tid.es>"


class Reporter:

    def __init__(self, backlog):
        self.backlog = backlog

    @property
    def impeded(self):
        return self.backlog.impeded

    @property
    def blockers(self):
        return self.backlog.blockers

    @property
    def epics(self):
        return self.backlog.epics

    @property
    def operativeIssues(self):
        return self.backlog.operativeIssues

    @property
    def sortDict(self):
        return Backlog._sortDict

    @property
    def issueType(self):
        count = Counter([issue.issueType for issue in self.backlog])
        return {issueType: count[issueType] for issueType in Backlog._issueTypes}

    @property
    def perspective(self):
        count = Counter([issue.frame for issue in self.backlog])
        return {frame: count[frame] for frame in Backlog._perspectives}

    @property
    def errors(self):
        count = Counter([issue.test.gStatus for issue in self.backlog])
        return {item: count[item] for item in ('OK', 'KO')}

    @property
    def status(self):
        count = Counter([issue.status for issue in self.backlog if issue.frame == 'Working On'])
        return {status:count[status] for status in count}

    @property
    def sprint_status(self):
        count = Counter([issue.status for issue in self.backlog
                         if issue.frame == 'Working On' and issue.issueType in backlogIssuesModel.shortTermTypes])
        return {status:count[status] for status in count}

    @property
    def implemented(self):
        book = FWcalendar.monthBook
        createdIssues = Counter(['{:02d}-{}'.format(issue.created.month, issue.created.year) for issue in self.backlog])
        createdData = list(accumulate([createdIssues[book[month]] for month in FWcalendar.pastMonths]))

        updatedIssues = Counter(['{:02d}-{}'.format(issue.updated.month, issue.updated.year) for issue in self.backlog])
        updatedData = list(accumulate([updatedIssues[book[month]] for month in FWcalendar.pastMonths]))

        closedIssues = [issue for issue in self.backlog if issue.status == 'Closed']
        resolvedIssues = Counter(['{:02d}-{}'.format(issue.resolved.month, issue.resolved.year) for issue in closedIssues])
        resolvedData = list(accumulate([resolvedIssues[book[month]] for month in FWcalendar.pastMonths]))

        finishedIssues = [issue for issue in closedIssues if issue.frame in ('Working On','Implemented')]
        releasedIssues = Counter(['{:02d}-{}'.format(issue.released.month, issue.released.year) for issue in finishedIssues])
        progressData = [releasedIssues[book[month]] for month in FWcalendar.pastMonths]
        releasedData = list(accumulate(progressData))

        outdata = {}
        outdata['categories'] = FWcalendar.timeline
        outdata['created'] = createdData
        outdata['resolved'] = resolvedData
        outdata['updated'] = updatedData
        outdata['released'] = releasedData
        outdata['progress'] = progressData
        return outdata

    @property
    def burndown(self):
        issues = [issue for issue in self.backlog if issue.frame == 'Working On' \
            and issue.issueType in backlogIssuesModel.shortTermTypes]

        closedIssues = Counter([issue.updated.day for issue in issues if issue.status == 'Closed'])
        #print(closedIssued)
        NIssues = len(issues)
        month_length = monthrange(date.today().year, date.today().month)[1]

        data = [(day, closedIssues[day]) for day in range(1, date.today().day+1)]
        #print(data)
        data = zip([item[0] for item in data], accumulate([item[1] for item in data]))
        data = {item[0]: NIssues-item[1] for item in data}
        #print(data)

        n = lambda x: NIssues/month_length if x > 0 else 0
        ref_data = {day : n(day) for day in range(1, month_length+1)}
        ref_data = dict(zip(ref_data.keys(), accumulate(ref_data.values())))
        ref_data = {day : round(abs(NIssues-ref_data[day]), 1) for day in ref_data}
        #print(ref_data)

        cdata = lambda d: data[d] if d in data else 'null'
        outdata = {}
        outdata['categories'] = [day for day in range(1, month_length+1)]
        outdata['reference'] = [ref_data[day] for day in range(1, month_length+1)]
        outdata['actual'] = [cdata(day) for day in range(1, date.today().day+1)]
        outdata['closed'] = [closedIssues[day] for day in range(1, date.today().day+1)]
        return outdata

    @property
    def issueType_graph_data(self):
        count = self.issueType
        return [[issueType, count[issueType]] for issueType in Backlog._issueTypes ]

    @property
    def perspective_graph_data(self):
        count = self.perspective
        return [[frame, count[frame]] for frame in Backlog._perspectives]

    @property
    def sprint_status_graph_data(self):
        count = self.sprint_status
        return [[status, count[status]] for status in count]

    @property
    def errors_graph_data(self):
        color = {'OK':'#bada55', 'KO':'#ff4040'}
        count = Counter([issue.test.gStatus for issue in self.backlog])
        return [{'name':_type, 'y': count[_type], 'color': color[_type]} for _type in count]

    @property
    def burndown_graph_data(self):
        issues = [issue for issue in self.backlog if issue.frame == 'Working On' \
            and issue.issueType in backlogIssuesModel.shortTermTypes]

        closedIssues = Counter([issue.updated.day for issue in issues if issue.status == 'Closed'])
        #print(closedIssued)
        NIssues = len(issues)
        month_length = monthrange(date.today().year, date.today().month)[1]

        data = [(day, closedIssues[day]) for day in range(1, date.today().day+1)]
        #print(data)
        data = zip([item[0] for item in data], accumulate([item[1] for item in data]))
        data = {item[0]: NIssues-item[1] for item in data}
        #print(data)

        n = lambda x: NIssues/month_length if x > 0 else 0
        ref_data = {day : n(day) for day in range(1, month_length+1)}
        ref_data = dict(zip(ref_data.keys(), accumulate(ref_data.values())))
        ref_data = {day : round(abs(NIssues-ref_data[day]), 1) for day in ref_data}
        #print(ref_data)

        cdata = lambda d: data[d] if d in data else 'null'
        outdata = {}
        outdata['categories'] = [day for day in range(1, month_length+1)]
        outdata['reference'] = dict()
        outdata['reference']['type'] = 'spline'
        outdata['reference']['name'] = 'Reference'
        outdata['reference']['data'] = [ref_data[day] for day in range(1, month_length+1)]
        outdata['reference']['marker'] = {'enabled': 'false'}
        outdata['reference']['dashStyle'] = 'shortdot'
        outdata['actual'] = dict()
        outdata['actual']['type'] = 'spline'
        outdata['actual']['name'] = 'Actual'
        outdata['actual']['data'] = [cdata(day) for day in range(1, date.today().day+1)]
        outdata['closed'] = dict()
        outdata['closed']['type'] = 'column'
        outdata['closed']['name'] = 'Closed'
        outdata['closed']['data'] = [closedIssues[day] for day in range(1, date.today().day+1)]
        return outdata

    @property
    def implemented_graph_data(self):
        book = FWcalendar.monthBook
        #issues = [issue for issue in self.backlog if issue.frame in ('Working On','Implemented') and issue.status == 'Closed']
        createdIssues = Counter(['{:02d}-{}'.format(issue.created.month, issue.created.year) for issue in self.backlog])
        createdData = list(accumulate([createdIssues[book[month]] for month in FWcalendar.pastMonths]))

        updatedIssues = Counter(['{:02d}-{}'.format(issue.updated.month, issue.updated.year) for issue in self.backlog])
        updatedData = list(accumulate([updatedIssues[book[month]] for month in FWcalendar.pastMonths]))

        closedIssues = [issue for issue in self.backlog if issue.status == 'Closed']
        resolvedIssues = Counter(['{:02d}-{}'.format(issue.resolved.month, issue.resolved.year) for issue in closedIssues])
        resolvedData = list(accumulate([resolvedIssues[book[month]] for month in FWcalendar.pastMonths]))

        finishedIssues = [issue for issue in closedIssues if issue.frame in ('Working On','Implemented')]
        releasedIssues = Counter(['{:02d}-{}'.format(issue.released.month, issue.released.year) for issue in finishedIssues])
        progressData = [releasedIssues[book[month]] for month in FWcalendar.pastMonths]
        releasedData = list(accumulate(progressData))

        outdata = {}
        outdata['categories'] = FWcalendar.timeline
        outdata['ncategories'] = len(FWcalendar.timeline) - 1
        outdata['created'] = dict()
        outdata['created']['type'] = 'spline'
        outdata['created']['name'] = 'Created'
        outdata['created']['data'] = createdData
        outdata['resolved'] = dict()
        outdata['resolved']['type'] = 'spline'
        outdata['resolved']['name'] = 'Resolved'
        outdata['resolved']['data'] = resolvedData
        outdata['updated'] = dict()
        outdata['updated']['type'] = 'spline'
        outdata['updated']['name'] = 'Updated'
        outdata['updated']['data'] = updatedData
        outdata['released'] = dict()
        outdata['released']['type'] = 'spline'
        outdata['released']['name'] = 'Released'
        outdata['released']['data'] = releasedData
        outdata['progress'] = dict()
        outdata['progress']['type'] = 'column'
        outdata['progress']['name'] = 'Progress'
        outdata['progress']['data'] = progressData
        return outdata

    @property
    def length(self):
        return len(self.backlog)

    def __len__(self):
        return len(self.backlog)

    def frame_length(self, frame):
        issues = [issue for issue in self.backlog if issue.frame == frame]
        return len(issues)

    def review(self):
        self.backlog.review()


class CoordinationReporter(Reporter):
    def __init__(self, chaptername, backlog):
        super().__init__(backlog)
        self.chaptername = chaptername
        self.backlog.review()

    @property
    def chapter(self):
        return chaptersBook[self.chaptername]

    @property
    def chaptersBook(self):
        return chaptersBook

    @property
    def frame_status_graph_data(self):
        frame='Working On'
        issues = [issue for issue in self.backlog if issue.frame == frame]
        #print('working on issues =', len(issues))
        statuses = sorted(set([issue.status for issue in issues]))
        #print('found statuses =', statuses)

        enablerIssuesBook = {}
        for enablername in enablersBook:
            enabler = enablersBook[enablername]
            enablerIssuesBook[enablername] = Counter([issue.status for issue in issues if enabler.key == issue.component])
                #print(enabler, dict(enablerIssuesBook[key]))

        _frame_status_graph_data = []
        for status in statuses:
            status_dict = {}
            status_dict['name'] = status
            status_dict['data'] = [enablerIssuesBook[enabler][status] for enabler in enablersBook]
            _frame_status_graph_data.append(status_dict)

        #print('frame_status_graph_data =', _frame_status_graph_data)
        return _frame_status_graph_data


class ChapterReporter(Reporter):
    def __init__(self, chaptername, backlog):
        super().__init__( backlog)
        self.chaptername = chaptername
        self.chapter = chaptersBook[chaptername]
        #start_time = time.time()
        backlog.review()
        #elapsed_time = time.time() - start_time
        #print(elapsed_time)

    @property
    def chaptersBook(self):
        return chaptersBook

    @property
    def enablers(self):
        return list(self.chapter.enablers.keys())

    @property
    def tools(self):
        return list(self.chapter.tools.keys())

    @property
    def coordination(self):
        return self.chapter.coordination

    @property
    def frame_status_graph_data(self):
        frame='Working On'
        issues = [issue for issue in self.backlog if issue.frame == frame and issue.component]

        statuses = sorted(set([issue.status for issue in issues]))
        chapterIssuesBook = {}
        for key in self.chapter.enablers:
            enabler = self.chapter.enablers[key]
            chapterIssuesBook[key] = Counter([issue.status for issue in issues if enabler.key == issue.component])

        _frame_status_graph_data = []
        for status in statuses:
            status_dict = {}
            status_dict['name'] = status
            status_dict['data'] = [chapterIssuesBook[enabler][status] for enabler in self.chapter.enablers]
            #print(status_dict)
            _frame_status_graph_data.append(status_dict)

        return _frame_status_graph_data

    @property
    def tools_frame_status_graph_data(self):
        frame='Working On'
        issues = [issue for issue in self.backlog if issue.frame == frame and issue.component]

        statuses = sorted(set([issue.status for issue in issues]))
        chapterIssuesBook = {}
        for key in self.chapter.tools:
            enabler = self.chapter.tools[key]
            chapterIssuesBook[key] = Counter([issue.status for issue in issues if enabler.key == issue.component])

        _frame_status_graph_data = []
        for status in statuses:
            status_dict = {}
            status_dict['name'] = status
            status_dict['data'] = [chapterIssuesBook[tool][status] for tool in self.chapter.tools]
            #print(status_dict)
            _frame_status_graph_data.append(status_dict)

        return _frame_status_graph_data

    @property
    def enablers_execution_status(self):
        frames = reversed(Issue._timeFrames)
        chapterIssuesBook = {}
        for key in self.chapter.enablers:
            enabler = self.chapter.enablers[key]
            chapterIssuesBook[key] = Counter([issue.frame for issue in self.backlog if enabler.key == issue.component])
        _frame_graph_data = []
        for frame in frames:
            frame_dict = {}
            frame_dict['name'] = frame
            frame_dict['data'] = [chapterIssuesBook[enabler][frame] for enabler in self.chapter.enablers]
            _frame_graph_data.append(frame_dict)
        return _frame_graph_data

    @property
    def tools_execution_status(self):
        frames = reversed(Issue._timeFrames)
        chapterIssuesBook = {}
        for key in self.chapter.tools:
            tool = self.chapter.tools[key]
            chapterIssuesBook[key] = Counter([issue.frame for issue in self.backlog if tool.key == issue.component])
        _frame_graph_data = []
        for frame in frames:
            frame_dict = {}
            frame_dict['name'] = frame
            frame_dict['data'] = [chapterIssuesBook[tool][frame] for tool in self.chapter.tools]
            _frame_graph_data.append(frame_dict)
        return _frame_graph_data


    @property
    def no_component(self):
        return [issue for issue in self.backlog if len(issue.components) == 0]


class ChaptersReporter(Reporter):
    def __init__(self, backlog):
        super().__init__(backlog)
        #start_time = time.time()
        backlog.review()
        #elapsed_time = time.time() - start_time
        #print(elapsed_time)

    @property
    def chapters_sprint_status_graph_data(self):
        frame='Working On'
        issues = [issue for issue in self.backlog
                  if issue.frame == frame and issue.issueType in backlogIssuesModel.shortTermTypes]

        statuses = sorted(set([issue.status for issue in issues]))

        chaptersIssuesBook = {}
        for chaptername in chaptersBook:
            chapter = chaptersBook[chaptername]
            chaptersIssuesBook[chaptername] = Counter([issue.status for issue in issues if chapter.tracker == issue.tracker ])

        _frame_status_graph_data = []
        for status in statuses:
            status_dict = {}
            status_dict['name'] = status
            status_dict['data'] = [chaptersIssuesBook[chapter][status] for chapter in chaptersBook]
            #print(status_dict)
            _frame_status_graph_data.append(status_dict)

        #print(_frame_status_graph_data)
        return _frame_status_graph_data

    @property
    def chapters_execution_status(self):
        frames = reversed(Issue._timeFrames)
        chaptersIssuesBook = {}
        for chaptername in chaptersBook:
            chapter = chaptersBook[chaptername]
            chaptersIssuesBook[chaptername] = Counter([issue.frame for issue in self.backlog if chapter.tracker == issue.tracker ])

        _frame_graph_data = []
        for frame in frames:
            frame_dict = {}
            frame_dict['name'] = frame
            frame_dict['data'] = [chaptersIssuesBook[chapter][frame] for chapter in chaptersBook]
            _frame_graph_data.append(frame_dict)
        return _frame_graph_data

    @property
    def chapters_errors_graph_data(self):
        color = {'OK':'#bada55', 'KO':'#ff4040'}
        values = ('OK', 'KO')
        chaptersIssuesBook = {}
        for key in chaptersBook:
            chapter = chaptersBook[key]
            #print(chapter)
            chaptersIssuesBook[key] = Counter([issue.test.gStatus for issue in self.backlog if chapter.tracker == issue.tracker ])
        #print(chaptersIssuesBook)
        _frame_errors_graph_data = []
        for value in values:
            errors_dict = {}
            errors_dict['name'] = value
            errors_dict['data'] = [chaptersIssuesBook[chapter][value] for chapter in chaptersBook]
            errors_dict['color'] = color[value]
            #print(status_dict)
            _frame_errors_graph_data.append(errors_dict)
        return _frame_errors_graph_data

    @property
    def chapters(self):
        return chaptersBook.chapters

    @property
    def enablers(self):
        return list(enablersBook.keys())

    @property
    def chaptersBook(self):
        return chaptersBook

    @property
    def nChapters(self):
        return len(chaptersBook)


    @property
    def enablers_execution_status(self):
        frames = reversed(Issue._timeFrames)
        issuesBook = {}
        for key in enablersBook:
            enabler = enablersBook[key]
            issuesBook[key] = Counter([issue.frame for issue in self.backlog if enabler.key == issue.component])
        _frame_graph_data = []
        for frame in frames:
            frame_dict = {}
            frame_dict['name'] = frame
            frame_dict['data'] = [issuesBook[enabler][frame] for enabler in enablersBook]
            _frame_graph_data.append(frame_dict)
        return _frame_graph_data


class ToolReporter(Reporter):
    def __init__(self, toolname, backlog):
        super().__init__(backlog)
        self.toolname = toolname
        self.backlog.review()

    @property
    def toolsBook(self):
        return toolsBook

    @property
    def tool(self):
        return toolsBook[self.toolname]


class EnablerReporter(Reporter):
    def __init__(self, enablername, backlog):
        super().__init__(backlog)
        self.enablername = enablername
        self.backlog.review()

    @property
    def enablersBook(self):
        return enablersBook

    @property
    def enabler(self):
        return enablersBook[self.enablername]


class EnablersReporter(Reporter):
    def __init__(self, backlog):
        super().__init__(backlog)
        #start_time = time.time()
        backlog.review()
        #elapsed_time = time.time() - start_time
        #print(elapsed_time)

    @property
    def enablers_sprint_status_graph_data(self):
        frame='Working On'
        issues = [issue for issue in self.backlog
                  if issue.frame == frame and self.enablers and issue.issueType in backlogIssuesModel.shortTermTypes]
        #print('working on issues =', len(issues))
        statuses = sorted(set([issue.status for issue in issues]))
        #print('found statuses =', statuses)

        enablerIssuesBook = {}
        for enablername in enablersBook:
            enabler = enablersBook[enablername]
            enablerIssuesBook[enablername] = Counter([issue.status for issue in issues if enabler.key == issue.component ])
                #print(enabler, dict(enablerIssuesBook[key]))

        _frame_status_graph_data = []
        for status in statuses:
            status_dict = {}
            status_dict['name'] = status
            status_dict['data'] = [enablerIssuesBook[enabler][status] for enabler in enablersBook]
            _frame_status_graph_data.append(status_dict)

        #print('frame_status_graph_data =', _frame_status_graph_data)
        return _frame_status_graph_data

    @property
    def enablers_errors_graph_data(self):
        color = {'OK':'#bada55', 'KO':'#ff4040'}
        values = ('OK', 'KO')
        enablerIssuesBook = {}
        for enablername in enablersBook:
            enabler = enablersBook[enablername]
            #print(chapter)
            enablerIssuesBook[enablername] = Counter([issue.test.gStatus for issue in self.backlog
                                                      if enabler.key == issue.component])
        #print(chaptersIssuesBook)
        _frame_errors_graph_data = []
        for value in values:
            errors_dict = {}
            errors_dict['name'] = value
            errors_dict['data'] = [enablerIssuesBook[enabler][value] for enabler in enablersBook]
            errors_dict['color'] = color[value]
            #print(status_dict)
            _frame_errors_graph_data.append(errors_dict)
        return _frame_errors_graph_data

    @property
    def enablers(self):
        return list(enablersBook.keys())

    @property
    def enablersBook(self):
        return enablersBook


if __name__ == "__main__":
    pass
