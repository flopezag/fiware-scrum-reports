import os
import json
from kernel.Jira import JIRA
from functools import reduce
from business_analytics.analysis import Analysis


class WorkBench:
    def __init__(self, start_date=None, end_date=None):
        self.data = list()
        self.enablers = list()
        self.start_date = start_date
        self.end_date = end_date

    def analysis_data(self):
        analysis = Analysis(self.data, self.enablers)

        analysis.set_start_date(start_date=self.start_date)
        analysis.set_end_date(end_date=self.end_date)

        analysis.get_composition()
        analysis.get_status()
        analysis.get_evolution()

        return

    def snapshot(self):
        print("   Getting JIRA session")
        jira = JIRA()

        print("   Getting enablers' list")
        code_home = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_home = os.path.join(code_home, 'site_config')
        json_file = os.path.join(config_home, 'NewTrackers.json')

        with open(json_file, 'r') as f:
            distros_dict = json.load(f)

        enablers_list = list(filter(lambda x: len(x) > 0, map(lambda x: x['enablers'], distros_dict['tracker'])))
        enablers = list(map(lambda x: list(map(lambda y: y['cmp_key'], x)), enablers_list))

        # from list of lists to list
        self.enablers = reduce(lambda x, y: x + y, enablers)

        # from list of key to string of keys
        enablers = reduce(lambda x, y: x + ', ' + y, self.enablers)
        print("      " + enablers)
        enablers = '(' + enablers + ')'

        # get the data from jira
        print("   Getting data from JIRA")
        self.data.extend(jira.get_multi_component_data(enablers))
        print("      data dimension: {}".format(len(self.data)))

        return self.data
