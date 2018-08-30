#!/usr/bin/env python
# -*- encoding: utf-8 -*-
##
# Copyright 2018 FIWARE Foundation, e.V.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

__author__ = "Fernando López"

import os
from datetime import date, datetime

import xlsxwriter
from xlsxwriter.utility import xl_range

from kernel.Reporter import ChapterReporter, EnablerReporter, CoordinationReporter, \
    ChaptersReporter, ToolReporter, LabReporter

from kernel.Calendar import agileCalendar
from kernel.TrackerBook import chaptersBook
from kernel.DataFactory import DataEngine
from kernel.NodesBook import helpdeskNodesBook

from kernel.Settings import settings
from kernel.SheetFormats import SpreadsheetFormats
from kernel.BacklogFactory import BacklogFactory
from kernel.DeploymentModel import deploymentBook
from kernel.UploaderTool import Uploader
from kernel.ComponentsBook import labNodesBook

from collections import Counter

class Painter:
    def __init__(self, wb, ws):
        self._wb = wb
        self._ws = ws
        self._column = 10

    def draw_composition(self, data):
        data = {item: data[item] for item in data if data[item]}
        wb, ws = self._wb, self._ws
        chart = wb.add_chart({'type': 'pie'})
        headings = ('Type', 'Amount')
        col = self._column
        ws.write_row(0, col, headings)
        ws.write_column(1, col + 0, data)
        ws.write_column(1, col + 1, [data[k] for k in data])
        sheet_name = ws.get_name()
        chart.add_series({
            'name': [sheet_name, 0, col + 1],
            'categories': [sheet_name, 1, col + 0, len(data), col + 0],
            'values': [sheet_name, 1, col + 1, len(data), col + 1],
            'data_labels': {'category': True, 'value': True, 'leader_lines': True, 'percentage': True}
        })
        chart.set_title({'name': 'Backlog Composition'})
        # chart.set_title({'none': True})
        chart.set_legend({'position': 'top'})
        chart.set_size({'width': 507, 'height': 502, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart

    def draw_status(self, data):
        wb = self._wb
        ws = self._ws
        # print(data)
        chart = wb.add_chart({'type': 'column'})
        headings = ('Perspective', '#Items')
        _perspectives = ('Implemented', 'Working On', 'Foreseen')
        col = self._column
        ws.write_row(0, col, headings)
        #
        ws.write_column(1, col + 0, _perspectives)
        ws.write_column(1, col + 1, [data[k] for k in _perspectives])

        sheet_name = ws.get_name()
        chart.add_series({
            'name': [sheet_name, 0, col + 0],
            'categories': [sheet_name, 1, col + 0, len(data), col + 0],
            'values': [sheet_name, 1, col + 1, len(data), col + 1],
            'data_labels': {'value': True}
        })

        chart.set_title({'name': 'Backlog Status'})
        # chart.set_title({'none': True})
        chart.set_x_axis({'name': 'Perspective'})
        chart.set_y_axis({'name': '# items'})
        chart.set_legend({'none': True})
        chart.set_size({'width': 480, 'height': 502, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart

    def draw_errors(self, data):
        # print(data)
        wb, ws = self._wb, self._ws
        chart = wb.add_chart({'type': 'pie'})
        headings = ('Type', 'Amount')
        col = self._column
        ws.write_row(0, col, headings)
        _types = ('OK', 'KO')
        ws.write_column(1, col + 0, _types)
        ws.write_column(1, col + 1, [data[k] for k in _types])
        sheet_name = ws.get_name()
        chart.add_series({
            'name': [sheet_name, 0, col + 1],
            'categories': [sheet_name, 1, col + 0, len(data), col + 0],
            'values': [sheet_name, 1, col + 1, len(data), col + 1],
            'data_labels': {'category': True, 'value': True, 'leader_lines': True, 'percentage': True},
            'points': [{'fill': {'color': 'green'}},
                       {'fill': {'color': 'red'}}]
        })
        chart.set_title({'name': 'Backlog Errors'})
        # chart.set_title({'none': True})
        chart.set_legend({'position': 'top'})
        chart.set_size({'width': 288, 'height': 288, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart

    def draw_sprint_burndown(self, data):
        wb = self._wb
        ws = self._ws

        chart = wb.add_chart({'type': 'line'})
        headings = ('Day', 'Reference', 'Actual', 'Closed')
        col = self._column
        ws.write_row(0, col, headings)
        #
        ws.write_column(1, col + 0, data['categories'])
        ws.write_column(1, col + 1, data['reference'])
        ws.write_column(1, col + 2, data['actual'])
        ws.write_column(1, col + 3, data['closed'])

        sheet_name = ws.get_name()
        chart.add_series({
            'name': [sheet_name, 0, col + 1],
            'categories': [sheet_name, 1, col + 0, len(data['categories']), col + 0],
            'values': [sheet_name, 1, col + 1, len(data['reference']), col + 1],
            'line': {'dash_type': 'dash_dot'}
        })
        chart.add_series({
            'name': [sheet_name, 0, col + 2],
            'categories': [sheet_name, 1, col + 0, len(data['categories']), col + 0],
            'values': [sheet_name, 1, col + 2, len(data['actual']), col + 2]
        })

        cchart = wb.add_chart({'type': 'column'})
        cchart.add_series({
            'name': [sheet_name, 0, col + 3],
            'categories': [sheet_name, 1, col + 0, len(data['categories']), col + 0],
            'values': [sheet_name, 1, col + 3, len(data['closed']), col + 3],
            'data_labels': {'value': True}
        })
        chart.combine(cchart)

        chart.set_title({'name': 'Backlog Sprint Evolution'})
        # chart.set_title({'none': True})
        chart.set_x_axis({'name': '# day in month'})
        chart.set_y_axis({'name': '# items'})
        chart.set_legend({'position': 'top'})
        chart.set_size({'width': 700, 'height': 288, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart

    def draw_sprint_status(self, data, legend=True):
        wb, ws = self._wb, self._ws
        chart = wb.add_chart({'type': 'pie'})
        headings = ('Type', 'Amount')
        col = self._column
        ws.write_row(0, col, headings)
        ws.write_column(1, col + 0, data)
        ws.write_column(1, col + 1, [data[k] for k in data])
        sheet_name = ws.get_name()
        chart.add_series({
            'name': [sheet_name, 0, col + 1],
            'categories': [sheet_name, 1, col + 0, len(data), col + 0],
            'values': [sheet_name, 1, col + 1, len(data), col + 1],
            'data_labels': {'category': True, 'value': True, 'percentage': True}
        })

        chart.set_title({'name': 'Backlog Sprint Status'})
        # chart.set_title({'none': True})
        if legend:
            chart.set_legend({'position': 'top'})
        else:
            chart.set_legend({'none': True})

        chart.set_size({'width': 288, 'height': 288, 'x_scale': 1, 'y_scale': 1})
        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart

    def draw_evolution(self, data):
        wb = self._wb
        ws = self._ws

        chart = wb.add_chart({'type': 'line'})
        headings = ('Month', 'Created', 'Resolved', 'Updated', 'Released', 'Progress', 'Dummy')
        col = self._column
        ws.write_row(0, col, headings)
        #
        # print(data['categories'])
        ws.write_column(1, col + 0, data['categories'])
        ws.write_column(1, col + 1, data['created'])
        ws.write_column(1, col + 2, data['resolved'])
        ws.write_column(1, col + 3, data['updated'])
        ws.write_column(1, col + 4, data['released'])
        ws.write_column(1, col + 5, data['progress'])
        ws.write_column(1, col + 6, [0 for i in data['categories']])

        sheet_name = ws.get_name()
        chart.add_series({
            'name': [sheet_name, 0, col + 1],
            'categories': [sheet_name, 1, col + 0, len(data['categories']), col + 0],
            'values': [sheet_name, 1, col + 1, len(data['created']), col + 1]
        })
        chart.add_series({
            'name': [sheet_name, 0, col + 2],
            'categories': [sheet_name, 1, col + 0, len(data['categories']), col + 0],
            'values': [sheet_name, 1, col + 2, len(data['resolved']), col + 2]
        })
        chart.add_series({
            'name': [sheet_name, 0, col + 3],
            'categories': [sheet_name, 1, col + 0, len(data['categories']), col + 0],
            'values': [sheet_name, 1, col + 3, len(data['updated']), col + 3]
        })
        chart.add_series({
            'name': [sheet_name, 0, col + 4],
            'categories': [sheet_name, 1, col + 0, len(data['categories']), col + 0],
            'values': [sheet_name, 1, col + 4, len(data['released']), col + 4]
        })

        cchart = wb.add_chart({'type': 'column'})

        cchart.add_series({
            'name': [sheet_name, 0, col + 5],
            'categories': [sheet_name, 1, col + 0, len(data['categories']), col + 0],
            'values': [sheet_name, 1, col + 5, len(data['categories']), col + 5],
            # 'values': [sheet_name, 1, col+5, len(data['progress']), col+5],
            'data_labels': {'value': True}
        })
        chart.combine(cchart)

        chart.set_title({'name': 'Backlog Evolution'})
        # chart.set_title({'none': True})
        chart.set_x_axis({'name': '# Month'})
        chart.set_y_axis({'name': '# items'})
        chart.set_legend({'position': 'top'})
        chart.set_size({'width': 1000, 'height': 291, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart

    def draw_component_sprint_status(self, cmpType, components, data):
        wb = self._wb
        ws = self._ws
        _data = {item['name']: item['data'] for item in data}
        chart = wb.add_chart({'type': 'column', 'subtype': 'stacked'})
        status = tuple([item['name'] for item in data])
        headings = (cmpType,) + status
        col = self._column
        ws.write_row(0, col, headings)
        ws.write_column(1, col + 0, components)

        for i, _status in enumerate(status, start=1):
            ws.write_column(1, col + i, _data[_status])

        sheet_name = ws.get_name()

        for i, _status in enumerate(status, start=1):
            chart.add_series({
                'name': [sheet_name, 0, col + i],
                'categories': [sheet_name, 1, col + 0, len(components), col + 0],
                'values': [sheet_name, 1, col + i, len(components), col + i],
                'data_labels': {'value': True}
            })

        chart.set_title({'name': "{}s' Backlog Sprint Status".format(cmpType)})
        # chart.set_title({'none': True})
        chart.set_x_axis({'name': cmpType})
        chart.set_y_axis({'name': '# items'})
        chart.set_legend({'position': 'top'})
        chart.set_size({'width': 1000, 'height': 291, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart

    def draw_component_status(self, cmpType, components, data):
        wb = self._wb
        ws = self._ws
        _data = {item['name']: item['data'] for item in data}
        chart = wb.add_chart({'type': 'column', 'subtype': 'stacked'})
        status = tuple([item['name'] for item in data])
        headings = (cmpType,) + status
        col = self._column
        ws.write_row(0, col, headings)
        ws.write_column(1, col + 0, components)

        for i, _status in enumerate(status, start=1):
            ws.write_column(1, col + i, _data[_status])

        sheet_name = ws.get_name()

        for i, _status in enumerate(status, start=1):
            chart.add_series({
                'name': [sheet_name, 0, col + i],
                'categories': [sheet_name, 1, col + 0, len(components), col + 0],
                'values': [sheet_name, 1, col + i, len(components), col + i],
                'data_labels': {'value': True}
            })

        chart.set_title({'name': "{}s' Backlog Status".format(cmpType)})
        # chart.set_title({'none': True})
        chart.set_x_axis({'name': 'Enablers'})
        chart.set_y_axis({'name': '# items'})
        chart.set_legend({'position': 'top'})
        chart.set_size({'width': 1000, 'height': 291, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart

    def draw_chapters_sprint_status(self, chapters, data):
        wb = self._wb
        ws = self._ws
        _data = {item['name']: item['data'] for item in data}
        chart = wb.add_chart({'type': 'column', 'subtype': 'stacked'})
        status = tuple([item['name'] for item in data])
        headings = ('Chapter',) + status
        col = self._column
        ws.write_row(0, col, headings)
        ws.write_column(1, col + 0, chapters)

        for i, _status in enumerate(status, start=1):
            ws.write_column(1, col + i, _data[_status])

        sheet_name = ws.get_name()

        for i, _status in enumerate(status, start=1):
            chart.add_series({
                'name': [sheet_name, 0, col + i],
                'categories': [sheet_name, 1, col + 0, len(chapters), col + 0],
                'values': [sheet_name, 1, col + i, len(chapters), col + i],
                'data_labels': {'value': True}
            })
        chart.set_title({'name': "Chapters' Backlog Sprint Status"})
        # chart.set_title({'none': True})
        chart.set_x_axis({'name': 'Chapters'})
        chart.set_y_axis({'name': '# items'})
        chart.set_legend({'position': 'top'})
        chart.set_size({'width': 1000, 'height': 291, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart

    def draw_lab_status(self, nodes, data):
        wb = self._wb
        ws = self._ws
        _data = {item['name']: reversed(item['data']) for item in data}
        chart = wb.add_chart({'type': 'bar', 'subtype': 'stacked'})
        status = tuple([item['name'] for item in data])
        headings = ('Node',) + status
        col = self._column
        ws.write_row(0, col, headings)
        ws.write_column(1, col + 0, reversed(nodes))

        for i, _status in enumerate(status, start=1):
            ws.write_column(1, col + i, _data[_status])

        sheet_name = ws.get_name()

        for i, _status in enumerate(status, start=1):
            chart.add_series({
                'name': [sheet_name, 0, col + i],
                'categories': [sheet_name, 1, col + 0, len(nodes), col + 0],
                'values': [sheet_name, 1, col + i, len(nodes), col + i],
                'data_labels': {'value': True}
            })

        chart.set_title({'name': "Enablers' Backlog Status"})
        chart.set_y_axis({'name': 'Enablers'})
        chart.set_x_axis({'name': '# items'})
        chart.set_legend({'position': 'top'})
        chart.set_size({'width': 1000, 'height': 1600, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1

        return chart

    def draw_chapters_status(self, chapters, data):
        wb = self._wb
        ws = self._ws
        _data = {item['name']: item['data'] for item in data}
        chart = wb.add_chart({'type': 'column', 'subtype': 'stacked'})
        status = tuple([item['name'] for item in data])
        headings = ('Chapter',) + status
        col = self._column
        ws.write_row(0, col, headings)
        ws.write_column(1, col + 0, chapters)

        for i, _status in enumerate(status, start=1):
            ws.write_column(1, col + i, _data[_status])

        sheet_name = ws.get_name()

        for i, _status in enumerate(status, start=1):
            chart.add_series({
                'name': [sheet_name, 0, col + i],
                'categories': [sheet_name, 1, col + 0, len(chapters), col + 0],
                'values': [sheet_name, 1, col + i, len(chapters), col + i],
                'data_labels': {'value': True}
            })
        chart.set_title({'name': "Chapters' Backlog Status"})
        # chart.set_title({'none': True})
        chart.set_x_axis({'name': 'Chapters'})
        chart.set_y_axis({'name': '# items'})
        chart.set_legend({'position': 'top'})
        chart.set_size({'width': 1000, 'height': 291, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart

    def draw_enablers_status(self, enablers, data):
        wb = self._wb
        ws = self._ws
        _data = {item['name']: reversed(item['data']) for item in data}
        chart = wb.add_chart({'type': 'bar', 'subtype': 'stacked'})
        status = tuple([item['name'] for item in data])
        headings = ('Enabler',) + status
        col = self._column
        ws.write_row(0, col, headings)
        ws.write_column(1, col + 0, reversed(enablers))

        for i, _status in enumerate(status, start=1):
            ws.write_column(1, col + i, _data[_status])

        sheet_name = ws.get_name()

        for i, _status in enumerate(status, start=1):
            chart.add_series({
                'name': [sheet_name, 0, col + i],
                'categories': [sheet_name, 1, col + 0, len(enablers), col + 0],
                'values': [sheet_name, 1, col + i, len(enablers), col + i],
                'data_labels': {'value': True}
            })

        chart.set_title({'name': "Enablers' Backlog Status"})
        # chart.set_title({'none': True})
        chart.set_y_axis({'name': 'Enablers'})
        chart.set_x_axis({'name': '# items'})
        chart.set_legend({'position': 'top'})
        chart.set_size({'width': 1000, 'height': 1600, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1

        return chart


class BacklogReporter:

    def __init__(self):
        self.calendar = agileCalendar
        self.workbook = None
        self.spFormats = None
        self.factory = BacklogFactory()
        self.gReporter = ChaptersReporter(self.factory.getTechChaptersBacklog())
        self.gLabReporter = LabReporter(self.factory.getLabChapterBacklog())
        self.start = date(2016, 12, 1)  # year, month, day
        self.end = date(2017, 11, 30)  # year, month, day

    def get_format(self, issue):
        _timeSlot = issue.timeSlot.split(' ')[1] if issue.timeSlot != 'Unscheduled' else 'Unscheduled'
        if _timeSlot in agileCalendar.pastTimeSlots:
            return self.spFormats.brown
        elif _timeSlot in agileCalendar.currentTimeSlots():
            return self.spFormats.green
        else:
            return self.spFormats.blue

    def _write_issue(self, ws, row, item):
        ws.write_url(row, 0, item.url, self.spFormats.link, item.key)
        if item.issueType == 'Epic':
            _format = self.workbook.add_format({'color': 'blue', 'underline': 1,
                                                'align': 'left', 'bg_color': '#99CC00'})
            if item.p_url:
                ws.write_url(row, 1, item.p_url, _format, item.name)
            else:
                ws.write(row, 1, item.name)
            _format = self.workbook.add_format({'bg_color': '#99CC00'})
            ws.write(row, 2, '', _format)
            ws.write(row, 3, item.status, _format)
            ws.write(row, 4, item.issueType, _format)
        elif item.issueType == 'Feature':
            if item.p_url:
                ws.write_url(row, 1, item.p_url, self.spFormats.lefty_link, item.name)
            else:
                ws.write(row, 1, item.name)
            _format = self.get_format(item)
            ws.write(row, 2, item.timeSlot, _format)
            ws.write(row, 3, item.status, _format)
            ws.write(row, 4, item.issueType, _format)
        else:
            if item.p_url:
                ws.write_url(row, 1, item.p_url, self.spFormats.lefty_link, item.name)
            else:
                ws.write(row, 1, item.name)
            _format = self.get_format(item)
            ws.write(row, 2, item.timeSlot, _format)
            ws.write(row, 3, item.status, _format)
            ws.write(row, 4, item.issueType, _format)

    def _coordination_dashboard(self, coordination):
        wb = self.workbook
        ws = wb.add_worksheet(coordination.name[1:])
        backlog = self.factory.getCoordinationBacklog(coordination.key)
        backlog.sort(key=backlog.sortDict['name'])
        # print(coordination.project)

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
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime))
        # row += 1
        ws.write(row, 2, 'Report Date:', self.spFormats.bold_right)
        ws.write(row, 3, date.today().strftime('%d-%m-%Y'))

        row += 1
        ws.write(row, 0, 'Start of Data Analysis:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime(current_date=self.start)))

        row += 1
        ws.write(row, 0, 'End of Data Analysis:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime(current_date=self.end)))

        #
        row += 2
        _format = self.workbook.add_format({'bold': True, 'font_size': 15, 'bg_color': '#60C1CF'})
        ws.write(row, 0, 'Backlog Owner:', self.spFormats.bold_right)
        ws.write(row, 1, coordination.leader, _format)
        ws.write(row, 2, '', _format)

        #
        row += 2
        ws.write(row, 0, 'Backlog Summary:', self.spFormats.bold_right)
        ws.write(row, 1, '# Items', self.spFormats.bold_left)
        # return
        row += 1
        reporter = CoordinationReporter(coordination.project, backlog)
        data = reporter.issueType
        ws.write(row, 0, 'Composition', self.spFormats.bold_right)
        ws.write(row, 1, '{0} Issues = {Epic} Epics + {Feature} Features + '
                         '{Story} User Stories + {WorkItem} WorkItems + {Bug} Bugs'.format(sum(data.values()), **data))
        #
        row += 1
        data = reporter.perspective
        ws.write(row, 0, 'Status', self.spFormats.bold_right)
        ws.write(row, 1, '{0} Issues = {Implemented} Implemented  + {Working On} Working On  + '
                         ' {Foreseen} Foreseen'.format(sum(data.values()), **data))

        row += 2
        chart = painter.draw_composition(reporter.issueType)
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        chart = painter.draw_status(reporter.perspective)
        ws.insert_chart(row, 1, chart, {'x_offset': 520, 'y_offset': 0})

        row += 26
        chart = painter.draw_evolution(reporter.implemented(self.start, self.end))
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        row += 15
        _format = self.workbook.add_format({'bold': True, 'font_size': 20, 'bg_color': '#60C1CF', 'align': 'center'})
        ws.merge_range(xl_range(row, 0, row, 4), 'Backlog Entries', _format)
        row += 1

        ws.write_row(row, 0, ('Item Id', 'Item reference', 'Time frame', 'Status', 'Item type'),
                     self.spFormats.column_heading)
        for issue in backlog:
            row += 1
            self._write_issue(ws, row, issue)

    def _enabler_dashboard(self, enabler):
        print('------>', enabler.name)
        wb = self.workbook
        ws = wb.add_worksheet(enabler.name)
        backlog = self.factory.getEnablerBacklog(enabler.name)
        backlog.sort(key=backlog.sortDict['name'])

        painter = Painter(wb, ws)
        ws.set_zoom(80)
        ws.set_column(0, 0, 30)
        ws.set_column(1, 1, 122)
        ws.set_column(2, 5, 20)
        row, col = 0, 0

        _heading = self.workbook.add_format({'bold': True, 'font_size': 30,
                                             'bg_color': '#002D67', 'font_color': '#FFE616', 'align': 'center'})
        ws.merge_range(xl_range(row, 0, row, 3),
                       "Backlog for Enabler: '{0}'".format(enabler.name), _heading)
        ws.set_row(0, 42)
        ws.insert_image(0, 0, settings.logofiware, {'x_scale': 0.5, 'y_scale': 0.5, 'x_offset': 0, 'y_offset': 0})

        row += 1
        ws.write(row, 0, 'Project Time:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime()))
        # row += 1
        ws.write(row, 2, 'Report Date:', self.spFormats.bold_right)
        ws.write(row, 3, date.today().strftime('%d-%m-%Y'))

        row += 1
        ws.write(row, 0, 'Start of Data Analysis:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime(current_date=self.start)))

        row += 1
        ws.write(row, 0, 'End of Data Analysis:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime(current_date=self.end)))

        #
        row += 2
        _format = self.workbook.add_format({'bold': True, 'font_size': 15, 'color': 'green'})
        ename = enabler.Name if enabler.GE else enabler.name
        ws.write(row, 0, 'Enabler:', self.spFormats.bold_right)
        ws.write(row, 1, ename, _format)
        row += 1
        _format = self.workbook.add_format({'bold': True, 'font_size': 15, 'bg_color': '#60C1CF'})
        ws.write(row, 0, 'Product Owner:', self.spFormats.bold_right)
        ws.write(row, 1, '{} - {}'.format(enabler.owner, enabler.leader), _format)
        ws.write(row, 2, '', _format)

        row += 1
        ws.write(row, 0, 'Work Mode:', self.spFormats.bold_right)
        ws.write(row, 1, enabler.mode)

        row += 2
        ws.write(row, 0, 'Backlog Summary:', self.spFormats.bold_right)
        ws.write(row, 1, '# Items', self.spFormats.bold_left)
        #
        row += 1
        # return
        reporter = EnablerReporter(enabler.name, backlog)
        data = reporter.issueType
        ws.write(row, 0, 'Composition', self.spFormats.bold_right)
        ws.write(row, 1, '{0:,} Issues = {Epic} Epics + {Feature} Features + '
                         '{Story:,} User Stories + {WorkItem:,} WorkItems + {Bug} Bugs'.format(sum(data.values()),
                                                                                               **data))
        #
        row += 1
        data = reporter.perspective
        ws.write(row, 0, 'Status', self.spFormats.bold_right)
        ws.write(row, 1, '{0:,} Issues = {Implemented:,} Implemented  + {Working On} Working On  + '
                         ' {Foreseen} Foreseen'.format(sum(data.values()), **data))
        #

        if not reporter.length:
            return

        row += 2
        chart = painter.draw_composition(reporter.issueType)
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        chart = painter.draw_status(reporter.perspective)
        ws.insert_chart(row, 1, chart, {'x_offset': 520, 'y_offset': 0})

        row += 26
        chart = painter.draw_evolution(reporter.implemented(self.start, self.end))
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})
        row += 15

        row += 1
        _format = self.workbook.add_format({'bold': True, 'font_size': 20, 'bg_color': '#60C1CF', 'align': 'center'})
        ws.merge_range(xl_range(row, 0, row, 4), 'Backlog Entries', _format)
        row += 1

        ws.write_row(row, 0, ('Item Id', 'Item reference', 'Time frame', 'Status', 'Item type'),
                     self.spFormats.column_heading)
        for issue in backlog:
            row += 1
            self._write_issue(ws, row, issue)

    def _lab_node_dashboard(self, node):
        print('------>', node)
        wb = self.workbook
        ws = wb.add_worksheet(node)
        # backlog = self.factory.getLabChapterBacklog()
        backlog = self.gLabReporter

        try:
            key = labNodesBook[node].key
            backlog = list(filter(lambda x: x.component == key, list(backlog.backlog)))
        except Exception:
            # There is no data about the corresponding node, therefore we manage it as a empty issues
            backlog = ()

        painter = Painter(wb, ws)
        ws.set_zoom(80)
        ws.set_column(0, 0, 30)
        ws.set_column(1, 1, 122)
        ws.set_column(2, 5, 20)
        row, col = 0, 0

        _heading = self.workbook.add_format({'bold': True, 'font_size': 30,
                                             'bg_color': '#002D67', 'font_color': '#FFE616', 'align': 'center'})
        ws.merge_range(xl_range(row, 0, row, 3),
                       "Backlog for Lab Node: '{0}'".format(node), _heading)
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

        #
        row += 2
        _format = self.workbook.add_format({'bold': True, 'font_size': 15, 'color': 'green'})
        ws.write(row, 0, 'Node:', self.spFormats.bold_right)
        ws.write(row, 1, node, _format)

        row += 1
        ws.write(row, 0, 'Work Mode:', self.spFormats.bold_right)

        try:
            ws.write(row, 1, labNodesBook[node].mode)
        except Exception:
            # there is no data about the node, therefore we consider the node Inactive
            ws.write(row, 1, 'Inactive')

        row += 2
        ws.write(row, 0, 'Backlog Summary:', self.spFormats.bold_right)
        ws.write(row, 1, '# Items', self.spFormats.bold_left)

        row += 1
        if len(backlog) == 0:
            ws.write(row, 0, 'Composition', self.spFormats.bold_right)
            ws.write(row, 1, '0 Issues = 0 Epics + 0 Features + 0 User Stories + 0 WorkItems + 0 Bugs')

            row += 1
            ws.write(row, 0, 'Status', self.spFormats.bold_right)
            ws.write(row, 1, '0 Issues = 0 Implemented  + 0 Working On  + 0 Foreseen')

            return
        else:
            data = Counter(list(map(lambda x: x['issueType'], backlog)))
            data_issue_type = \
                BacklogReporter.fix_values(a_dict=data, keys=['Epic', 'Feature', 'Story', 'WorkItem', 'Bug'])

            ws.write(row, 0, 'Composition', self.spFormats.bold_right)
            text = '{0:,} Issues = {Epic} Epics + {Feature} Features + {Story} User Stories ' \
                   '+ {WorkItem} WorkItems + {Bug} Bugs'.format(sum(data_issue_type.values()), **data_issue_type)
            ws.write(row, 1, text)

            row += 1
            data = Counter(list(map(lambda x: x['frame'], backlog)))
            data_frame = \
                BacklogReporter.fix_values(a_dict=data, keys=['Implemented', 'Working On', 'Foreseen'])

            ws.write(row, 0, 'Status', self.spFormats.bold_right)
            ws.write(row, 1, '{0:,} Issues = {Implemented:,} Implemented  + {Working On} Working On  + '
                             ' {Foreseen} Foreseen'.format(sum(data_frame.values()), **data_frame))

            row += 2
            chart = painter.draw_composition(data_issue_type)
            ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

            chart = painter.draw_status(data_frame)
            ws.insert_chart(row, 1, chart, {'x_offset': 520, 'y_offset': 0})

            row += 26
            from kernel.Reporter import Reporter
            data = Reporter(backlog)
            chart = painter.draw_evolution(data.implemented(self.start, self.end))
            ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

            row += 16
            _format = self.workbook.add_format({'bold': True, 'font_size': 20, 'bg_color': '#60C1CF', 'align': 'center'})
            ws.merge_range(xl_range(row, 0, row, 4), 'Backlog Entries', _format)

            row += 1
            ws.write_row(row, 0, ('Item Id', 'Item reference', 'Time frame', 'Status', 'Item type'),
                         self.spFormats.column_heading)
            for issue in backlog:
                row += 1
                self._write_issue(ws, row, issue)

    @staticmethod
    def fix_values(a_dict, keys, value=0):
        result = {}

        for key in keys:
            try:
                result[key] = a_dict[key]
            except KeyError:
                result[key] = value

        return result

    def _tool_dashboard(self, tool):
        print('------>', tool.name)
        wb = self.workbook
        ws = wb.add_worksheet(tool.name)
        backlog = self.factory.getToolBacklog(tool.name)
        backlog.sort(key=backlog.sortDict['name'])
        painter = Painter(wb, ws)
        ws.set_zoom(80)
        ws.set_column(0, 0, 30)
        ws.set_column(1, 1, 122)
        ws.set_column(2, 5, 20)
        row, col = 0, 0

        _heading = self.workbook.add_format({'bold': True, 'font_size': 30,
                                             'bg_color': '#002D67', 'font_color': '#FFE616', 'align': 'center'})
        ws.merge_range(xl_range(row, 0, row, 3),
                       "Backlog for Tool: '{0}'".format(tool.name), _heading)
        ws.set_row(0, 42)
        ws.insert_image(0, 0, settings.logofiware, {'x_scale': 0.5, 'y_scale': 0.5, 'x_offset': 0, 'y_offset': 0})

        row += 1
        ws.write(row, 0, 'Project Time:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime))
        # row += 1
        ws.write(row, 2, 'Report Date:', self.spFormats.bold_right)
        ws.write(row, 3, date.today().strftime('%d-%m-%Y'))
        #

        row += 1
        ws.write(row, 0, 'Start of Data Analysis:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime(current_date=self.start)))

        row += 1
        ws.write(row, 0, 'End of Data Analysis:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime(current_date=self.end)))

        row += 2
        _format = self.workbook.add_format({'bold': True, 'font_size': 15, 'bg_color': '#60C1CF'})
        ws.write(row, 0, 'Product Owner:', self.spFormats.bold_right)
        ws.write(row, 1, '{} - {}'.format(tool.owner, tool.leader), _format)
        ws.write(row, 2, '', _format)

        row += 1
        ws.write(row, 0, 'Work Mode:', self.spFormats.bold_right)
        ws.write(row, 1, tool.mode)

        row += 2
        ws.write(row, 0, 'Backlog Summary:', self.spFormats.bold_right)
        ws.write(row, 1, '# Items', self.spFormats.bold_left)
        #
        row += 1
        # return
        reporter = ToolReporter(tool.name, backlog)
        data = reporter.issueType
        ws.write(row, 0, 'Composition', self.spFormats.bold_right)
        ws.write(row, 1, '{0} Issues = {Epic} Epics + {Feature} Features + '
                         '{Story} User Stories + {WorkItem} WorkItems + {Bug} Bugs'.format(sum(data.values()), **data))
        #
        row += 1
        data = reporter.perspective
        ws.write(row, 0, 'Status', self.spFormats.bold_right)
        ws.write(row, 1, '{0} Issues = {Implemented} Implemented  + {Working On} Working On  + '
                         ' {Foreseen} Foreseen'.format(sum(data.values()), **data))
        #
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
                             '{:,} Issues = {OK:,}'.format(sum(data.values()), **data), self.spFormats.green, ' OK',
                             ' + '
                             ' {KO:,}'.format(sum(data.values()), **data), self.spFormats.red, ' KO')

        if not reporter.length:
            return

        row += 2
        chart = painter.draw_composition(reporter.issueType)
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        chart = painter.draw_status(reporter.perspective)
        ws.insert_chart(row, 1, chart, {'x_offset': 520, 'y_offset': 0})

        row += 26
        chart = painter.draw_evolution(reporter.implemented(self.start, self.end))
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})
        row += 15

        _format = self.workbook.add_format({'bold': True, 'font_size': 20, 'bg_color': '#60C1CF', 'align': 'center'})
        ws.merge_range(xl_range(row, 0, row, 4), 'Backlog Entries', _format)
        row += 1

        ws.write_row(row, 0, ('Item Id', 'Item reference', 'Time frame', 'Status', 'Item type'),
                     self.spFormats.column_heading)
        for issue in backlog:
            row += 1
            self._write_issue(ws, row, issue)

    def _chapter_dashboard(self, chapter):
        print('------>', chapter.name)
        wb = self.workbook
        ws = wb.add_worksheet('{} Chapter'.format(chapter.name))
        backlog = self.factory.getChapterBacklog(chapter.name)

        painter = Painter(wb, ws)
        ws.set_zoom(80)
        ws.set_column(0, 0, 30)
        ws.set_column(1, 1, 122)
        ws.set_column(2, 5, 20)
        row, col = 0, 0

        _heading = self.workbook.add_format({'bold': True, 'font_size': 30,
                                             'bg_color': '#002D67', 'font_color': '#FFE616', 'align': 'center'})
        ws.merge_range(xl_range(row, 0, row, 3),
                       "Backlog for Chapter: '{0}'".format(chapter.name), _heading)
        ws.set_row(0, 42)
        ws.insert_image(0, 0, settings.logofiware, {'x_scale': 0.5, 'y_scale': 0.5, 'x_offset': 0, 'y_offset': 0})

        row += 1
        ws.write(row, 0, 'Project Time:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime()))
        # row += 1
        ws.write(row, 2, 'Report Date:', self.spFormats.bold_right)
        ws.write(row, 3, date.today().strftime('%d-%m-%Y'))

        row += 1
        ws.write(row, 0, 'Start of Data Analysis:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime(current_date=self.start)))

        row += 1
        ws.write(row, 0, 'End of Data Analysis:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime(current_date=self.end)))

        #
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
        if deploymentBook.roadmap[chapter.name]:
            ws.write(row, 0, 'Roadmap:', self.spFormats.bold_right)
            ws.write_url(row, 1, '{0}'.format(deploymentBook.roadmap[chapter.name]))
            row += 1

        link = deploymentBook.tracker[chapter.name] + '&func=browse'
        ws.write(row, 0, 'Tracker:', self.spFormats.bold_right)
        ws.write_url(row, 1, '{0}'.format(link))

        row += 1
        link = 'http://backlog.fiware.org/chapter/{}'.format(chapter.name)
        ws.write(row, 0, 'Backlog:', self.spFormats.bold_right)
        ws.write_url(row, 1, '{0}'.format(link))

        if deploymentBook.materializing[chapter.name]:
            row += 1
            ws.write(row, 0, 'Materializing:', self.spFormats.bold_right)
            ws.write_url(row, 1, '{0}'.format(deploymentBook.materializing[chapter.name]))

        row += 2
        ws.write(row, 0, 'Backlog Structure:', self.spFormats.bold_right)
        n_enablers = len(chapter.enablers)
        n_tools = len(chapter.tools)
        n_coordination = 1
        data = (n_enablers + n_tools + n_coordination, n_enablers, n_tools, n_coordination)
        ws.write(row, 1, '{} Components = {} Enablers + {} Tools + {} Coordination'.format(*data))

        row += 1
        ws.write(row, 0, 'Backlog Summary:', self.spFormats.bold_right)
        ws.write(row, 1, '# Items', self.spFormats.bold_left)
        #
        row += 1
        # return
        reporter = ChapterReporter(chapter.name, backlog)
        data = reporter.issueType
        ws.write(row, 0, 'Composition', self.spFormats.bold_right)
        ws.write(row, 1, '{0:,} Issues = {Epic:,} Epics + {Feature:,} Features + '
                         '{Story:,} User Stories + {WorkItem:,} WorkItems + {Bug:,} Bugs'.format(sum(data.values()),
                                                                                                 **data))
        #
        row += 1
        data = reporter.perspective
        ws.write(row, 0, 'Status', self.spFormats.bold_right)
        ws.write(row, 1, '{0:,} Issues = {Implemented:,} Implemented  + {Working On:,} Working On  + '
                         ' {Foreseen:,} Foreseen'.format(sum(data.values()), **data))

        row += 2
        chart = painter.draw_composition(reporter.issueType)
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        chart = painter.draw_status(reporter.perspective)
        ws.insert_chart(row, 1, chart, {'x_offset': 520, 'y_offset': 0})

        # row += 15
        # chart = painter.draw_enablers_sprint_status(reporter.enablers,
        #                                    reporter.frame_status_graph_data)
        # ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})
        if len(reporter.enablers):
            row += 26
            chart = painter.draw_component_status('Enabler', reporter.enablers, reporter.enablers_execution_status)
            ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        if len(reporter.tools):
            row += 15
            chart = painter.draw_component_status('Tool', reporter.tools, reporter.tools_execution_status)
            ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        row += 15
        chart = painter.draw_evolution(reporter.implemented(self.start, self.end))
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})
        row += 15
        ws.write(row, 0, '')

    def _techChapters_dashboard(self):
        print('---> TechChapters')
        wb = self.workbook
        ws = wb.add_worksheet('Overview')

        painter = Painter(wb, ws)
        ws.set_zoom(80)
        ws.set_column(0, 0, 30)
        ws.set_column(1, 1, 122)
        ws.set_column(2, 5, 20)
        row, col = 0, 0

        _heading = self.workbook.add_format({'bold': True, 'font_size': 30,
                                             'bg_color': '#002D67', 'font_color': '#FFE616', 'align': 'center'})
        ws.merge_range(xl_range(row, 0, row, 3),
                       "Backlog for Technical Chapters", _heading)
        ws.set_row(0, 42)
        ws.insert_image(0, 0, settings.logofiware, {'x_scale': 0.5, 'y_scale': 0.5, 'x_offset': 0, 'y_offset': 0})

        row += 1
        ws.write(row, 0, 'Project Time:', self.spFormats.bold_right)
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime()))
        # row += 1
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
        ws.write(row, 0, 'Scrum Master:', self.spFormats.bold_right)
        ws.write(row, 1, 'FF - Veronika Vlnkova', _format)
        ws.write(row, 2, '', _format)

        row += 1
        _format = self.workbook.add_format({'bold': True, 'font_size': 15, 'bg_color': '#60C1CF'})
        ws.write(row, 0, 'Technical Scrum Master:', self.spFormats.bold_right)
        ws.write(row, 1, 'FF - Fernando López', _format)
        ws.write(row, 2, '', _format)

        # return
        row += 1
        ws.write(row, 0, 'Backlog Structure:', self.spFormats.bold_right)
        ws.write(row, 1, '# Items', self.spFormats.bold_left)
        row += 1
        ws.write(row, 1, '{} Chapters'.format(len(self.gReporter.chapters)))
        n_enablers = sum([len(chaptersBook[chapter].enablers) for chapter in chaptersBook])
        n_tools = sum([len(chaptersBook[chapter].tools) for chapter in chaptersBook])
        n_coordination = len([chaptersBook[chapter].coordination for chapter in chaptersBook])
        data = (n_enablers + n_tools + n_coordination, n_enablers, n_tools, n_coordination)
        row += 1
        ws.write(row, 1, '{} Components = {} Enablers + {} Tools + {} Coordination'.format(*data))
        #
        row += 1
        ws.write(row, 0, 'Backlog Summary:', self.spFormats.bold_right)
        ws.write(row, 1, '# Items', self.spFormats.bold_left)
        #
        reporter = self.gReporter
        row += 1
        data = reporter.issueType
        ws.write(row, 0, 'Composition', self.spFormats.bold_right)
        ws.write(row, 1, '{0:,} Issues = {Epic:,} Epics + {Feature:,} Features + '
                         '{Story:,} User Stories + {WorkItem:,} WorkItems + {Bug:,} Bugs'.format(sum(data.values()),
                                                                                                 **data))
        #
        row += 1
        data = reporter.perspective
        ws.write(row, 0, 'Status', self.spFormats.bold_right)
        ws.write(row, 1, '{0:,} Issues = {Implemented:,} Implemented  + {Working On:,} Working On  + '
                         ' {Foreseen:,} Foreseen'.format(sum(data.values()), **data))

        row += 2
        chart = painter.draw_composition(reporter.issueType)
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        chart = painter.draw_status(reporter.perspective)
        ws.insert_chart(row, 1, chart, {'x_offset': 520, 'y_offset': 0})

        row += 26
        chart = painter.draw_evolution(reporter.implemented(self.start, self.end))
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        row += 15
        chart = painter.draw_chapters_status(reporter.chapters, reporter.chapters_execution_status)
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        row += 15
        chart = painter.draw_enablers_status(reporter.enablers, reporter.enablers_execution_status)
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        row += 50
        ws.write(row, 0, '')

    def chapter(self, chaptername):
        if chaptername not in settings.chapters:
            raise Exception("Unknown chapter: {}".format(chaptername))

        print()
        print("--monitor-- chapter:", chaptername)

        _date = datetime.now().strftime("%Y%m%d-%H%M")
        filename = 'FIWARE.backlog.report.' + chaptername + '.' + _date + '.xlsx'
        myfile = os.path.join(settings.outHome, filename)
        self.workbook = xlsxwriter.Workbook(myfile)
        self.spFormats = SpreadsheetFormats(self.workbook)
        self._techChapters_dashboard()

        chapter = chaptersBook[chaptername]
        self._chapter_dashboard(chapter)
        self._coordination_dashboard(chapter.coordination)

        for _enabler in chapter.enablers:
            self._enabler_dashboard(chapter.enablers[_enabler])

        for _tool in chapter.tools:
            self._tool_dashboard(chapter.tools[_tool])

        print(chaptername, ': W:' + myfile)
        self.workbook.close()

    def _lab_chapter_dashboard(self):
        print('---> LabChapter')
        wb = self.workbook
        ws = wb.add_worksheet('Overview')

        painter = Painter(wb, ws)
        ws.set_zoom(80)
        ws.set_column(0, 0, 30)
        ws.set_column(1, 1, 122)
        ws.set_column(2, 5, 20)
        row, col = 0, 0

        _heading = self.workbook.add_format({'bold': True, 'font_size': 30,
                                             'bg_color': '#002D67', 'font_color': '#FFE616', 'align': 'center'})

        ws.merge_range(xl_range(row, 0, row, 3),
                       "Backlog for Lab Chapter", _heading)

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
        ws.write(row, 0, 'Scrum Master:', self.spFormats.bold_right)
        ws.write(row, 1, 'FF - Veronika Vlnkova', _format)
        ws.write(row, 2, '', _format)

        row += 1
        _format = self.workbook.add_format({'bold': True, 'font_size': 15, 'bg_color': '#60C1CF'})
        ws.write(row, 0, 'Technical Scrum Master:', self.spFormats.bold_right)
        ws.write(row, 1, 'FF - Fernando López', _format)
        ws.write(row, 2, '', _format)

        row += 1
        ws.write(row, 0, 'Backlog Structure:', self.spFormats.bold_right)
        ws.write(row, 1, '# Items', self.spFormats.bold_left)

        row += 1
        ws.write(row, 1, '{} Nodes'.format(len(self.gLabReporter.lab_nodes)))

        row += 2
        ws.write(row, 0, 'Backlog Summary:', self.spFormats.bold_right)
        ws.write(row, 1, '# Items', self.spFormats.bold_left)

        reporter = self.gLabReporter
        row += 1
        data = reporter.issueType
        ws.write(row, 0, 'Composition', self.spFormats.bold_right)
        ws.write(row, 1, '{0:,} Issues = {Epic:,} Epics + {Feature:,} Features + '
                         '{Story:,} User Stories + {WorkItem:,} WorkItems + {Bug:,} Bugs'.format(sum(data.values()),
                                                                                                 **data))
        #
        row += 1
        data = reporter.perspective
        ws.write(row, 0, 'Status', self.spFormats.bold_right)
        ws.write(row, 1, '{0:,} Issues = {Implemented:,} Implemented  + {Working On:,} Working On  + '
                         ' {Foreseen:,} Foreseen'.format(sum(data.values()), **data))

        row += 2
        chart = painter.draw_composition(reporter.issueType)
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        chart = painter.draw_status(reporter.perspective)
        ws.insert_chart(row, 1, chart, {'x_offset': 520, 'y_offset': 0})

        row += 26
        chart = painter.draw_evolution(reporter.implemented(self.start, self.end))
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        #reporter = self.gReporter
        row += 15
        #filtered_data = map(lambda x: [x.component, x.frame], self.gLabReporter.backlog)
        #implemented = Counter(map(lambda x: x[0], filter(lambda x: x[1] == 'Implemented', filtered_data)))
        #working_on = Counter(map(lambda x: x[0], filter(lambda x: x[1] == 'Working On', filtered_data)))
        #foreseen = Counter(map(lambda x: x[0], filter(lambda x: x[1] == 'Foreseen', filtered_data)))
        chart = painter.draw_lab_status(self.gLabReporter.lab_nodes, reporter.nodes_execution_status)
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        row += 50
        ws.write(row, 0, '')

    def lab(self):
        print()
        print("--monitor-- chapter: Lab")

        _date = datetime.now().strftime("%Y%m%d-%H%M")
        filename = 'FIWARE.backlog.report.lab.' + _date + '.xlsx'
        myfile = os.path.join(settings.outHome, filename)
        self.workbook = xlsxwriter.Workbook(myfile)
        self.spFormats = SpreadsheetFormats(self.workbook)
        self._lab_chapter_dashboard()

        # for each node we have to get the data to show detailed information
        for node in helpdeskNodesBook:
            self._lab_node_dashboard(node)

        print('Lab: W:' + myfile)
        self.workbook.close()


class WorkBench:
    @staticmethod
    def report():
        print('report')
        reporter = BacklogReporter()
        chapters = settings.chapters

        for _chapter in chapters:
            reporter.chapter(_chapter)

        reporter.lab()

    @staticmethod
    def snapshot():
        print('snapshot')
        DataEngine.snapshot(storage=settings.storeHome)

    @staticmethod
    def upload():
        print('upload')
        uploader = Uploader()
        uploader.upload('backlog', 'report', settings.chapters)


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
