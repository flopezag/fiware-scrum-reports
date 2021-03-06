import os
import operator
from collections import OrderedDict
from datetime import date, datetime


import xlsxwriter
from xlsxwriter.utility import xl_range

from kernel.Calendar import agileCalendar
from kernel.DataBoard import Data
from kernel.DataFactory import DataEngine
from kernel.NM_Aggregates import Deck, LabDeck, ChapterDeck
from kernel.NM_HelpDeskReporter import DeckReporter, TechChapterReporter, LabChannelReporter
from kernel.Reporter import CoordinationReporter

from kernel.Settings import settings
from kernel.SheetFormats import SpreadsheetFormats
from kernel.UploaderTool import Uploader
from kernel.NodesBook import helpdeskNodesBook
from functools import reduce

__author__ = "Fernando López"

chapters = 'Lab'


class Painter:
    def __init__(self, wb, ws):
        self._wb = wb
        self._ws = ws
        self._column = 10

    def draw_composition(self, data):
        data = {item: data[item] for item in data if data[item]}
        wb, ws = self._wb, self._ws
        chart = wb.add_chart({'type': 'pie'})

        headings = ('Composition', '# Items')
        col = self._column
        ws.write_row(0, col, headings)
        ws.write_column(1, col+0, data)
        ws.write_column(1, col+1, [data[k] for k in data])
        sheet_name = ws.get_name()
        chart.add_series({
                'name': [sheet_name, 0, col],
                'categories': [sheet_name, 1, col, len(data), col],
                'values': [sheet_name, 1, col+1, len(data), col+1],
                'data_labels': {'value': True, 'percentage': True}
        })

        chart.set_title({'name': 'Composition'})
        chart.set_legend({'position': 'top'})
        chart.set_size({'width': 250, 'height': 300, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart

    def draw_status(self, data):
        data = {item: data[item] for item in data if data[item]}
        wb = self._wb
        ws = self._ws
        chart = wb.add_chart({'type': 'bar'})
        headings = ('Status', '#Items')
        col = self._column
        status = ('Closed', 'Answered', 'Impeded', 'In Progress', 'Open')
        ws.write_row(0, col, headings)
        ws.write_column(1, col+0, status)
        value = (lambda x, y: y[x] if x in y else 0)
        ws.write_column(1, col+1, [value(k, data) for k in status])
        sheet_name = ws.get_name()
        chart.add_series({
                'name': [sheet_name, 0, col],
                'categories': [sheet_name, 1, col, len(status), col],
                'values': [sheet_name, 1, col+1, len(status), col+1],
                'data_labels': {'value': True}
        })

        chart.set_title({'name': 'Status'})
        chart.set_legend({'none': True})
        chart.set_x_axis({'name': '# items'})
        chart.set_size({'width': 300, 'height': 300, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart

    def draw_resolution(self, data):
        data = {item: data[item] for item in data if data[item]}
        wb = self._wb
        ws = self._ws
        chart = wb.add_chart({'type': 'bar'})
        headings = ('Resolution', '#Items')

        resolutions = ('Done',
                       'Fixed',
                       'Dismissed',
                       'Incomplete',
                       'Duplicate',
                       'Cannot Reproduce',
                       'New functionality',
                       "Won't Fix")

        col = self._column
        value = (lambda x, y: y[x] if x in y else 0)
        ws.write_row(0, col, headings)
        ws.write_column(1, col+0, resolutions)
        ws.write_column(1, col+1, [value(k, data) for k in resolutions])
        sheet_name = ws.get_name()
        chart.add_series({
                'name': [sheet_name, 0, col],
                'categories': [sheet_name, 1, col, len(resolutions), col],
                'values': [sheet_name, 1, col+1, len(resolutions), col+1],
                'data_labels': {'value': True}
            })

        chart.set_title({'name': 'Resolution'})
        chart.set_x_axis({'name': '# items'})
        chart.set_legend({'none': True})
        chart.set_size({'width': 450, 'height': 300, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart

    def draw_evolution(self, data):
        wb = self._wb
        ws = self._ws

        chart = wb.add_chart({'type': 'line'})
        headings = ('Month', 'Created', 'Resolved', 'Progress')
        col = self._column
        ws.write_row(0, col, headings)

        # print(data['categories'])
        ws.write_column(1, col+0, data['categories'])
        ws.write_column(1, col+1, data['created']['data'])
        ws.write_column(1, col+2, data['resolved']['data'])
        ws.write_column(1, col+3, data['progress']['data'])
        ws.write_column(1, col+4, [0]*(len(data['categories'])))

        sheet_name = ws.get_name()
        chart.add_series({
            'name': [sheet_name, 0, col+1],
            'categories': [sheet_name, 1, col+0, len(data['categories']), col+0],
            'values': [sheet_name, 1, col+1, len(data['created']['data']), col+1],
            'line': {'color': '#008000'}  # created - green
        })

        chart.add_series({
            'name': [sheet_name, 0, col+2],
            'categories': [sheet_name, 1, col+0, len(data['categories']), col+0],
            'values': [sheet_name, 1, col+2, len(data['resolved']['data']), col+2],
            'line': {'color': '#0000FF'}  # resolve - cyan
        })

        cchart = wb.add_chart({'type': 'column'})
        cchart.add_series({
            'name': [sheet_name, 0, col+3],
            'categories': [sheet_name, 1, col+0, len(data['categories']), col+0],
            'values': [sheet_name, 1, col+3, len(data['categories']), col+3],
            # 'values': [sheet_name, 1, col+5, len(data['progress']), col+5],
            'data_labels': {'value': True},
            'fill': {'color': '#FF00FF'}  # resolve - magenta
        })

        chart.combine(cchart)

        chart.set_title({'name': 'Helpdesk Evolution'})
        chart.set_x_axis({'name': '# Month'})
        chart.set_y_axis({'name': '# items'})
        chart.set_legend({'position': 'top'})
        chart.set_size({'width': 1000, 'height': 288, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart

    def draw_resolution_time(self, data):
        wb = self._wb
        ws = self._ws
        chart = wb.add_chart({'type': 'column'})
        headings = ('#days', 'Recent', 'Mature', 'Pending')
        col = self._column
        ws.write_row(0, col, headings)

        ws.write_column(1, col+0, data['categories'])
        ws.write_column(1, col+1, data['recent']['data'])
        ws.write_column(1, col+2, data['time']['data'])
        ws.write_column(1, col+3, data['age']['data'])

        sheet_name = ws.get_name()
        chart.add_series({
            'name': [sheet_name, 0, col+1],
            'categories': [sheet_name, 1, col+0, len(data['categories']), col+0],
            'values': [sheet_name, 1, col+1, len(data['recent']['data']), col+1],
            'fill': {'color': '#008000'}  # recent - green
        })

        chart.add_series({
            'name': [sheet_name, 0, col+2],
            'categories': [sheet_name, 1, col+0, len(data['categories']), col+0],
            'values': [sheet_name, 1, col+2, len(data['time']['data']), col+2],
            'fill': {'color': '#0000FF'}  # mature - blue
        })

        chart.add_series({
            'name': [sheet_name, 0, col+3],
            'categories': [sheet_name, 1, col+0, len(data['categories']), col+0],
            'values': [sheet_name, 1, col+3, len(data['age']['data']), col+3],
            'fill': {'color': '#FF0000'}  # pending - red
        })

        chart.set_title({'name': 'Helpdesk Resolution Time'})
        chart.set_x_axis({'name': '# days'})
        chart.set_y_axis({'name': '# issues'})
        chart.set_legend({'position': 'top'})
        chart.set_size({'width': 1000, 'height': 288, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#CCFFCC'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart

    def draw_enablers_status(self, data):
        wb, ws = self._wb, self._ws
        data = {k: data[k][0] for k in data}
        _data = sorted({k: sum(data[k].values()) for k in data}.items(), key=operator.itemgetter(1), reverse=True)
        _data = OrderedDict([(item[0], data[item[0]]) for item in _data])

        chart = wb.add_chart({'type': 'bar', 'subtype': 'stacked'})
        status = ('Open', 'Answered', 'In Progress', 'Impeded', 'Closed')
        enablers = list(_data.keys())
        headings = ('Enabler',) + status
        col = self._column
        ws.write_row(0, col, headings)
        ws.write_column(1, col+0, enablers)

        for i, _status in enumerate(status, start=1):
            ws.write_column(1, col+i, [_data[enabler][_status] for enabler in _data])

        sheet_name = ws.get_name()

        for i, _status in enumerate(status, start=1):
            chart.add_series({
                'name': [sheet_name, 0, col+i],
                'categories': [sheet_name, 1, col+0, len(enablers), col+0],
                'values': [sheet_name, 1, col+i, len(enablers), col+i],
                'data_labels': {'value': True}
            })

        chart.set_title({'name': "Enablers' Help Desk Status"})
        chart.set_y_axis({'name': 'Enablers'})
        chart.set_x_axis({'name': '# items'})
        chart.set_legend({'position': 'top'})
        chart.set_size({'width': 500, 'height': 1600, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart

    def draw_nodes_contribution(self, data):
        wb, ws = self._wb, self._ws
        nodes = data.keys()

        chart = wb.add_chart({'type': 'bar'})
        headings = ('Nodes', 'Size')
        col = self._column
        ws.write_row(0, col, headings)
        ws.write_column(1, col+0, nodes)
        # ws.write_column(1, col+1, [sum(data[node][0].values()) for node in nodes])
        ws.write_column(1, col+1, [len(data[node]) for node in nodes])

        sheet_name = ws.get_name()

        chart.add_series({
            'name': [sheet_name, 0, col+1],
            'categories': [sheet_name, 1, col+0, len(nodes), col+0],
            'values': [sheet_name, 1, col+1, len(nodes), col+1],
            'data_labels': {'value': True}
        })

        chart.set_title({'name': "Nodes' Help Desk Contribution"})
        chart.set_y_axis({'name': 'Enablers'})
        chart.set_x_axis({'name': '# items'})
        chart.set_legend({'position': 'top'})
        height = 100 + 35 * len(nodes)
        chart.set_size({'width': 500, 'height': height, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart

    @staticmethod
    def calculate_delta_time(a_issue_field):
        resolution_date = a_issue_field['resolutiondate']
        created_date = a_issue_field['created']

        resolution_date = datetime.strptime(resolution_date, '%Y-%m-%dT%H:%M:%S.%f%z')
        created_date = datetime.strptime(created_date, '%Y-%m-%dT%H:%M:%S.%f%z')

        result = (resolution_date - created_date).total_seconds() / 86400

        return result

    def draw_nodes_service_time(self, data):
        wb, ws = self._wb, self._ws
        nodes = data.keys()
        chart = wb.add_chart({'type': 'bar'})
        headings = ('Nodes', 'Overall Mean')
        col = self._column
        ws.write_row(0, col, headings)
        ws.write_column(1, col+0, nodes)

        a = {}
        for node in nodes:
            aux_data = data[node].data
            aux_data = list(map(lambda x: Painter.calculate_delta_time(x['fields']), aux_data))

            if len(aux_data) == 0:
                a[node] = 0
            else:
                a[node] = reduce(lambda x, y: x+y, aux_data) / len(aux_data)

        ws.write_column(1, col+1, [a[node] for node in nodes])

        sheet_name = ws.get_name()

        chart.add_series({
                'name': [sheet_name, 0, col+1],
                'categories': [sheet_name, 1, col+0, len(nodes), col+0],
                'values': [sheet_name, 1, col+1, len(nodes), col+1],
                'data_labels': {'value': True}
            })

        chart.set_title({'name': "Nodes' Help Desk Service Time"})
        chart.set_y_axis({'name': 'Enablers'})
        chart.set_x_axis({'name': '# days'})
        chart.set_legend({'position': 'top'})
        height = 100 + 35 * len(nodes)
        chart.set_size({'width': 500, 'height': height, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#CCFFCC'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart


class HelpDeskLabReporter:

    def __init__(self):
        self.calendar = agileCalendar
        self.workbook = None
        self.spFormats = None

        self.data, self.timestamp, self.source = Data.getHelpDeskLabChannel()
        self.deck = Deck(self.data, self.timestamp, self.source)
        self.start = date(2016, 12, 1)  # year, month, day
        self.end = date(2017, 11, 30)  # year, month, day
        self.reporter = LabChannelReporter(self.deck, start=self.start, end=self.end)
        self.reporter.deck = self.deck

    def _coordination_helpdesk(self, coordination):
        wb = self.workbook
        ws = wb.add_worksheet(coordination.name[1:])
        backlog = self.factory.getCoordinationBacklog(coordination.key)
        backlog.sort(key=backlog.sortDict['name'])

        painter = Painter(wb, ws)
        ws.set_zoom(80)
        ws.set_column(0, 0, 30)
        ws.set_column(1, 1, 122)
        ws.set_column(2, 5, 20)
        row, col = 0, 0
        _heading = self.workbook.add_format({'bold': True, 'font_size': 30,
                                            'bg_color': '#002D67', 'font_color': '#FFE616', 'align': 'center'})

        ws.merge_range(xl_range(row, 0, row, 3), "Coordination Backlog", _heading)
        ws.set_row(0, 42)
        ws.insert_image(0, 0, settings.logofiware, {'x_scale': 0.5, 'y_scale': 0.5, 'x_offset': 0, 'y_offset': 0})

        row += 1
        ws.write(row, 0, 'Project Time:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime()))

        ws.write(row, 2, 'Report Date:', self.spFormats.bold_right)
        ws.write(row, 3, date.today().strftime('%d-%m-%Y'))

        row += 1
        ws.write(row, 0, 'Start of Data Analysis:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime(current_date=self.start)))

        row += 1
        ws.write(row, 0, 'End of Data Analysis:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime(current_date=self.end)))

        row += 2
        _format = self.workbook.add_format({'bold': True, 'font_size': 15, 'bg_color': '#60C1CF'})
        ws.write(row, 0, 'Backlog Owner:', self.spFormats.bold_right)
        ws.write(row, 1, coordination.leader, _format)
        ws.write(row, 2, '', _format)

        row += 2
        ws.write(row, 0, 'Backlog Summary:', self.spFormats.bold_right)
        ws.write(row, 1, '# Items', self.spFormats.bold_left)

        row += 1
        reporter = CoordinationReporter(coordination.project, backlog)
        data = reporter.issueType
        ws.write(row, 0, 'Composition', self.spFormats.bold_right)
        ws.write(row, 1, '{0} Issues = {Epic} Epics + {Feature} Features + '
                         '{Story} User Stories + {WorkItem} WorkItems + {Bug} Bugs'.format(sum(data.values()), **data))

        row += 1
        data = reporter.perspective
        ws.write(row, 0, 'Status', self.spFormats.bold_right)
        ws.write(row, 1, '{0} Issues = {Implemented} Implemented  + {Working On} Working On  + '
                         ' {Foreseen} Foreseen'.format(sum(data.values()), **data))

        row += 1
        data = reporter.sprint_status
        ws.write(row, 0, 'Sprint Status', self.spFormats.red_bold_right)
        ws.write_string(row, 1, '{} Issues = {}'.format(sum(data.values()),
                                                        ' + '.join("{!s} {}".format(v, k) for (k, v) in data.items())))

        row += 1
        ws.write(row, 0, 'Tests', self.spFormats.bold_right)
        data = reporter.backlog.testMetrics
        total = sum(data['OK'].values()) + sum(data['KO'].values())
        ws.write_rich_string(row, 1,
                             '{0:,} Tests = {1:,}'.format(total, sum(data['OK'].values())),
                             self.spFormats.green, ' OK', ' + ',
                             '{0:,}'.format(sum(data['KO'].values())), self.spFormats.red, ' KO ')

        row += 1
        data = reporter.errors
        ws.write(row, 0, 'Errors', self.spFormats.bold_right)
        ws.write_rich_string(row, 1,
                             '{:,} Issues = {OK:,}'.format(sum(data.values()), **data),
                             self.spFormats.green,
                             ' OK',
                             ' + '
                             ' {KO:,}'.format(sum(data.values()), **data), self.spFormats.red, ' KO')

        row += 2
        chart = painter.draw_composition(reporter.issueType)
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        chart = painter.draw_status(reporter.perspective)
        ws.insert_chart(row, 1, chart, {'x_offset': 300, 'y_offset': 0})

        chart = painter.draw_errors(reporter.errors)
        ws.insert_chart(row, 1, chart, {'x_offset': 712, 'y_offset': 0})

        row += 15
        chart = painter.draw_sprint_burndown(reporter.burndown)
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        chart = painter.draw_sprint_status(reporter.sprint_status)
        ws.insert_chart(row, 1, chart, {'x_offset': 712, 'y_offset': 0})

        row += 15
        chart = painter.draw_evolution(reporter.implemented)
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        row += 15
        _format = self.workbook.add_format({'bold': True, 'font_size': 20, 'bg_color': '#60C1CF', 'align': 'center'})
        ws.merge_range(xl_range(row, 0, row, 4), 'Backlog Entries', _format)
        row += 1

        ws.write_row(row, 0,
                     ('Item Id', 'Item reference', 'Time frame', 'Status', 'Item type'),
                     self.spFormats.column_heading)

        for issue in backlog:
            row += 1
            self._write_issue(ws, row, issue)

    @staticmethod
    def _write_stats(ws, row, data):
        if data['n'] == 0:
            ws.write(row, 1, 'n={n}'.format(**data))
        elif data['n'] > 1:
            ws.write(row, 1,
                     'n={n}; min={min} days; max={max} days; mean={mean:.0f} days; median={median:.0f} days; '
                     'std dev={stdev:.0f} days; variance={variance:.0f} days'.format(**data))
        else:
            ws.write(row, 1,
                     'n={n}; min={min} days; max={max} days; mean={mean:.0f} days; median={median:.0f} days;'
                     .format(**data))

    def _node_helpdesk(self, node):
        print('--------->', node.name)
        wb = self.workbook
        ws = wb.add_worksheet(node.name)
        deck = LabDeck(node, self.data, self.timestamp, self.source)
        # reporter = self.reporter

        painter = Painter(wb, ws)
        ws.set_zoom(80)
        ws.set_column(0, 0, 20)
        ws.set_column(1, 1, 20)
        ws.set_column(2, 2, 122)
        ws.set_column(3, 5, 25)
        row, col = 0, 0

        _heading = self.workbook.add_format({'bold': True, 'font_size': 30,
                                            'bg_color': '#002D67', 'font_color': '#FFE616', 'align': 'center'})

        ws.merge_range(xl_range(row, 0, row, 4),
                       "Help Desk for Node: '{0}'".format(node.name), _heading)

        ws.set_row(0, 42)
        ws.insert_image(0, 0, settings.logofiware, {'x_scale': 0.5, 'y_scale': 0.5, 'x_offset': 0, 'y_offset': 0})

        row += 1
        ws.write(row, 0, 'Project Time:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime()))

        ws.write(row, 3, 'Report Date:', self.spFormats.bold_right)
        ws.write(row, 4, date.today().strftime('%d-%m-%Y'))

        row += 1
        ws.write(row, 0, 'Start of Data Analysis:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime(current_date=self.start)))

        row += 1
        ws.write(row, 0, 'End of Data Analysis:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime(current_date=self.end)))

        row += 2
        _format = self.workbook.add_format({'bold': True, 'font_size': 15, 'color': 'green'})
        ws.write(row, 0, 'Node:', self.spFormats.bold_right)
        ws.write(row, 1, node.name, _format)

        row += 1
        ws.write(row, 0, 'Work Mode:', self.spFormats.bold_right)
        try:
            ws.write(row, 1, deck.node.mode)
        except Exception:
            # there is no data about the node, therefore we consider the node Inactive
            ws.write(row, 1, 'Inactive')

        row += 2
        ws.write(row, 0, 'HelpDesk Summary:', self.spFormats.bold_right)
        ws.write(row, 1, '# Items', self.spFormats.bold_left)

        row += 1
        reporter = DeckReporter(node.name, deck, start=self.start, end=self.end)
        reporter.deck = deck
        ws.write(row, 0, 'Composition', self.spFormats.bold_right)
        ws.write(row, 1, '{} Issues = {} extRequests + {} Monitors'
                 .format(len(deck), deck.issueType['extRequest'], deck.issueType['Monitor']))

        row += 1
        ws.write(row, 0, 'Status', self.spFormats.bold_right)
        ws.write(row, 1, '{} Issues = {} Open + {} In Progress + {} Impeded + {} Answered + {} Closed'
                 .format(len(deck),
                         deck.status['Open'],
                         deck.status['In Progress'],
                         deck.status['Impeded'],
                         deck.status['Answered'],
                         deck.status['Closed']
                         )
                 )

        if len(reporter.deck):
            row += 2
            chart = painter.draw_composition(reporter.deck.issueType)
            ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

            chart = painter.draw_status(reporter.deck.status)
            ws.insert_chart(row, 1, chart, {'x_offset': 250, 'y_offset': 0})

            chart = painter.draw_resolution(reporter.deck.resolution)
            ws.insert_chart(row, 1, chart, {'x_offset': 550, 'y_offset': 0})

            row += 15

        row += 2
        ws.write(row, 0, 'HelpDesk Set:', self.spFormats.bold_right)
        ws.write(row, 1, 'Statistics', self.spFormats.bold_left)

        row += 1
        ws.write(row, 0, 'All:', self.spFormats.bold_right)
        self._write_stats(ws, row, reporter.stats)

        if reporter.stats['n'] > 0:
            row += 1
            ws.write(row, 0, 'Pending Issues:', self.spFormats.bold_right)
            self._write_stats(ws, row, reporter.statsOfPending)

        if len(reporter.deck):
            row += 1
            chart = painter.draw_resolution_time(reporter.resolutionTime_graph_data)
            ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

            row += 15
            chart = painter.draw_evolution(reporter.evolution_graph_data)
            ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

            row += 15

        row += 1
        _format = self.workbook.add_format({'bold': True, 'font_size': 16, 'bg_color': '#009999'})

        row += 1
        _format = self.workbook.add_format({'bold': True, 'font_size': 20, 'bg_color': '#3399FF', 'align': 'center'})
        ws.merge_range(xl_range(row, 0, row, 4), 'Help Desk Entries', _format)
        ws.write(row+1, 1, 'No entries found for this enabler in the Tech channel of the Help Desk')

        _center = self.workbook.add_format({'align': 'center'})

        if len(reporter.deck.unresolved):
            row += 1
            _format = self.workbook.add_format({'bold': True,
                                                'font_size': 20,
                                                'bg_color': '#CCFFE5',
                                                'align': 'center'})

            ws.merge_range(xl_range(row, 0, row, 4), 'Unresolved Issues', _format)
            row += 1
            ws.write_row(row, 0,
                         ('Item Id', 'Channel', 'Summary', 'Status', 'Age (#days)'), self.spFormats.column_heading)

            for issue in reporter.deck.unresolved:
                row += 1
                ws.write_url(row, 0, issue.url, self.spFormats.link, issue.key)
                ws.write(row, 1, issue.channel.name)
                ws.write(row, 2, issue.name)
                ws.write(row, 3, issue.status)
                ws.write(row, 4, issue.age, _center)
            else:
                ws.write(row+1, 0, '>>>>> {} issues found'.format(len(reporter.deck.unresolved)))
            row += 1

        if len(reporter.deck.resolved):
            row += 1
            _format = self.workbook.add_format({'bold': True,
                                                'font_size': 20,
                                                'bg_color': '#CCFFE5',
                                                'align': 'center'})

            ws.merge_range(xl_range(row, 0, row, 4), 'Resolved Issues', _format)
            row += 1
            ws.write_row(row, 0,
                         ('Resolution Date', 'Item Id', 'Summary', 'Status-Resolution', 'Age (#days)'),
                         self.spFormats.column_heading)

            for issue in reporter.deck.resolved:
                row += 1
                ws.write(row, 0, issue.resolutionDate, self.spFormats.date)
                ws.write_url(row, 1, issue.url, self.spFormats.link, issue.key)
                ws.write(row, 2, issue.name)
                ws.write(row, 3, '{0} - {1}'.format(issue.status, issue.resolution))
                ws.write(row, 4, issue.age, _center)
            else:
                ws.write(row+1, 0, '>>>>> {} issues found'.format(len(reporter.deck.resolved)))

    def _chapter_helpdesk(self, chapter):
        print('------>', chapter.name)
        wb = self.workbook
        ws = wb.add_worksheet('{} Chapter'.format(chapter.name))
        deck = ChapterDeck(chapter, *Data.getChapterHelpDesk(chapter.name))
        reporter = TechChapterReporter(chapter, deck, start=self.start, end=self.end)
        painter = Painter(wb, ws)
        ws.set_zoom(80)
        ws.set_column(0, 0, 30)
        ws.set_column(1, 1, 122)
        ws.set_column(2, 5, 20)
        row, col = 0, 0

        _heading = self.workbook.add_format({'bold': True, 'font_size': 30,
                                            'bg_color': '#002D67', 'font_color': '#FFE616', 'align': 'center'})

        ws.merge_range(xl_range(row, 0, row, 3),
                       "Help Desk for Chapter: '{0}'".format(chapter.name), _heading)

        ws.set_row(0, 42)
        ws.insert_image(0, 0, settings.logofiware, {'x_scale': 0.5, 'y_scale': 0.5, 'x_offset': 0, 'y_offset': 0})

        row += 1
        ws.write(row, 0, 'Project Time:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime()))

        ws.write(row, 2, 'Report Date:', self.spFormats.bold_right)
        ws.write(row, 3, date.today().strftime('%d-%m-%Y'))

        row += 1
        ws.write(row, 0, 'Start of Data Analysis:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime(current_date=self.start)))

        row += 1
        ws.write(row, 0, 'End of Data Analysis:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime(current_date=self.end)))

        row += 2
        _format = self.workbook.add_format({'bold': True, 'font_size': 15, 'color': 'green'})
        ws.write(row, 0, 'Chapter Name:', self.spFormats.bold_right)
        ws.write(row, 1, chapter.Name, _format)
        row += 1
        _format = self.workbook.add_format({'bold': True, 'font_size': 15, 'bg_color': '#60C1CF'})
        ws.write(row, 0, 'Chapter Leader:', self.spFormats.bold_right)
        ws.write(row, 1, chapter.leader, _format)
        ws.write(row, 2, '', _format)
        if chapter.architect:
            row += 1
            ws.write(row, 0, 'Chapter Architect:', self.spFormats.bold_right)
            ws.write(row, 1, chapter.architect, _format)
            ws.write(row, 2, '', _format)
        row += 2

        ws.write(row, 0, 'HelpDesk Summary:', self.spFormats.bold_right)
        ws.write(row, 1, '# Items', self.spFormats.bold_left)

        row += 1
        data = deck.issueType
        ws.write(row, 0, 'Composition', self.spFormats.bold_right)
        ws.write(row, 1, '{0:,} Issues = {extRequest} extRequests + '
                         '{Monitor:,} Monitors'.format(sum(data.values()), **data))

        row += 1
        data = deck.status
        ws.write(row, 0, 'Status', self.spFormats.bold_right)
        ws.write(row, 1,
                 '{0:,} Issues = {Open} Open + {In Progress} In Progress + {Impeded} Impeded + {Answered} Answered +'
                 ' {Closed} Closed'.format(sum(data.values()), **data))

        row += 1
        data = deck.resolution
        ws.write(row, 0, 'Resolved', self.spFormats.bold_right)
        fields = ' + '.join(['{' + '{0}'.format(item) + '} ' + '{0}'.format(item) for item in data])
        ws.write(row, 1, '{0:,} Issues = '.format(sum(data.values())) + fields.format(**data))

        if len(deck):
            row += 2
            chart = painter.draw_composition(deck.issueType)
            ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

            chart = painter.draw_status(deck.status)
            ws.insert_chart(row, 1, chart, {'x_offset': 250, 'y_offset': 0})

            chart = painter.draw_resolution(deck.resolution)
            ws.insert_chart(row, 1, chart, {'x_offset': 550, 'y_offset': 0})

            row += 17
        ws.write(row, 0, 'HelpDesk Set:', self.spFormats.bold_right)
        ws.write(row, 1, 'Statistics', self.spFormats.bold_left)

        row += 1
        ws.write(row, 0, 'All:', self.spFormats.bold_right)
        self._write_stats(ws, row, reporter.stats)

        if reporter.stats['n'] > 0:
            row += 1
            ws.write(row, 0, 'Last 60 days:', self.spFormats.bold_right)
            self._write_stats(ws, row, reporter.statsOfRecent)

            row += 1
            ws.write(row, 0, 'Pending Issues:', self.spFormats.bold_right)
            self._write_stats(ws, row, reporter.statsOfPending)
        if len(deck):
            row += 1
            chart = painter.draw_resolution_time(reporter.resolutionTime_graph_data)
            ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

            row += 15
            chart = painter.draw_evolution(reporter.evolution_graph_data)
            ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

            row += 15
        row += 1
        _format = self.workbook.add_format({'bold': True, 'font_size': 16, 'bg_color': '#009999'})

        row += 1
        ws.merge_range(xl_range(row, 1, row, 2), 'Enablers Contribution and Service Time', _format)

        row += 1
        chart = painter.draw_enablers_contribution(reporter.enablers)
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        chart = painter.draw_enablers_service_time(reporter.enablers)
        ws.insert_chart(row, 1, chart, {'x_offset': 500, 'y_offset': 0})

    def _lab_channel_help_desk(self):
        print('---> Lab Nodes')
        wb = self.workbook
        ws = wb.add_worksheet('Lab Channel')
        deck = self.deck
        reporter = self.reporter

        painter = Painter(wb, ws)
        ws.set_zoom(80)
        ws.set_column(0, 0, 30)
        ws.set_column(1, 1, 122)
        ws.set_column(2, 5, 20)
        row, col = 0, 0

        _heading = self.workbook.add_format({'bold': True, 'font_size': 30,
                                             'bg_color': '#002D67',
                                             'font_color': '#FFE616',
                                             'align': 'center'})

        ws.merge_range(xl_range(row, 0, row, 3),
                       "Help Desk for Technical Chapters", _heading)

        ws.set_row(0, 42)
        ws.insert_image(0, 0, settings.logofiware, {'x_scale': 0.5, 'y_scale': 0.5, 'x_offset': 0, 'y_offset': 0})

        row += 1
        ws.write(row, 0, 'Project Time:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime()))

        ws.write(row, 2, 'Report Date:', self.spFormats.bold_right)
        ws.write(row, 3, date.today().strftime('%d-%m-%Y'))

        row += 1
        ws.write(row, 0, 'Start of Data Analysis:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime(current_date=self.start)))

        row += 1
        ws.write(row, 0, 'End of Data Analysis:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime(current_date=self.end)))

        row += 2
        _format = self.workbook.add_format({'bold': True, 'font_size': 15, 'bg_color': '#60C1CF'})
        ws.write(row, 0, 'Tech Channel Leader:', self.spFormats.bold_right)
        ws.write(row, 1, 'FF - Veronika Vlnkova', _format)
        ws.write(row, 2, '', _format)

        row += 2
        ws.write(row, 0, 'Tech Channel Summary', self.spFormats.bold_right)
        ws.write(row, 1, '# Items', self.spFormats.bold_left)

        row += 1
        reporter.deck = deck
        data = reporter.deck.issueType
        ws.write(row, 0, 'Composition', self.spFormats.bold_right)
        ws.write(row, 1, '{0:,} Issues = {extRequest} extRequests + '
                         '{Monitor:,} Monitors'.format(sum(data.values()), **data))

        row += 1
        data = reporter.deck.status
        ws.write(row, 0, 'Status', self.spFormats.bold_right)
        ws.write(row, 1,
                 '{0:,} Issues = {Open} Open + {In Progress} In Progress + {Impeded} Impeded + {Answered} Answered +'
                 ' {Closed} Closed'.format(sum(data.values()), **data))

        row += 1
        data = reporter.deck.resolution
        ws.write(row, 0, 'Resolved', self.spFormats.bold_right)
        fields = ' + '.join(['{' + '{0}'.format(item) + '} ' + '{0}'.format(item) for item in data])
        ws.write(row, 1, '{0:,} Issues = '.format(sum(data.values())) + fields.format(**data))

        if len(reporter.deck):
            row += 2
            chart = painter.draw_composition(reporter.deck.issueType)
            ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

            chart = painter.draw_status(reporter.deck.status)
            ws.insert_chart(row, 1, chart, {'x_offset': 250, 'y_offset': 0})

            chart = painter.draw_resolution(reporter.deck.resolution)
            ws.insert_chart(row, 1, chart, {'x_offset': 550, 'y_offset': 0})

            row += 17

        ws.write(row, 0, 'Channel Set:', self.spFormats.bold_right)
        ws.write(row, 1, 'Statistics', self.spFormats.bold_left)

        row += 1
        ws.write(row, 0, 'All:', self.spFormats.bold_right)
        self._write_stats(ws, row, reporter.stats)

        if reporter.stats['n'] > 0:
            row += 1
            ws.write(row, 0, 'Pending Issues:', self.spFormats.bold_right)
            self._write_stats(ws, row, reporter.statsOfPending)

        if len(reporter.deck):
            row += 1
            chart = painter.draw_resolution_time(reporter.resolutionTime_graph_data)
            ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

            row += 15
            chart = painter.draw_evolution(reporter.evolution_graph_data)
            ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

            row += 15

        row += 1
        _format = self.workbook.add_format({'bold': True, 'font_size': 13, 'bg_color': '#D0E799'})
        ws.merge_range(xl_range(row, 1, row, 2), 'Nodes Contribution and Service Time', _format)

        row += 1
        chart = painter.draw_nodes_contribution(reporter.nodes)
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        chart = painter.draw_nodes_service_time(reporter.nodes)
        ws.insert_chart(row, 1, chart, {'x_offset': 500, 'y_offset': 0})

    def lab(self):
        print("\n--monitor-- Help-Desk Lab nodes:")

        _date = datetime.now().strftime("%Y%m%d-%H%M")
        filename = 'FIWARE.helpdesk-lab.report.' + _date + '.xlsx'
        myfile = os.path.join(settings.outHome, filename)

        self.workbook = xlsxwriter.Workbook(myfile)
        self.spFormats = SpreadsheetFormats(self.workbook)
        self._lab_channel_help_desk()

        nodes = helpdeskNodesBook

        for node in nodes:
            self._node_helpdesk(helpdeskNodesBook[node])

        print('Help-Desk Lab nodes report: W:' + myfile)
        self.workbook.close()


class WorkBench:
    @staticmethod
    def report():
        print('report')
        reporter = HelpDeskLabReporter()

        reporter.lab()

    @staticmethod
    def snapshot():
        print('snapshot')
        DataEngine.snapshot(storage=settings.storeHome)

    @staticmethod
    def upload():
        print('upload')
        uploader = Uploader()
        uploader.upload('helpdesklab', 'report', settings.chapters)


if __name__ == "__main__":
    options = {'0': WorkBench.snapshot,
               '1': WorkBench.report,
               '2': WorkBench.upload,
               'E': exit}

    while True:
        menu = '\nMenu:\n\t0: get snapshot\n\t1: create reports \n\t2: upload report\n\tE: Exit'
        choice = input(menu + '\nEnter your choice[0-2,(E)xit] : ')

        print('\nChosen option: {}\n'.format(choice))

        if choice in ('0', '1', '2', 'E'):
            options[choice]()
        else:
            print('\n\n\nWrong option, please try again... ')

# TODO: the period of time should be a parameter to put on the initialization
#       of the scripts and the code should work with or without these data.
