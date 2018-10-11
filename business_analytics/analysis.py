from collections import Counter
from datetime import datetime
from kernel.Calendar import calendar as fiware_calendar
from itertools import accumulate
from functools import reduce
import pandas as pd


class Analysis:
    def __init__(self, data, enablers):
        self.data = list(map(lambda x: Analysis.clean_data(x['fields']), data))
        self.enablers = enablers

        # Static values of data
        self.issue_type = list({'Epic', 'Feature', 'Story', 'WorkItem', 'Bug'})
        self.status_type = list({'Open', 'Impeded', 'Analysing', 'In Progress', 'Fixed', 'Rejected', 'Closed'})
        self.status_final_type = list({'Implemented', 'Working On', 'Foreseen'})

        # Counters issues type
        self.c_issue_type = {}
        self.c_status = {}

        # Counters issues created
        self.c_created = {}
        self.c_updated = {}
        self.c_resolved = {}
        self.c_released = {}

        # Counter chapter issue type
        self.c_chapter_issue_type = {}
        self.c_chapter_status = {}

        # Counters chapter issues created
        self.c_chapter_created = {}
        self.c_chapter_updated = {}
        self.c_chapter_resolved = {}
        self.c_chapter_released = {}

        # Counter global issue type
        self.c_global_issue_type = {}
        self.c_global_status = {}

        # Counters chapter issues created
        self.c_global_created = {}
        self.c_global_updated = {}
        self.c_global_resolved = {}
        self.c_global_released = {}

        self.calendar_book = fiware_calendar.monthBook
        self.sprints_month = fiware_calendar.pastMonths

        self.start_date_index = 0
        self.end_date_index = len(self.sprints_month)

    def extend_data(self, data):
        self.data = self.data + data

    def set_start_date(self, start_date):
        start_month_id = fiware_calendar.currentMonth(current_date=start_date)[1]
        self.start_date_index = fiware_calendar.timeline.index(start_month_id)

    def set_end_date(self, end_date):
        end_month_id = fiware_calendar.currentMonth(current_date=end_date)[1]
        self.end_date_index = fiware_calendar.timeline.index(end_month_id) + 1

    def filter_time(self):
        # Now from this data we have to see what is the calendar date
        date = [self.calendar_book[self.sprints_month[x]]
                for x in range(self.start_date_index, self.end_date_index + 1)]

        self.data = list(filter(lambda x: x['created'] in date, self.data))

    @staticmethod
    def format_datetime(a_datetime, a_format):
        if a_datetime is None:
            result = None
        else:
            result = datetime.strptime(a_datetime, a_format)
            result = '{:02d}-{}'.format(result.month, result.year)

        return result

    @staticmethod
    def format_datetime_1(a_datetime, a_format):
        if len(a_datetime) == 0:
            result = None
        else:
            result = datetime.strptime(a_datetime[0]['releaseDate'], a_format)
            result = '{:02d}-{}'.format(result.month, result.year)

        return result

    @staticmethod
    def clean_data(enabler):
        a_dict = dict([
            ("issuetype", enabler['issuetype']['name']),
            ("component_name", enabler['components'][0]['name']),
            ("component_id", enabler['components'][0]['id']),
            ("status", enabler['status']['name']),
            ("created", Analysis.format_datetime(enabler['created'], '%Y-%m-%dT%H:%M:%S.%f%z')),
            ("updated", Analysis.format_datetime(enabler['updated'], '%Y-%m-%dT%H:%M:%S.%f%z')),
            ("resolved", Analysis.format_datetime(enabler['resolutiondate'], '%Y-%m-%dT%H:%M:%S.%f%z')),
            ("released", Analysis.format_datetime_1(enabler['fixVersions'], '%Y-%m-%d'))
        ])

        return a_dict

    @staticmethod
    def counter_issue(issue_type, field, component_id, data):
        aux = dict(Counter(map(lambda y: y[field], filter(lambda z: z['component_id'] == component_id, data))))

        for issue in issue_type:
            try:
                aux[issue]
            except KeyError:
                aux[issue] = 0

        return aux

    def counter_issue_type(self, component_id):
        aux = Analysis.counter_issue(self.issue_type, 'issuetype', component_id, self.data)
        return {component_id: aux}

    def counter_status(self, component_id):
        aux = Analysis.counter_issue(self.status_type, 'status', component_id, self.data)

        perspective = dict()
        perspective['Implemented'] = aux['Closed']
        perspective['Working On'] = aux['Analysing'] + aux['In Progress'] + aux['Fixed'] + aux['Rejected']
        perspective['Foreseen'] = aux['Open'] + aux['Impeded']

        return {component_id: perspective}

    def get_composition(self):
        print("      Counting Type of Issues")
        c_issue_type = list(map(lambda x: self.counter_issue_type(x), self.enablers))
        self.c_issue_type = reduce(lambda a, b: dict(a, **b), c_issue_type)

    def get_status(self):
        print("      Counting Status of Issues")
        c_status = list(map(lambda x: self.counter_status(x), self.enablers))
        self.c_status = reduce(lambda x, y: dict(x, **y), c_status)

    def counter_datetime(self, component_id, field):
        aux = Counter(map(lambda y: y[field], filter(lambda z: z['component_id'] == component_id, self.data)))

        aux = list(accumulate(map(lambda x: aux[self.calendar_book[x]], self.sprints_month)))

        aux = aux[self.start_date_index:self.end_date_index]

        return {component_id: aux}

    def get_evolution(self):
        print("      Counting different dates (created, updated, resolved, and released)")
        aux = list(map(lambda x: self.counter_datetime(x, 'created'), self.enablers))
        self.c_created = reduce(lambda a, b: dict(a, **b), aux)

        aux = list(map(lambda x: self.counter_datetime(x, 'updated'), self.enablers))
        self.c_updated = reduce(lambda a, b: dict(a, **b), aux)

        aux = list(map(lambda x: self.counter_datetime(x, 'resolved'), self.enablers))
        self.c_resolved = reduce(lambda a, b: dict(a, **b), aux)

        aux = list(map(lambda x: self.counter_datetime(x, 'released'), self.enablers))
        self.c_released = reduce(lambda a, b: dict(a, **b), aux)

    @staticmethod
    def reduce_chapter(a_dict, issue_type, data):
        aux = {}

        if len(data) != 0:
            dataframe = list(map(lambda y: a_dict[y], data))

            df = pd.DataFrame(dataframe)

            aux = list(map(lambda x: dict([(x, df[x].sum().item())]), issue_type))

            aux = reduce(lambda a, b: dict(a, **b), aux)

        return aux

    @staticmethod
    def reduce_chapter_evolution(a_dict, data):
        aux = list()

        if len(data) != 0:
            dataframe = list(map(lambda y: a_dict[y], data))

            df = pd.DataFrame(dataframe)

            aux = df.sum().tolist()

        return aux

    def get_chapter_composition(self, chapters_name, enabler_per_chapter):
        aux = list(
            map(
                lambda x:
                    dict([(x, Analysis.reduce_chapter(self.c_issue_type, self.issue_type, enabler_per_chapter[x]))]),
                chapters_name
            ))

        self.c_chapter_issue_type = reduce(lambda a, b: dict(a, **b), aux)

    def get_chapter_status(self, chapters_name, enabler_per_chapter):
        aux = list(
            map(
                lambda x:
                    dict([(x, Analysis.reduce_chapter(self.c_status, self.status_final_type, enabler_per_chapter[x]))]),
                chapters_name
            ))

        self.c_chapter_status = reduce(lambda a, b: dict(a, **b), aux)

    def get_chapter_evolution(self, chapters_name, enabler_per_chapter):
        aux = list(
            map(
                lambda x:
                    dict([(x, Analysis.reduce_chapter_evolution(self.c_created, enabler_per_chapter[x]))]),
                chapters_name
            ))

        self.c_chapter_created = reduce(lambda a, b: dict(a, **b), aux)

        aux = list(
            map(
                lambda x:
                    dict([(x, Analysis.reduce_chapter_evolution(self.c_updated, enabler_per_chapter[x]))]),
                chapters_name
            ))

        self.c_chapter_updated = reduce(lambda a, b: dict(a, **b), aux)

        aux = list(
            map(
                lambda x:
                    dict([(x, Analysis.reduce_chapter_evolution(self.c_released, enabler_per_chapter[x]))]),
                chapters_name
            ))

        self.c_chapter_released = reduce(lambda a, b: dict(a, **b), aux)

        aux = list(
            map(
                lambda x:
                    dict([(x, Analysis.reduce_chapter_evolution(self.c_resolved, enabler_per_chapter[x]))]),
                chapters_name
            ))

        self.c_chapter_resolved = reduce(lambda a, b: dict(a, **b), aux)

    def get_global_composition(self, chapters_name):
        dataframe = list(map(lambda y: self.c_chapter_issue_type[y], chapters_name))

        df = pd.DataFrame(dataframe)

        aux = list(map(lambda x: dict([(x, df[x].sum().item())]), self.issue_type))

        self.c_global_issue_type = reduce(lambda a, b: dict(a, **b), aux)

    def get_global_status(self, chapters_name):
        dataframe = list(map(lambda y: self.c_chapter_status[y], chapters_name))

        df = pd.DataFrame(dataframe)

        aux = list(map(lambda x: dict([(x, df[x].sum().item())]), self.status_final_type))

        self.c_global_status = reduce(lambda a, b: dict(a, **b), aux)

    def get_global_evolution(self, chapters_name):
        dataframe = list(map(lambda y: self.c_chapter_created[y], chapters_name))
        df = pd.DataFrame(dataframe)
        self.c_global_created = df.sum().tolist()

        dataframe = list(map(lambda y: self.c_chapter_updated[y], chapters_name))
        df = pd.DataFrame(dataframe)
        self.c_global_updated = df.sum().tolist()

        dataframe = list(map(lambda y: self.c_chapter_resolved[y], chapters_name))
        df = pd.DataFrame(dataframe)
        self.c_global_resolved = df.sum().tolist()

        dataframe = list(map(lambda y: self.c_chapter_released[y], chapters_name))
        df = pd.DataFrame(dataframe)
        self.c_global_released = df.sum().tolist()


