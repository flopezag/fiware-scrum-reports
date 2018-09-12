import os
import json
from kernel.Jira import JIRA
from functools import reduce
from business_analytics.analysis import Analysis


class WorkBench:
    def __init__(self, start_date=None, end_date=None):
        self.data = list()
        self.enablers = list()
        self.enablers_per_chapter = {}
        self.chapters_name = list()

        self.start_date = start_date
        self.end_date = end_date

    def analysis_data(self):
        analysis = Analysis(self.data, self.enablers)

        analysis.set_start_date(start_date=self.start_date)
        analysis.set_end_date(end_date=self.end_date)

        # Analysis of all GEs
        analysis.get_composition()
        analysis.get_status()
        analysis.get_evolution()

        # Reduce to chapters analysis
        analysis.get_chapter_composition(self.chapters_name, self.enablers_per_chapter)
        analysis.get_chapter_status(self.chapters_name, self.enablers_per_chapter)
        analysis.get_chapter_evolution(self.chapters_name, self.enablers_per_chapter)

        # Reduce to Global analysis
        analysis.get_global_composition(self.chapters_name)
        analysis.get_global_status(self.chapters_name)
        analysis.get_global_evolution(self.chapters_name)

        return

    @staticmethod
    def mapping_chapter_enablers(chapter):
        chapter_name = chapter['name']

        if len(chapter['enablers']) == 0:
            enablers = list()
        else:
            enablers = list(map(lambda x: x['cmp_key'], chapter['enablers']))

        return dict([(chapter_name, enablers)])

    def snapshot(self):
        print("   Getting JIRA session")
        jira = JIRA()

        print("   Getting enablers' list")
        code_home = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_home = os.path.join(code_home, 'site_config')
        json_file = os.path.join(config_home, 'NewTrackers.json')

        with open(json_file, 'r') as f:
            distros_dict = json.load(f)

        enablers_per_chapter = list(map(lambda x: WorkBench.mapping_chapter_enablers(x), distros_dict['tracker']))

        for chapter in enablers_per_chapter:
            key = reduce(lambda x, y: x + y, chapter.keys())
            values = reduce(lambda x, y: x + y, chapter.values())
            self.enablers_per_chapter[key] = values
            self.enablers = self.enablers + values
            self.chapters_name.append(key)

        # from list of key to string of keys
        enablers = reduce(lambda x, y: x + ', ' + y, self.enablers)
        print("      " + enablers)
        enablers = '(' + enablers + ')'

        # get the data from jira
        print("   Getting data from JIRA")
        self.data.extend(jira.get_multi_component_data(enablers))
        print("      data dimension: {}".format(len(self.data)))

        return self.data
