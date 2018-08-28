import statistics
from calendar import monthrange
from itertools import accumulate
from datetime import date

from collections import Counter, OrderedDict
from kernel.Calendar import calendar as FWcalendar
from kernel.TrackerBook import helpdeskBookByName, chaptersBook
from kernel.ComponentsBook import enablersBook, enablersBookByName

from kernel.Recorder import Recorder
from kernel.DataBoard import Data

from kernel.NM_Aggregates import ChannelDeck, InnChannel, EnablerDeck, ChapterDeck

__author__ = 'Manuel Escriche'


class DeckReporter:
    def __init__(self, chaptername, deck):
        self.chaptername = chaptername
        self.timestamp = deck.timestamp
        self.stats = self._stats(deck)
        self.statsOfPending = self._statsOfPending(deck)
        self.statsOfRecent = self._statsOfRecent(deck)
        self.statsOfVeryRecent = self._statsOfVeryRecent(deck)
        self.achievement_graph_data = self._achievement_graph_data(deck)
        self.evolution_graph_data = self._evolution_graph_data(deck)
        self.resolutionTime_graph_data = self._resolutionTime_graph_data(deck)
        self.monthly_evolution_graph_data = self._monthly_evolution_graph_data(deck)
        self.monthly_resolutionTime_graph_data = self._monthly_resolutionTime_graph_data(deck)
        self._len = len(deck)

    def _stats(self, deck):
        # count = Counter([issue.age for issue in self.issues])
        data = [issue.age for issue in deck]
        outdata = dict()
        outdata['n'] = len(data)
        try:
            outdata['min'] = min(data)
        except:
            pass

        try:
            outdata['max'] = max(data)
        except:
            pass

        try:
            outdata['mean'] = statistics.mean(data)
        except:
            outdata['mean'] = None

        try:
            outdata['median'] = statistics.median(data)
        except:
            pass

        try:
            outdata['mode'] = statistics.mode(data)
        except:
            pass

        try:
            outdata['stdev'] = statistics.stdev(data)
        except:
            pass

        try:
            outdata['variance'] = statistics.variance(data)
        except:
            pass

        return outdata

    def _statsOfPending(self, deck):
        # count = Counter([issue.age for issue in self.issues])
        data = [issue.age for issue in deck if not issue.resolved]
        outdata = dict()
        outdata['n'] = len(data)
        try:
            outdata['min'] = min(data)
        except:
            pass

        try:
            outdata['max'] = max(data)
        except:
            pass

        try:
            outdata['mean'] = statistics.mean(data)
        except:
            outdata['mean'] = None

        try:
            outdata['median'] = statistics.median(data)
        except:
            pass

        try:
            outdata['mode'] = statistics.mode(data)
        except:
            pass

        try:
            outdata['stdev'] = statistics.stdev(data)
        except:
            pass

        try:
            outdata['variance'] = statistics.variance(data)
        except:
            pass

        return outdata

    def _statsOfRecent(self, deck):
        # count = Counter([issue.age for issue in self.issues])
        data = [issue.age for issue in deck if (date.today() - issue.created).days <= 60]
        outdata = dict()
        outdata['n'] = len(data)
        try:
            outdata['min'] = min(data)
        except:
            pass

        try:
            outdata['max'] = max(data)
        except:
            pass

        try:
            outdata['mean'] = statistics.mean(data)
        except:
            outdata['mean'] = None

        try:
            outdata['median'] = statistics.median(data)
        except:
            pass

        try:
            outdata['mode'] = statistics.mode(data)
        except:
            pass

        try:
            outdata['stdev'] = statistics.stdev(data)
        except:
            pass

        try:
            outdata['variance'] = statistics.variance(data)
        except:
            pass

        return outdata

    def _statsOfVeryRecent(self, deck):
        # count = Counter([issue.age for issue in self.issues])
        resolved = [issue for issue in deck if issue.resolved]
        data = [issue.age for issue in resolved if (date.today() - issue.resolutionDate).days <= 30]
        outdata = dict()
        outdata['n'] = len(data)
        try:
            outdata['min'] = min(data)
        except:
            pass

        try:
            outdata['max'] = max(data)
        except:
            pass

        try:
            outdata['mean'] = statistics.mean(data)
        except:
            outdata['mean'] = None

        try:
            outdata['median'] = statistics.median(data)
        except:
            pass

        try:
            outdata['mode'] = statistics.mode(data)
        except:
            pass

        try:
            outdata['stdev'] = statistics.stdev(data)
        except:
            pass

        try:
            outdata['variance'] = statistics.variance(data)
        except:
            pass

        return outdata

    def _achievement_graph_data(self, deck):
        color = {'Resolved':'#bada55', 'Pending':'#ff4040'}
        value = {True: 'Resolved', False: 'Pending'}
        count = Counter([value[issue.resolved != None] for issue in deck])
        return [{'name':_type, 'y': count[_type], 'color': color[_type]} for _type in count]

    def _evolution_graph_data(self, deck):
        book = FWcalendar.monthBook

        createdIssues = Counter(['{:02d}-{}'.format(issue.created.month, issue.created.year) for issue in deck])
        createdData = list(accumulate([createdIssues[book[month]] for month in FWcalendar.pastMonths]))

        issues = [issue for issue in deck if issue.resolved]
        resolvedIssues = Counter(['{:02d}-{}'.format(issue.resolutionDate.month, issue.resolutionDate.year) for issue in issues])
        progressData = [resolvedIssues[book[month]] for month in FWcalendar.pastMonths]
        resolvedData = list(accumulate(progressData))

        outdata = dict()
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
        outdata['progress'] = dict()
        outdata['progress']['type'] = 'column'
        outdata['progress']['name'] = 'Progress'
        outdata['progress']['data'] = progressData
        outdata['summary'] = dict()
        outdata['summary']['type'] = 'pie'
        outdata['summary']['name'] = 'Status'
        outdata['summary']['data'] = [{'name': 'Resolved', 'y': resolvedData[-1], 'color': 'Highcharts.getOptions().colors[1]' },
                                      {'name': 'Pending', 'y': createdData[-1] - resolvedData[-1], 'color': '#ff4040'}]
        outdata['summary']['center'] = [70, 60]
        outdata['summary']['size'] = 80
        outdata['summary']['dataLabels'] = {'enabled': 'true',
                                            'format': '<b>{point.name}</b>: <br/> {point.y} ({point.percentage:.1f}%)'}

        return outdata

    def _resolutionTime_graph_data(self, deck):
        count = Counter([issue.age for issue in deck])
        if not count:
            return dict()

        pending_count = Counter([issue.age for issue in deck if not issue.resolved ])

        _min,_max = min(count.keys()), max(count.keys())
        data = [count[k] for k in range(_min,_max+1)]

        pending_data = [pending_count[k] for k in range(_min,_max+1)]

        recent_count = Counter([issue.age for issue in deck if (date.today() - issue.created).days <= 60 ])
        recent_data = [recent_count[k] for k in range(_min,_max+1)]

        outdata = dict()
        outdata['categories'] = [k for k in range(_min,_max+1)]
        outdata['time'] = dict()
        outdata['time']['type'] = 'column'
        outdata['time']['name'] = 'Mature issues'
        outdata['time']['data'] = data
        outdata['age'] = dict()
        outdata['age']['type'] = 'column'
        outdata['age']['name'] = "Pending issues"
        outdata['age']['color'] = '#ff4040'
        outdata['age']['data'] = pending_data
        outdata['recent'] = dict()
        outdata['recent']['type'] = 'column'
        outdata['recent']['name'] = "Recent issues"
        outdata['recent']['color'] = 'green'
        outdata['recent']['data'] = recent_data
        return outdata

    def _monthly_evolution_graph_data(self, deck):
        month_length = monthrange(date.today().year, date.today().month)[1]
        month, year = FWcalendar.monthBook[FWcalendar.currentMonth[1]].split('-')
        createdIssues = Counter([issue.created.day for issue in deck
                                 if issue.created.month == int(month) and issue.created.year == int(year)])
        createdData = list(accumulate([createdIssues[day] for day in range(1, date.today().day+1)]))

        resolvedIssues = Counter([issue.resolutionDate.day for issue in deck
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

    def _monthly_resolutionTime_graph_data(self, deck):
        month_length = monthrange(date.today().year, date.today().month)[1]
        month, year = FWcalendar.monthBook[FWcalendar.currentMonth[1]].split('-')
        issues_set = [issue for issue in deck
                                 if (issue.resolved and
                                     issue.resolutionDate.month == int(month) and
                                     issue.resolutionDate.year == int(year)) or
                                 not issue.resolved]

        count = Counter([issue.age for issue in issues_set])

        if not count:
            return dict()

        _min,_max = min(count.keys()), max(count.keys())

        pending_count = Counter([issue.age for issue in issues_set if not issue.resolved ])
        pending_data = [pending_count[k] for k in range(_min,_max+1)]

        data_count = Counter([issue.age for issue in issues_set if issue.resolved])
        data = [data_count[k] for k in range(_min,_max+1)]

        outdata = dict()
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

    def __len__(self):
        return self._len


class ChannelReporter(DeckReporter, Recorder):
    def __init__(self, channel, deck):
        self.channel = channel
        # DeckReporter.__init__(self, deck)
        DeckReporter.__init__(self, channel.name, deck)
        Recorder.__init__(self, 'FIWARE.ChannelReporter.' + channel.name + '.pkl')
        self.save()

    @classmethod
    def fromFile(cls, channel):
        return super().fromFile('FIWARE.ChannelReporter.' + channel.name + '.pkl')


class TechChapterReporter(DeckReporter):
    def __init__(self, chapter, deck):
        # super().__init__(deck)
        super().__init__(chapter, deck)
        self.enablers = self._enablers(chapter, deck)

    def _enablers(self, chapter, deck):
        data = dict()
        for enabler in chapter.enablers:
            _deck = EnablerDeck(enablersBook[enabler], deck.data, deck.timestamp, deck.source)
            # reporter = DeckReporter(_deck)
            reporter = DeckReporter(chapter.name, _deck)
            data[enabler] = (_deck.status, reporter.stats, reporter.statsOfRecent, reporter.statsOfVeryRecent)
        return data


class TechChannelReporter(ChannelReporter):
    __chapters = ('Apps', 'Cloud', 'Data', 'IoT', 'I2ND', 'Security', 'WebUI')

    def __init__(self, deck):
        channel = helpdeskBookByName['Main-Help-Desk'].channels['Tech']
        super().__init__(channel, deck)
        self.chapters = self._chapters(deck)
        self.enablers = self._enablers(deck)
        self.save()

    def _chapters(self, deck):
        data = OrderedDict()
        for chapter in ('Apps', 'Cloud', 'Data', 'IoT', 'I2ND', 'Security', 'WebUI'):
            _deck = ChapterDeck(chaptersBook[chapter], deck.data, deck.timestamp, deck.source)
            reporter = TechChapterReporter(chaptersBook[chapter], _deck)
            data[chapter] = (len(_deck), reporter.stats, reporter.statsOfRecent, reporter.statsOfVeryRecent)
        return data

    def _enablers(self, deck):
        data = dict()
        for enabler in enablersBookByName:
            if enablersBookByName[enabler].chapter not in self.__chapters: continue
            _deck = EnablerDeck(enablersBookByName[enabler], deck.data, deck.timestamp, deck.source)
            # reporter = DeckReporter(_deck)
            reporter = DeckReporter(enablersBookByName[enabler].chapter, _deck)
            data[enabler] = (_deck.status, reporter.stats, reporter.statsOfRecent, reporter.statsOfVeryRecent)
        return data


class DeskReporter(DeckReporter, Recorder):
    def __init__(self, desk, deck):
        self.desk = desk
        DeckReporter.__init__(self, deck)
        Recorder.__init__(self,'FIWARE.DeskReporter.' + desk.name + '.pkl')
        value = lambda x: x if x else 'null'
        reporters = dict()
        for channelname in desk.channels:
            channel = helpdeskBookByName[desk.name].channels[channelname]
            data, timestamp, source = Data.getChannel(channel.key)
            channeldeck = InnChannel(data, timestamp, source) \
                if desk.name == 'ToolsSupport-Help-Desk' else ChannelDeck(channel, data, timestamp, source)
            reporters[channelname] = ChannelReporter(channel, channeldeck)

        self._composition_data = dict()
        self._composition_data['categories'] = [channel for channel in desk.channels]
        self._composition_data['all'] = [[channel, len(reporters[channel])] for channel in desk.channels]
        self._composition_data['veryrecent'] = [reporters[channel].statsOfVeryRecent['n'] for channel in desk.channels]
        self._composition_data['pending'] = [reporters[channel].statsOfPending['n'] for channel in desk.channels]
        self._composition_data['vveryrecent'] = [[channel, reporters[channel].statsOfVeryRecent['n']] for channel in desk.channels]
        self._composition_data['ppending'] = [[channel, reporters[channel].statsOfPending['n']] for channel in desk.channels]


        self._behaviour_data = dict()
        self._behaviour_data['categories'] = [channel for channel in desk.channels]
        self._behaviour_data['all'] = [value(reporters[channel].stats['mean']) for channel in desk.channels]
        self._behaviour_data['recent'] = [value(reporters[channel].statsOfRecent['mean']) for channel in desk.channels]
        self._behaviour_data['veryrecent'] = [value(reporters[channel].statsOfVeryRecent['mean']) for channel in desk.channels]
        self._behaviour_data['pending'] = [value(reporters[channel].statsOfPending['mean']) for channel in desk.channels]

        self.save()

    @property
    def composition_graph(self):
        return self._composition_data
    @property
    def behaviour_graph(self):
        return self._behaviour_data

    @classmethod
    def fromFile(cls, desk):
        return super().fromFile('FIWARE.DeskReporter.' + desk.name + '.pkl')


if __name__ == "__main__":
    pass