class Data:
    def __init__(self):
        # Static values of data
        self.issue_type = list({'Epic', 'Feature', 'Story', 'WorkItem', 'Bug'})
        self.status_type = list({'Open', 'Impeded', 'Analysing', 'In Progress', 'Fixed', 'Rejected', 'Closed'})
        self.status_final_type = list({'Implemented', 'Working On', 'Foreseen'})

        # Counters issues type
        self.c_issue_type = {}
        self.c_status = {}

        # Counters issues created
        self.c_created = {}
        self.c_updated = {}
        self.c_resolved = {}
        self.c_released = {}

        # Counter chapter issue type
        self.c_chapter_issue_type = {}
        self.c_chapter_status = {}

        # Counters chapter issues created
        self.c_chapter_created = {}
        self.c_chapter_updated = {}
        self.c_chapter_resolved = {}
        self.c_chapter_released = {}

        # Counter global issue type
        self.c_global_issue_type = {}
        self.c_global_status = {}

        # Counters chapter issues created
        self.c_global_created = {}
        self.c_global_updated = {}
        self.c_global_resolved = {}
        self.c_global_released = {}

        self.calendar_book = fiware_calendar.monthBook
        self.sprints_month = fiware_calendar.pastMonths

        self.start_date_index = 0
        self.end_date_index = len(self.sprints_month)
