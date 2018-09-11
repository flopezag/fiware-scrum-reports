from collections import Counter
from datetime import datetime
from kernel.Calendar import calendar as fiware_calendar
from itertools import accumulate


class Analysis:
    def __init__(self, data, enablers):
        self.data = list(map(lambda x: Analysis.clean_data(x['fields']), data))
        self.enablers = enablers
        self.issue_type = list({'Epic', 'Feature', 'Story', 'WorkItem', 'Bugs'})
        self.status_type = list({'Open', 'Impeded', 'Analysing', 'In Progress', 'Fixed', 'Rejected', 'Closed'})

        self.c_issue_type = list()
        self.c_status = list()

        self.c_created = list()
        self.c_updated = list()
        self.c_resolved = list()
        self.c_released = list()

        self.calendar_book = fiware_calendar.monthBook
        self.sprints_month = fiware_calendar.pastMonths

        self.start_date_index = 0
        self.end_date_index = len(self.sprints_month)

    def set_start_date(self, start_date):
        start_month_id = fiware_calendar.currentMonth(current_date=start_date)[1]
        self.start_date_index = fiware_calendar.timeline.index(start_month_id)

    def set_end_date(self, end_date):
        end_month_id = fiware_calendar.currentMonth(current_date=end_date)[1]
        self.end_date_index = fiware_calendar.timeline.index(end_month_id) + 1

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
        self.c_issue_type = list(map(lambda x: self.counter_issue_type(x), self.enablers))

    def get_status(self):
        print("      Counting Status of Issues")
        self.c_status = list(map(lambda x: self.counter_status(x), self.enablers))

    def counter_datetime(self, component_id, field):
        aux = Counter(map(lambda y: y[field], filter(lambda z: z['component_id'] == component_id, self.data)))

        aux = list(accumulate(map(lambda x: aux[self.calendar_book[x]], self.sprints_month)))

        aux = aux[self.start_date_index:self.end_date_index]

        return {component_id: aux}

    def get_evolution(self):
        print("      Counting different dates (created, updated, resolved, and released)")
        self.c_created = list(map(lambda x: self.counter_datetime(x, 'created'), self.enablers))
        self.c_updated = list(map(lambda x: self.counter_datetime(x, 'updated'), self.enablers))
        self.c_resolved = list(map(lambda x: self.counter_datetime(x, 'resolved'), self.enablers))
        self.c_released = list(map(lambda x: self.counter_datetime(x, 'released'), self.enablers))

        return
