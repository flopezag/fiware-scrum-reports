__author__ = "Manuel Escriche <mev@tid.es>"

import ssl, certifi
import sys, os, xlsxwriter, re
from operator import attrgetter
from xlsxwriter.utility import xl_range
from datetime import date, datetime
from kernel.Calendar import agileCalendar

from kernel.TrackerBook import chaptersBook
from kernel.TComponentsBook import enablersBook
from kernel.Reporter import ChapterReporter, EnablerReporter
from kernel.DataFactory import DataEngine

from _Kernel.Settings import settings
from _Kernel.SheetFormats import SpreadsheetFormats
from _Kernel.BacklogFactory import BacklogFactory

from jira.client import JIRA

try:
    server = settings.server['JIRA']
    options={'server': 'https://{}'.format(server.domain), 'verify':False}
    jira = JIRA(options, basic_auth=(server.username, server.password))
except Exception('No connection to JIRA'):
    print(Exception)
    exit(0)

class Karma(dict):
    labels = {1:'hideous', 2:'bad', 3:'neutral', 4:'good', 5:'excellent'}
    def __init__(self, _type, reporter, **kwargs):
        super().__init__()
        self['type'] = _type
        self['name'] = kwargs['name']
        self['leader'] = kwargs['leader']

        status = reporter.sprint_status
        self['size'] = sum(status.values())
        self['performance']  = status['Closed']*100/sum(status.values()) if 'Closed' in status else 0
        self['errors'] = reporter.errors['KO']*100/sum(reporter.errors.values())

        try:
            sp_issue = kwargs['plan_issues'][0]
            self['planning'] = self.issue_status('Planning', sp_issue)
        except Exception:
            self['planning'] = 'Missing'

        try:
            sc_issue = kwargs['close_issues'][0]
            self['closing'] = self.issue_status('Closing', sc_issue)
        except Exception:
            self['closing'] = 'Missing'

        try:
            sr_issue = kwargs['feedback_issues'][0]
            self['feedback'] = self.issue_status('Feedback', sr_issue)
            issue = jira.issue(sr_issue.key)
            self['retrospective'] = len(issue.fields.comment.comments)
            print('Issue {} - Retrospective= {}'.format(issue, len(issue.fields.comment.comments) > 0))
        except Exception:
            self['feedback'] = 'Missing'
            self['retrospective'] = None

        self['karma'] = 0.60 * self.performance_rule() + 0.25 * self.errors_rule() + \
                        0.05 * self.planning_rule() + 0.05 * self.closing_rule() + 0.05 * self.feedback_rule()
        self['klabel'] = Karma.labels[int(round(self['karma'], 0))]

        self.karma = self['karma']
        self.size = self['size']
        self.performance = self['performance']

    def planning_rule(self):
        planning = self['planning']
        if planning == 'OK': return 5
        elif planning == 'Delayed': return 3
        else: return 0

    def closing_rule(self):
        if self['closing'] == 'OK': return 5
        elif self['closing'] == 'Delayed': return 3
        else: return 0

    def feedback_rule(self):
        if self['feedback'] == 'OK' and self['retrospective']: return 5
        elif self['retrospective']: return 3
        else: return 0

    def performance_rule(self):
        performance = self['performance']
        if performance <  50: return 1
        elif performance < 65: return 2
        elif performance < 80: return 3
        elif performance < 90: return 4
        else: return 5

    def errors_rule(self):
        errors = self['errors']
        if errors > 25: return 1
        elif errors > 10: return 2
        elif errors > 5: return 3
        elif errors > 0: return 4
        else: return 5

    def issue_status(self, head, issue):
        status = 'Available'
        try:
            if issue.resolved:
                status = 'OK' if issue.status == 'Closed' and issue.delay <= 0 else 'Delayed'
            else:
                status = 'Pending' if issue.delay <= 0 else 'Overdue'
            print('{}:'.format(head), issue.key, ' status=', status, ' duedate=', issue.duedate, ' resolved=', issue.resolved, ' delay=', issue.delay, issue.url)
        except:
            print('check duedate for {}'.format(issue.url))
        return status

class ChpKarma(Karma):
    def __init__(self, chapter, backlog, sprint):

        _sprint = re.sub('\.', '', sprint)
        _prev_sprint = re.sub('\.', '', agileCalendar.get_prev_sprint(sprint))

        sr_issues = [issue for issue in backlog
                           if re.match(r'FIWARE\.WorkItem\.{}\.Coordination\.Agile\.Sprint\-{}.Retrospective'.format(chapter.name,
                                                                                               _prev_sprint), issue.reference)]
        sp_issues = [issue for issue in backlog
                           if re.match(r'FIWARE\.WorkItem\.{}\.Coordination\.Agile\.Sprint\-{}.Planning'.format(chapter.name,
                                                                                               _sprint), issue.reference)]
        sc_issues = [issue for issue in backlog
                          if re.match(r'FIWARE\.WorkItem\.{}\.Coordination\.Agile\.Sprint\-{}.Close'.format(chapter.name,
                                                                                               _sprint), issue.reference)]
        reporter = ChapterReporter(chapter.name, backlog)

        super().__init__('chapter', reporter,
                         name=chapter.name, leader=chapter.leader,
                         plan_issues=sp_issues, close_issues=sc_issues, feedback_issues=sr_issues)


