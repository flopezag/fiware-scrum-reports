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

from kernel.Reporter import ChapterReporter, EnablerReporter, CoordinationReporter, ChaptersReporter, ToolReporter
from kernel.Calendar import agileCalendar
from kernel.TrackerBook import chaptersBook, coordinationBook
from kernel.DataFactory import DataEngine

from kernel.Settings import settings
from kernel.SheetFormats import SpreadsheetFormats
from kernel.BacklogFactory import BacklogFactory
from kernel.DeploymentModel import deploymentBook
from kernel.UploaderTool import Uploader


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
        chart.set_size({'width': 288, 'height': 288, 'x_scale': 1, 'y_scale': 1})

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
        chart.set_size({'width': 700, 'height': 288, 'x_scale': 1, 'y_scale': 1})

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
        chart.set_size({'width': 1000, 'height': 288, 'x_scale': 1, 'y_scale': 1})

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
        chart.set_size({'width': 1000, 'height': 288, 'x_scale': 1, 'y_scale': 1})

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
        chart.set_size({'width': 1000, 'height': 288, 'x_scale': 1, 'y_scale': 1})

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
        chart.set_size({'width': 1000, 'height': 288, 'x_scale': 1, 'y_scale': 1})

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
        chart.set_size({'width': 1000, 'height': 288, 'x_scale': 1, 'y_scale': 1})

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


class GlobalBacklogReporter:

    def __init__(self):
        self.calendar = agileCalendar
        self.workbook = None
        self.spFormats = None
        self.factory = BacklogFactory()
        backlog = self.factory.getCoordinationBacklog('11700')

        self.gReporter = EnablerReporter(enablername='QualityAssurance',
                                         backlog=backlog)

    def get_format(self, issue):
        _timeSlot = issue.timeSlot.split(' ')[1] if issue.timeSlot != 'Unscheduled' else 'Unscheduled'
        if _timeSlot in agileCalendar.pastTimeSlots:
            return self.spFormats.brown
        elif _timeSlot in agileCalendar.currentTimeSlots:
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

    def _enabler_dashboard(self, enabler):
        print('--->', enabler.name)
        wb = self.workbook
        ws = wb.add_worksheet(enabler.name)
        #backlog = self.factory.getEnablerBacklog(enabler.name)
        backlog = self.factory.getCoordinationBacklog(enabler.key)

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
        ws.write(row, 1, '{}'.format(agileCalendar.projectTime))
        # row += 1
        ws.write(row, 2, 'Report Date:', self.spFormats.bold_right)
        ws.write(row, 3, date.today().strftime('%d-%m-%Y'))
        #
        row += 2

        _format = self.workbook.add_format({'bold': True, 'font_size': 15, 'color': 'green'})
        ename = enabler.name
        ws.write(row, 0, 'Enabler:', self.spFormats.bold_right)
        ws.write(row, 1, ename, _format)
        row += 1
        _format = self.workbook.add_format({'bold': True, 'font_size': 15, 'bg_color': '#60C1CF'})
        ws.write(row, 0, 'Product Owner:', self.spFormats.bold_right)
        ws.write(row, 1, '{} - {}'.format(enabler.owner, enabler.leader), _format)
        ws.write(row, 2, '', _format)

        row += 1
        ws.write(row, 0, 'Work Mode:', self.spFormats.bold_right)
        ws.write(row, 1, 'Active')

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
        row += 1
        data = reporter.sprint_status
        ws.write(row, 0, 'Sprint Status', self.spFormats.red_bold_right)
        ws.write_string(row, 1, '{} Issues = {}'.format(sum(data.values()),
                                                        ' + '.join("{!s} {}".format(v, k) for (k, v) in data.items())))

        # We do not show any more the tests and errors so we comment the next 2 blocks
        # row += 1
        # ws.write(row, 0, 'Tests', self.spFormats.bold_right)
        # data = reporter.backlog.testMetrics
        # total = sum(data['OK'].values()) + sum(data['KO'].values())
        # ws.write_rich_string(row, 1,
        #                      '{0:,} Tests = {1:,}'.format(total, sum(data['OK'].values())),
        #                      self.spFormats.green, ' OK', ' + ',
        #                      '{0:,}'.format(sum(data['KO'].values())), self.spFormats.red, ' KO ')
        #
        # row += 1
        # data = reporter.errors
        # ws.write(row, 0, 'Errors', self.spFormats.bold_right)
        # ws.write_rich_string(row, 1,
        #                      '{:,} Issues = {OK:,}'.format(sum(data.values()), **data), self.spFormats.green, ' OK',
        #                      ' + '
        #                      ' {KO:,}'.format(sum(data.values()), **data), self.spFormats.red, ' KO')

        if not reporter.length:
            return

        row += 2
        chart = painter.draw_composition(reporter.issueType)
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        chart = painter.draw_status(reporter.perspective)
        ws.insert_chart(row, 1, chart, {'x_offset': 300, 'y_offset': 0})

        # Since FI-NEXT, we do not show the ERROR graphics anymore
        # chart = painter.draw_errors(reporter.errors)
        # ws.insert_chart(row, 1, chart, {'x_offset': 712, 'y_offset': 0})

        row += 15
        chart = painter.draw_sprint_burndown(reporter.burndown)
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        chart = painter.draw_sprint_status(reporter.sprint_status)
        ws.insert_chart(row, 1, chart, {'x_offset': 712, 'y_offset': 0})

        row += 15
        chart = painter.draw_evolution(reporter.implemented)
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

    def chapter(self, name):
        print("--monitor-- chapter:", name)
        _date = datetime.now().strftime("%Y%m%d-%H%M")
        filename = 'FIWARE.backlog.report.' + name + '.' + _date + '.xlsx'
        myfile = os.path.join(settings.outHome, filename)
        self.workbook = xlsxwriter.Workbook(myfile)
        self.spFormats = SpreadsheetFormats(self.workbook)

        # For each component 'xxxx' create dashboard
        # chapter = chaptersBook[name]
        component = coordinationBook['10509']
        self._enabler_dashboard(component)

        component = coordinationBook['11700']
        self._enabler_dashboard(component)

        component = coordinationBook['10401']
        self._enabler_dashboard(component)

        component = coordinationBook['10249']
        self._enabler_dashboard(component)

        component = coordinationBook['11200']
        self._enabler_dashboard(component)

        print(name, ': W:' + myfile)
        self.workbook.close()


class WorkBench:
    @staticmethod
    def report():
        print('report')
        reporter = GlobalBacklogReporter()
        coordination = settings.management
        coordination = ('Coordination')

        reporter.chapter('GlobalCoordination')

    @staticmethod
    def snapshot():
        print('snapshot')
        DataEngine.snapshot(storage=settings.inHome)

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
        print('Chosen option:', choice)
        options[choice]()
