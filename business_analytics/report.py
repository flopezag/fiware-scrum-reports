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
from kernel.DeploymentModel import deploymentBook
from functools import reduce


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
        self._chapter_dashboard(chapter_name)

        '''
        chapter = chaptersBook[chaptername]
        self._coordination_dashboard(chapter.coordination)
        '''
        for enabler in self.data.enabler_per_chapter[chapter_name]:
            self._enabler_dashboard(enabler)

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

    @staticmethod
    def enablers_status(enablers_per_name, status, enablers):
        a = dict()
        a[enablers_per_name[enablers]] = status[enablers]
        return a

    def _chapter_dashboard(self, chapter):
        print('------>', chapter)
        wb = self.workbook
        ws = wb.add_worksheet('{} Chapter'.format(chapter.partition(' ')[0]))
        # backlog = self.factory.getChapterBacklog(chapter.name)

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
                       "Backlog for Chapter: '{0}'".format(chapter), _heading)

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
        ws.write(row, 1, chapter, _format)

        row += 2
        if deploymentBook.roadmap[chapter]:
            ws.write(row, 0, 'Roadmap:', self.spFormats.bold_right)
            ws.write_url(row, 1, '{0}'.format(deploymentBook.roadmap[chapter]))
            row += 1

        row += 2
        ws.write(row, 0, 'Backlog Structure:', self.spFormats.bold_right)
        n_enablers = len(self.data.c_issue_type)
        ws.write(row, 1, '{} Enablers'.format(n_enablers))

        row += 1
        ws.write(row, 0, 'Backlog Summary:', self.spFormats.bold_right)
        ws.write(row, 1, '# Items', self.spFormats.bold_left)

        row += 1
        data = self.data.c_chapter_issue_type[chapter]
        ws.write(row, 0, 'Composition', self.spFormats.bold_right)
        if len(data) == 0:
            ws.write(row, 1, '0 Issues = 0 Epics + 0 Features + 0 User Stories + 0 WorkItems + 0 Bugs')
        else:
            ws.write(row, 1, '{0:,} Issues = {Epic:,} Epics + {Feature:,} Features + '
                             '{Story:,} User Stories + {WorkItem:,} WorkItems + {Bug:,} Bugs'
                             .format(sum(data.values()), **data))

        row += 1
        data = self.data.c_chapter_status[chapter]
        ws.write(row, 0, 'Status', self.spFormats.bold_right)
        if len(data) == 0:
            ws.write(row, 1, '0 Issues = 0 Implemented  + 0 Working On  + 0 Foreseen')
        else:
            ws.write(row, 1, '{0:,} Issues = {Implemented:,} Implemented  + {Working On:,} Working On  + '
                             ' {Foreseen:,} Foreseen'.format(sum(data.values()), **data))

        row += 2
        chart = painter.draw_composition(self.data.c_chapter_issue_type[chapter])
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        chart = painter.draw_status(self.data.c_chapter_status[chapter])
        ws.insert_chart(row, 1, chart, {'x_offset': 520, 'y_offset': 0})

        row += 26
        chart = painter.draw_evolution(created=self.data.c_chapter_created[chapter],
                                       updated=self.data.c_chapter_updated[chapter],
                                       resolved=self.data.c_chapter_resolved[chapter],
                                       released=self.data.c_chapter_released[chapter])
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        row += 15
        data = list(map(lambda x: self.enablers_status(self.enablers_per_name, self.data.c_status, x),
                        self.data.enabler_per_chapter[chapter]))
        if len(data) != 0:
            data = dict((key, d[key]) for d in data for key in d)  # reduce(lambda x, y: x + y, data)
            chart = painter.draw_component_status('Enabler', data)
            ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        row += 15
        ws.write(row, 0, '')

    def _enabler_dashboard(self, enabler):
        enabler_name = self.enablers_per_name[enabler]
        print('------>', enabler_name)
        wb = self.workbook
        ws = wb.add_worksheet(enabler_name)
        # backlog = self.factory.getEnablerBacklog(enabler_name)
        # backlog.sort(key=backlog.sortDict['name'])

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
                       "Backlog for Enabler: '{0}'".format(enabler_name), _heading)
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
        ws.write(row, 0, 'Backlog Summary:', self.spFormats.bold_right)
        ws.write(row, 1, '# Items', self.spFormats.bold_left)

        row += 1
        data = self.data.c_issue_type[enabler]
        ws.write(row, 0, 'Composition', self.spFormats.bold_right)
        ws.write(row, 1, '{0:,} Issues = {Epic} Epics + {Feature} Features + '
                         '{Story:,} User Stories + {WorkItem:,} WorkItems + {Bug} Bugs'
                         .format(sum(data.values()), **data))

        row += 1
        data = self.data.c_status[enabler]
        ws.write(row, 0, 'Status', self.spFormats.bold_right)
        ws.write(row, 1, '{0:,} Issues = {Implemented:,} Implemented  + {Working On} Working On  + '
                         ' {Foreseen} Foreseen'.format(sum(data.values()), **data))

        # if not reporter.length:
        #     return

        row += 2
        chart = painter.draw_composition(self.data.c_issue_type[enabler])
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        chart = painter.draw_status(self.data.c_status[enabler])
        ws.insert_chart(row, 1, chart, {'x_offset': 520, 'y_offset': 0})

        row += 26
        chart = painter.draw_evolution(created=self.data.c_created[enabler],
                                       updated=self.data.c_updated[enabler],
                                       resolved=self.data.c_resolved[enabler],
                                       released=self.data.c_released[enabler])
        ws.insert_chart(row, 1, chart, {'x_offset': 0, 'y_offset': 0})

        row += 15
        ws.write(row, 0, '')