class EnablerKarma(Karma):
    def __init__(self, enabler, backlog, sprint):
        _sprint = re.sub('\.','', sprint)
        sp_issues = [issue for issue in backlog
                           if re.match(r'FIWARE\.WorkItem\.{}\.{}\.Agile\.Sprint\-{}.Planning'.format(enabler.chapter,
                                                                                               enabler.backlogKeyword,
                                                                                               _sprint), issue.reference)]
        sc_issues = [issue for issue in backlog
                          if re.match(r'FIWARE\.WorkItem\.{}\.{}\.Agile\.Sprint\-{}.Close'.format(enabler.chapter,
                                                                                               enabler.backlogKeyword,
                                                                                               _sprint), issue.reference)]
        reporter = EnablerReporter(enabler.name, backlog)

        super().__init__('enabler', reporter,
                         name=enabler.name, leader= enabler.leader,
                          plan_issues=sp_issues, close_issues= sc_issues, feedback_issues=sc_issues)



class KarmaReport:
    def __init__(self, sprint):
        self.workbook = None
        self.backlogFactory = None
        self.spFormats = None

        self.sprint = sprint
        self.prev_sprint = agileCalendar.get_prev_sprint(sprint)
        print('\nEvaluated Sprint {}'.format(self.sprint))
        print('Previous Sprint {}'.format(self.prev_sprint))

        _order = sorted(self.enablers(), key=attrgetter('performance'), reverse=True)
        self.enablers_karma = sorted(_order, key=attrgetter('karma'), reverse=True)

        _order = sorted(self.chapters(), key=attrgetter('performance'), reverse=True)
        self.chapters_karma = sorted(_order, key=attrgetter('karma'), reverse=True)


    def chapters(self):
        data = list()
        for chaptername in chaptersBook:
            print('\n{}'.format(chaptername))
            chapter = chaptersBook[chaptername]
            self.backlogFactory = BacklogFactory()
            backlog = self.backlogFactory.getChapterBacklog(chaptername)
            data.append(ChpKarma(chapter, backlog, self.sprint))
        return data

    def enablers(self):
        data = list()
        #condition = lambda x: x.mode not in ( 'Support', 'Deprecated', 'Incubated')
        for enablername in enablersBook:
        #for enablername in filter(condition, enablersBook.values()):
            if enablersBook[enablername].mode in ( 'Support', 'Deprecated', 'Incubated') : continue
            print('\n{}'.format(enablername))
            enabler = enablersBook[enablername]
            self.backlogFactory = BacklogFactory()
            backlog = self.backlogFactory.getEnablerBacklog(enablername)
            data.append(EnablerKarma(enabler, backlog, self.sprint))
        return data

    def write(self):
        ws = self.workbook.add_worksheet('Karma')
        ws.set_zoom(80)
        ws.set_column(0, 0, 5)
        ws.set_column(1, 1, 25)
        ws.set_column(2, 2, 25)
        ws.set_column(3, 3, 20)
        ws.set_column(4, 4, 15)
        ws.set_column(5, 10, 10)
        row, col = 0, 0
        columns_merge = 8
        ws.merge_range(xl_range(row, 0, row, columns_merge), "Backlog's Karma Assessment", self.spFormats.chapter_title)
        ws.set_row(0, 40)
        ws.insert_image(0, 8, settings.logoAzul, {'x_scale': 0.9, 'y_scale': 0.9, 'x_offset': -200, 'y_offset': 5})
        #
        row += 1
        ws.write(row, 1, 'Report Date:', self.spFormats.bold_right)
        ws.write(row, 2, datetime.now().strftime('%d-%m-%Y %H:%m'))
        row += 1
        ws.write(row, 1, 'Sprint:', self.spFormats.bold_right)
        ws.write(row, 2, self.sprint)
        row += 1
        ws.write(row, 1, 'Month:', self.spFormats.bold_right)
        ws.write(row, 2, agileCalendar.projectTime)
        row += 2
        ws.merge_range( xl_range(row, 0, row, columns_merge) , 'Chapters', self.spFormats.section)
        row += 1
        ws.write_row(row, 0, ('#','Chapter', 'Leader', 'Sprint Performance', 'Backlog Errors', 'Planning', 'Closing', 'Retrospective', 'Karma', "Assessment"),
                     self.spFormats.column_heading )
        row += 1
        for k,item in enumerate(self.chapters_karma, start=1):
            ws.write(row, 0, k )
            #ws.write(row, 1, '{name}'.format(**item))
            ws.write_url(row, 1, 'http://backlog.fiware.org/chapter/{name}'.format(**item),
                         self.spFormats.lefty_link, item['name'])
            ws.write(row, 2, '{leader}'.format(**item))
            ws.write(row, 3, '{performance:2.1f}%'.format(**item), self.spFormats.center)
            ws.write(row, 4, '{errors:2.1f}%'.format(**item), self.spFormats.center)
            ws.write(row, 5, '{planning}'.format(**item), self.spFormats.center)
            ws.write(row, 6, '{closing}'.format(**item), self.spFormats.center)
            ws.write(row, 7, '{retrospective}'.format(**item), self.spFormats.center)
            ws.write(row, 8, '{karma:1.1f}'.format(**item), self.spFormats.center)
            ws.write(row, 9, '{klabel}'.format(**item))
            row += 1

        row += 2
        ws.merge_range(xl_range(row, 1, row, columns_merge), "Missing = It doesn't exist; Overdue = it isn't resolved yet; Pending = due date ahead; Delayed = Resolved late; ")
        row += 1
        ws.merge_range(xl_range(row, 1, row, columns_merge), "Retrospective refers to the previous sprint in Chapters and to the current sprint in Enablers")
        row += 2
        ws.merge_range( xl_range(row, 0, row, columns_merge) , 'Enablers', self.spFormats.section)
        row += 1
        ws.write_row(row, 0, ('#','Enabler', 'Owner', 'Sprint Performance', 'Backlog Errors', 'Planning', 'Closing', 'Retrospective', 'Karma', "Assessment"),
                     self.spFormats.column_heading )
        row += 1
        for k,item in enumerate([karma for karma in self.enablers_karma if karma.size >= 5], start=1):
            ws.write(row, 0, k)
            #ws.write(row, 1, '{name}'.format(**item))
            ws.write_url(row, 1, 'http://backlog.fiware.org/enabler/{name}/dashboard'.format(**item),
                         self.spFormats.lefty_link, item['name'])
            ws.write(row, 2, '{leader}'.format(**item))
            ws.write(row, 3, '{performance:1.1f}%'.format(**item), self.spFormats.center)
            ws.write(row, 4, '{errors:1.1f}%'.format(**item), self.spFormats.center)
            ws.write(row, 5, '{planning}'.format(**item), self.spFormats.center)
            ws.write(row, 6, '{closing}'.format(**item), self.spFormats.center)
            ws.write(row, 7, '{retrospective}'.format(**item), self.spFormats.center)
            ws.write(row, 8, '{karma:1.1f}'.format(**item), self.spFormats.center)
            ws.write(row, 9, '{klabel}'.format(**item))
            row += 1

        row += 2
        ws.merge_range( xl_range(row, 0, row, columns_merge) , 'Low Activity Enablers', self.spFormats.section)
        row += 1
        ws.write_row(row, 0, ('#','Enabler', 'Owner', 'Sprint Performance (Size)', 'Backlog Errors', 'Planning', 'Closing', 'Retrospective', 'Karma', "Assessment"),
                     self.spFormats.column_heading )
        row += 1
        for k,item in enumerate([karma for karma in self.enablers_karma if karma.size <5 ], start=1):
            ws.write(row, 0, k)
            #ws.write(row, 1, '{name}'.format(**item))
            ws.write_url(row, 1, 'http://backlog.fiware.org/enabler/{name}/dashboard'.format(**item),
                         self.spFormats.lefty_link, item['name'])
            ws.write(row, 2, '{leader}'.format(**item))
            ws.write(row, 3, '{performance:1.1f}% ({size})'.format(**item), self.spFormats.center)
            ws.write(row, 4, '{errors:1.1f}%'.format(**item), self.spFormats.center)
            ws.write(row, 5, '{planning}'.format(**item), self.spFormats.center)
            ws.write(row, 6, '{closing}'.format(**item), self.spFormats.center)
            ws.write(row, 7, '{retrospective}'.format(**item), self.spFormats.center)
            ws.write(row, 8, '{karma:1.1f}'.format(**item), self.spFormats.center)
            ws.write(row, 9, '{klabel}'.format(**item))
            row += 1



def main():
    DataEngine.snapshot(storage=settings.storeHome)
    sprint = agileCalendar.current_sprint
    #sprint = '5.1.2'

    report = KarmaReport(sprint)

    _sprint = re.sub(r'\.', '', sprint)
    _date = datetime.now().strftime("%Y%m%d-%H%M")

    filename = 'FIWARE.backlog.karma.sprint-'+ _sprint + '.' + _date + '.xlsx'
    myfile = os.path.join(settings.outHome, filename)
    report.workbook = xlsxwriter.Workbook(myfile)
    report.spFormats = SpreadsheetFormats(report.workbook)

    report.write()

    print('W:' + myfile)
    report.workbook.close()

if __name__ == "__main__":
    print('Karma Report')
    main()