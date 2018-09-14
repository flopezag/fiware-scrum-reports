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

from xlsxwriter import Workbook
from xlsxwriter.utility import xl_range

from kernel.Calendar import agileCalendar
from kernel.Settings import settings
from kernel.SheetFormats import SpreadsheetFormats
from business_analytics.draw import Painter


class Report:

    def __init__(self, data, enablers, enablers_per_name, start_date=None, end_date=None):
        self.calendar = agileCalendar
        self.spFormats = None
        self.start = start_date  # year, month, day
        self.end = end_date  # year, month, day
        self.workbook = None
        self.spFormats = None
        self.data = data
        self.enablers = enablers
        self.enablers_per_name = enablers_per_name

    def chapter_report(self, chapter_name):
        print()
        print("--monitor-- chapter:", chapter_name)

        _date = datetime.now().strftime("%Y%m%d-%H%M")
        filename = 'FIWARE.backlog.report.' + chapter_name.partition(' ')[0] + '.' + _date + '.xlsx'
        my_file = os.path.join(settings.outHome, filename)

        self.workbook = Workbook(my_file)
        self.spFormats = SpreadsheetFormats(self.workbook)

        self._tech_chapters_dashboard()

        '''
        chapter = chaptersBook[chaptername]
        self._chapter_dashboard(chapter)
        self._coordination_dashboard(chapter.coordination)

        for _enabler in chapter.enablers:
            self._enabler_dashboard(chapter.enablers[_enabler])
        '''

        print(chapter_name, ': W:' + my_file)
        self.workbook.close()

    def _tech_chapters_dashboard(self):
        print('---> TechChapters')
        wb = self.workbook
        ws = wb.add_worksheet('Overview')

        painter = Painter(wb, ws)
        painter.set_dates(start=self.start, end=self.end)

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
        ws.write(row, 1, '{} Chapters'.format(len(self.data.c_chapter_created)))
        n_enablers = len(self.enablers)
        n_tools = 0
        n_coordination = 1
        data = (n_enablers + n_tools + n_coordination, n_enablers, n_tools, n_coordination)

        row += 1
        ws.write(row, 1, '{} Components = {} Enablers + {} Tools + {} Coordination'.format(*data))

        row += 1
        ws.write(row, 0, 'Backlog Summary:', self.spFormats.bold_right)
        ws.write(row, 1, '# Items', self.spFormats.bold_left)

        row += 1
        ws.write(row, 0, 'Composition', self.spFormats.bold_right)
        ws.write(row, 1,
                 '{} Issues = {} Epics  +  {} Features  +  {} User Stories  +  {} WorkItems  +  {} Bugs'
                 .format(
                    int(sum(self.data.c_global_issue_type.values())),
                    int(self.data.c_global_issue_type['Epic']),
                    int(self.data.c_global_issue_type['Feature']),
                    int(self.data.c_global_issue_type['Story']),
                    int(self.data.c_global_issue_type['WorkItem']),
                    int(self.data.c_global_issue_type['Bug'])
                    )
                 )

        row += 1
        ws.write(row, 0, 'Status', self.spFormats.bold_right)
        ws.write(row, 1, '{} Issues = {} Implemented  + {} Working On  +  {} Foreseen'
                         .format(
                            int(sum(self.data.c_global_status.values())),
                            int(self.data.c_global_status['Implemented']),
                            int(self.data.c_global_status['Working On']),
                            int(self.data.c_global_status['Foreseen'])
                            )
                 )

        row += 2
        chart = painter.draw_composition(self.data.c_global_issue_type)
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        chart = painter.draw_status(self.data.c_global_status)
        ws.insert_chart(row, 1, chart, {'x_offset': 520, 'y_offset': 0})

        row += 26
        chart = painter.draw_evolution(created=self.data.c_global_created,
                                       updated=self.data.c_global_updated,
                                       resolved=self.data.c_global_resolved,
                                       released=self.data.c_global_released)
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        row += 15
        chart = painter.draw_chapters_status(self.data.c_chapter_status)
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        row += 15
        chart = painter.draw_enablers_status(self.enablers_per_name, self.data.c_status)
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        row += 50
        ws.write(row, 0, '')

    '''
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

        row += 1
        reporter = EnablerReporter(enabler.name, backlog)
        data = reporter.issueType
        ws.write(row, 0, 'Composition', self.spFormats.bold_right)
        ws.write(row, 1, '{0:,} Issues = {Epic} Epics + {Feature} Features + '
                         '{Story:,} User Stories + {WorkItem:,} WorkItems + {Bug} Bugs'.format(sum(data.values()),
                                                                                               **data))

        row += 1
        data = reporter.perspective
        ws.write(row, 0, 'Status', self.spFormats.bold_right)
        ws.write(row, 1, '{0:,} Issues = {Implemented:,} Implemented  + {Working On} Working On  + '
                         ' {Foreseen} Foreseen'.format(sum(data.values()), **data))

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
            _format = \
                self.workbook.add_format({'bold': True, 'font_size': 20, 'bg_color': '#60C1CF', 'align': 'center'})

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
        ws.write(row, 0, 'Product Owner:', self.spFormats.bold_right)
        ws.write(row, 1, '{} - {}'.format(tool.owner, tool.leader), _format)
        ws.write(row, 2, '', _format)

        row += 1
        ws.write(row, 0, 'Work Mode:', self.spFormats.bold_right)
        ws.write(row, 1, tool.mode)

        row += 2
        ws.write(row, 0, 'Backlog Summary:', self.spFormats.bold_right)
        ws.write(row, 1, '# Items', self.spFormats.bold_left)

        row += 1
        reporter = ToolReporter(tool.name, backlog)
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

        row += 1
        reporter = ChapterReporter(chapter.name, backlog)
        data = reporter.issueType
        ws.write(row, 0, 'Composition', self.spFormats.bold_right)
        ws.write(row, 1, '{0:,} Issues = {Epic:,} Epics + {Feature:,} Features + '
                         '{Story:,} User Stories + {WorkItem:,} WorkItems + {Bug:,} Bugs'.format(sum(data.values()),
                                                                                                 **data))

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
        ws.write(row, 1, '{} Chapters'.format(len(self.gReporter.chapters)))
        n_enablers = sum([len(chaptersBook[chapter].enablers) for chapter in chaptersBook])
        n_tools = sum([len(chaptersBook[chapter].tools) for chapter in chaptersBook])
        n_coordination = len([chaptersBook[chapter].coordination for chapter in chaptersBook])
        data = (n_enablers + n_tools + n_coordination, n_enablers, n_tools, n_coordination)

        row += 1
        ws.write(row, 1, '{} Components = {} Enablers + {} Tools + {} Coordination'.format(*data))

        row += 1
        ws.write(row, 0, 'Backlog Summary:', self.spFormats.bold_right)
        ws.write(row, 1, '# Items', self.spFormats.bold_left)
        reporter = self.gReporter

        row += 1
        data = reporter.issueType
        ws.write(row, 0, 'Composition', self.spFormats.bold_right)
        ws.write(row, 1, '{0:,} Issues = {Epic:,} Epics + {Feature:,} Features + '
                         '{Story:,} User Stories + {WorkItem:,} WorkItems + {Bug:,} Bugs'.format(sum(data.values()),
                                                                                                 **data))

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
    '''
