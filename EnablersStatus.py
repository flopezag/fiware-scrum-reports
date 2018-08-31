import os
import re
import xlsxwriter
from datetime import datetime
from xlsxwriter.utility import xl_range
from kernel.Calendar import agileCalendar
from kernel.Settings import settings
from kernel.SheetFormats import SpreadsheetFormats
from kernel.TrackerBook import chaptersBook

__author__ = 'Manuel Escriche'


class StatusReport:
    def __init__(self, sprint):
        self.workbook = None
        self.spFormats = None
        self.sprint = sprint

    def write(self):
        ws = self.workbook.add_worksheet('Working Mode')
        ws.set_zoom(80)
        ws.set_column(0, 0, 25)
        ws.set_column(1, 1, 40)
        ws.set_column(2, 2, 60)
        ws.set_column(3, 3, 50)
        ws.set_column(4, 4, 15)
        ws.set_column(5, 5, 20)
        ws.set_column(6, 6, 60)
        row, col = 0, 0
        columns_merge = 8
        ws.merge_range(xl_range(row, 0, row, columns_merge), "Backlog's Enabler's Status", self.spFormats.chapter_title)
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
        row += 1

        for chaptername in chaptersBook:
            chapter = chaptersBook[chaptername]
            ws.write(row, 0, 'Chapter', self.spFormats.section)
            ws.write(row, 1, '{}'.format(chaptername), self.spFormats.bold)
            ws.write(row, 2, 'Leader: {}'.format(chapter.leader))
            ws.write(row, 3, 'Architect: {}'.format(chapter.architect))
            row += 1

            ws.write_row(row,
                         0,
                         ('Enabler/Tool', 'Owner-Leader', 'GE-GEI', 'Keyword', 'Mode', 'Comment'),
                         self.spFormats.column_heading
                         )

            row += 1
            for enablername in chapter.enablers:
                enabler = chapter.enablers[enablername]
                ws.write(row, 0, '{}'.format(enablername))
                ws.write(row, 1, '{}-{}'.format(enabler.owner, enabler.leader))
                ws.write(row, 2, '{}'.format(enabler.Name))
                ws.write(row, 3, '{}'.format(enabler.backlogKeyword))
                ws.write(row, 4, '{}'.format(enabler.mode))
                row += 1
            for toolname in chapter.tools:
                tool = chapter.tools[toolname]
                ws.write(row, 0, '{}'.format(toolname))
                ws.write(row, 1, '{}-{}'.format(tool.owner, tool.leader))
                ws.write(row, 2, '{}'.format(tool.name))
                ws.write(row, 3, '{}'.format(tool.backlogKeyword))
                ws.write(row, 4, '{}'.format(tool.mode))
                row += 1
            row += 1


def main():
    sprint = agileCalendar.current_sprint
    report = StatusReport(sprint)
    _sprint = re.sub(r'\.', '', sprint)
    _date = datetime.now().strftime("%Y%m%d-%H%M")

    filename = 'FIWARE.backlog.enablerStatus.sprint-' + _sprint + '.' + _date + '.xlsx'
    myfile = os.path.join(settings.outHome, filename)
    report.workbook = xlsxwriter.Workbook(myfile)
    report.spFormats = SpreadsheetFormats(report.workbook)
    report.write()
    print('W:' + myfile)
    report.workbook.close()


if __name__ == "__main__":
    print("Enabler's Status Report")
    main()
