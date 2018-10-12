from kernel.Calendar import calendar
from functools import reduce
import pandas as pd


class Painter:
    def __init__(self, wb, ws):
        self._wb = wb
        self._ws = ws
        self._column = 10
        self.categories = list()
        self.status = ['Foreseen', 'Working On', 'Implemented']

    def set_dates(self, start=None, end=None):
        start_month_id = calendar.currentMonth(current_date=start)[1]
        end_month_id = calendar.currentMonth(current_date=end)[1]

        start_index = calendar.timeline.index(start_month_id)
        end_index = calendar.timeline.index(end_month_id) + 1

        self.categories = calendar.timeline[start_index:end_index]

    def draw_composition(self, data):
        wb, ws = self._wb, self._ws

        chart = wb.add_chart({'type': 'pie'})
        headings = ('Type', 'Amount')

        col = self._column
        ws.write_row(0, col, headings)
        ws.write_column(1, col + 0, list(data.keys()))
        ws.write_column(1, col + 1, [data[k] for k in data])

        sheet_name = ws.get_name()
        chart.add_series({
            'name': [sheet_name, 0, col + 1],
            'categories': [sheet_name, 1, col + 0, len(data), col + 0],
            'values': [sheet_name, 1, col + 1, len(data), col + 1],
            'data_labels': {'category': True, 'value': True, 'leader_lines': True, 'percentage': True}
        })
        chart.set_title({'name': 'Backlog Composition'})
        chart.set_legend({'position': 'top'})
        chart.set_size({'width': 507, 'height': 502, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart

    def draw_status(self, data):
        wb = self._wb
        ws = self._ws

        chart = wb.add_chart({'type': 'column'})
        headings = ('Perspective', '#Items')
        keys = ('Foreseen', 'Working On', 'Implemented')

        col = self._column
        ws.write_row(0, col, headings)
        ws.write_column(1, col + 0, keys)

        try:
            ws.write_column(1, col + 1, [data['Foreseen'], data['Working On'], data['Implemented']])
        except KeyError:
            ws.write_column(1, col + 1, [0, 0, 0])

        sheet_name = ws.get_name()
        chart.add_series({
            'name': [sheet_name, 0, col + 0],
            'categories': [sheet_name, 1, col + 0, len(data), col + 0],
            'values': [sheet_name, 1, col + 1, len(data), col + 1],
            'data_labels': {'value': True}
        })

        chart.set_title({'name': 'Backlog Status'})
        chart.set_x_axis({'name': 'Perspective'})
        chart.set_y_axis({'name': '# items'})
        chart.set_legend({'none': True})
        chart.set_size({'width': 480, 'height': 502, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart

    def draw_errors(self, data):
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

        if legend:
            chart.set_legend({'position': 'top'})
        else:
            chart.set_legend({'none': True})

        chart.set_size({'width': 288, 'height': 288, 'x_scale': 1, 'y_scale': 1})
        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart

    def draw_evolution(self, created, updated, resolved, released):
        wb = self._wb
        ws = self._ws

        chart = wb.add_chart({'type': 'line'})
        headings = ('Month', 'Created', 'Resolved', 'Updated', 'Released')
        col = self._column
        ws.write_row(0, col, headings)

        ws.write_column(1, col + 0, self.categories)
        ws.write_column(1, col + 1, created)
        ws.write_column(1, col + 2, resolved)
        ws.write_column(1, col + 3, updated)
        ws.write_column(1, col + 4, released)

        sheet_name = ws.get_name()
        chart.add_series({
            'name': [sheet_name, 0, col + 1],
            'categories': [sheet_name, 1, col, len(self.categories), col],
            'values': [sheet_name, 1, col + 1, len(created), col + 1]
        })
        chart.add_series({
            'name': [sheet_name, 0, col + 2],
            'categories': [sheet_name, 1, col, len(self.categories), col],
            'values': [sheet_name, 1, col + 2, len(resolved), col + 2]
        })
        chart.add_series({
            'name': [sheet_name, 0, col + 3],
            'categories': [sheet_name, 1, col, len(self.categories), col],
            'values': [sheet_name, 1, col + 3, len(updated), col + 3]
        })
        chart.add_series({
            'name': [sheet_name, 0, col + 4],
            'categories': [sheet_name, 1, col, len(self.categories), col],
            'values': [sheet_name, 1, col + 4, len(released), col + 4]
        })

        chart.set_title({'name': 'Backlog Evolution'})
        chart.set_x_axis({'name': '# Month'})
        chart.set_y_axis({'name': '# items'})
        chart.set_legend({'position': 'top'})
        chart.set_size({'width': 1000, 'height': 291, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart

    def draw_component_sprint_status(self, cmp_type, components, data):
        wb = self._wb
        ws = self._ws
        _data = {item['name']: item['data'] for item in data}
        chart = wb.add_chart({'type': 'column', 'subtype': 'stacked'})
        status = tuple([item['name'] for item in data])
        headings = (cmp_type,) + status
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

        chart.set_title({'name': "{}s' Backlog Sprint Status".format(cmp_type)})
        chart.set_x_axis({'name': cmp_type})
        chart.set_y_axis({'name': '# items'})
        chart.set_legend({'position': 'top'})
        chart.set_size({'width': 1000, 'height': 291, 'x_scale': 1, 'y_scale': 1})

        chart.set_plotarea({'fill': {'color': '#FFFF99'}})
        chart.set_style(2)
        self._column += len(headings) + 1
        return chart

    def draw_component_status(self, cmp_type, data):
        wb = self._wb
        ws = self._ws
        chart = wb.add_chart({'type': 'column', 'subtype': 'stacked'})
        keys = list(list(data.values())[0].keys())
        headings = (cmp_type,) + tuple(keys)
        col = self._column
        ws.write_row(0, col, headings)
        ws.write_column(1, col + 0, list(data.keys()))

        for i, key in enumerate(list(data.values()), start=1):
            df = pd.DataFrame(list(key.values())).fillna(0)
            for j in range(0, len(keys)):
                ws.write_column(1, col + i + j, df.iloc[j].tolist())

        sheet_name = ws.get_name()

        for i in range(1, len(keys) + 1):  # , _status in enumerate(list(data.keys()), start=1):
            chart.add_series({
                'name': [sheet_name, 0, col + i],
                'categories': [sheet_name, 1, col + 0, len(data), col + 0],
                'values': [sheet_name, 1, col + i, len(data), col + i],
                'data_labels': {'value': True}
            })

        chart.set_title({'name': "{}s' Backlog Status".format(cmp_type)})
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

    def draw_chapters_status(self, data):
        wb = self._wb
        ws = self._ws
        invert_status = list(reversed(self.status))

        chart = wb.add_chart({'type': 'column', 'subtype': 'stacked'})
        headings = ('Chapter',) + tuple(invert_status)
        chapters = list(data.keys())

        col = self._column
        ws.write_row(0, col, headings)
        ws.write_column(1, col + 0, list(data.keys()))

        sheet_name = ws.get_name()

        df = pd.DataFrame(data).fillna(0).T
        df = df[invert_status]

        length = len(data)

        for i in range(0, len(chapters)):
            ws.write_row(i+1, col+1, df.iloc[i].tolist())

        for i in range(0, len(invert_status)):
            chart.add_series({
                'name': [sheet_name, 0, col + i + 1],
                'categories': [sheet_name, 1, col, length, col],
                'values': [sheet_name, 1, col + i + 1, length, col + i + 1],
                'data_labels': {'value': True}
            })

        chart.set_title({'name': "Chapters' Backlog Status"})
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
        invert_status = list(reversed(self.status))

        chart = wb.add_chart({'type': 'bar', 'subtype': 'stacked'})
        headings = ('Enabler',) + tuple(invert_status)

        df = pd.DataFrame(data).fillna(0).T
        df = df[invert_status]
        df = df.reindex(enablers)

        enablers = list(map(lambda x: enablers[x], enablers))
        length = len(data)

        col = self._column
        ws.write_row(0, col, headings)
        ws.write_column(1, col + 0, enablers)

        sheet_name = ws.get_name()

        for i in range(0, len(data)):
            ws.write_row(i+1, col+1, df.iloc[i].tolist())

        for i, _status in enumerate(enablers, start=1):
            chart.add_series({
                'name': [sheet_name, 0, col + i],
                'categories': [sheet_name, 1, col, length, col],
                'values': [sheet_name, 1, col + i, length, col + i],
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
