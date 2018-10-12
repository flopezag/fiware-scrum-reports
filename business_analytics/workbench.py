import os
import json
from kernel.Jira import JIRA
from functools import reduce
from business_analytics.analysis import Analysis, Data
from business_analytics.report import Report
from business_analytics.github import Github


class WorkBench:
    def __init__(self, start_date=None, end_date=None):
        self.data_jira = list()
        self.data_github = list()
        self.enablers = list()
        self.enablers_per_chapter = {}
        self.enablers_per_name = {}
        self.chapters_name = list()

        self.start_date = start_date
        self.end_date = end_date

        self.analysis = None
        # self.data = None
        self.data_analysis = None

    def analysis_data(self):
        self.analysis = Analysis(self.data_jira, self.enablers)
        self.analysis.extend_data(self.data_github)
        self.analysis.set_start_date(start_date=self.start_date)
        self.analysis.set_end_date(end_date=self.end_date)
        self.analysis.filter_time()

        # Analysis of all GEs
        self.analysis.get_composition()
        self.analysis.get_status()
        self.analysis.get_evolution()

        # Reduce to chapters analysis
        self.analysis.get_chapter_composition(self.chapters_name, self.enablers_per_chapter)
        self.analysis.get_chapter_status(self.chapters_name, self.enablers_per_chapter)
        self.analysis.get_chapter_evolution(self.chapters_name, self.enablers_per_chapter)

        # Reduce to Global analysis
        self.analysis.get_global_composition(self.chapters_name)
        self.analysis.get_global_status(self.chapters_name)
        self.analysis.get_global_evolution(self.chapters_name)

        # Create Data structure to manage the final analysis data
        self.data_analysis = Data()

        # Counters issues type
        self.data_analysis.c_issue_type = self.analysis.c_issue_type
        self.data_analysis.c_status = self.analysis.c_status

        # Counters issues created
        self.data_analysis.c_created = self.analysis.c_created
        self.data_analysis.c_updated = self.analysis.c_updated
        self.data_analysis.c_resolved = self.analysis.c_resolved
        self.data_analysis.c_released = self.analysis.c_released

        # Counter chapter issue type
        self.data_analysis.c_chapter_issue_type = self.analysis.c_chapter_issue_type
        self.data_analysis.c_chapter_status = self.analysis.c_chapter_status

        # Counters chapter issues created
        self.data_analysis.c_chapter_created = self.analysis.c_chapter_created
        self.data_analysis.c_chapter_updated = self.analysis.c_chapter_updated
        self.data_analysis.c_chapter_resolved = self.analysis.c_chapter_resolved
        self.data_analysis.c_chapter_released = self.analysis.c_chapter_released

        # Counter global issue type
        self.data_analysis.c_global_issue_type = self.analysis.c_global_issue_type
        self.data_analysis.c_global_status = self.analysis.c_global_status

        # Counters chapter issues created
        self.data_analysis.c_global_created = self.analysis.c_global_created
        self.data_analysis.c_global_updated = self.analysis.c_global_updated
        self.data_analysis.c_global_resolved = self.analysis.c_global_resolved
        self.data_analysis.c_global_released = self.analysis.c_global_released

        # Enablers per chapter
        self.data_analysis.enabler_per_chapter = self.enablers_per_chapter
        self.data_analysis.enablers_per_name = self.enablers_per_name

    @staticmethod
    def mapping_chapter_enablers(chapter):
        chapter_name = chapter['name']

        if len(chapter['enablers']) == 0:
            enablers = list()
        else:
            enablers = list(map(lambda x: x['cmp_key'], chapter['enablers']))

        return dict([(chapter_name, enablers)])

    @staticmethod
    def mapping_enablers_name(enablers):
        if len(enablers) == 0:
            enablers = {}
        else:
            enablers = list(map(lambda x: dict([(x['cmp_key'], x['name'])]), enablers))
            enablers = dict((key, d[key]) for d in enablers for key in d)

        return enablers

    def snapshot(self):
        print("   Getting enablers' list")
        code_home = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_home = os.path.join(code_home, 'site_config')
        json_file = os.path.join(config_home, 'NewTrackers.json')

        with open(json_file, 'r') as f:
            distros_dict = json.load(f)

        self.__snapshot_jira__(distros_dict=distros_dict)
        self.__snapshot_github__(distros_dict=distros_dict)

    def __snapshot_github__(self, distros_dict):
        print("   Getting GitHub data")
        github = Github(enablers_dict=distros_dict)
        self.data_github.extend(github.get_data())
        print("\n      data dimension: {}".format(len(self.data_github)))

    def __snapshot_jira__(self, distros_dict):
        print("   Getting JIRA session")
        jira = JIRA()

        enablers_per_chapter = list(map(lambda x: WorkBench.mapping_chapter_enablers(x), distros_dict['tracker']))
        enablers_per_name = list(map(lambda x: WorkBench.mapping_enablers_name(x['enablers']), distros_dict['tracker']))
        self.enablers_per_name = dict((key, d[key]) for d in enablers_per_name for key in d)

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
        print("   Getting Jira data")
        self.data_jira.extend(jira.get_multi_component_data(enablers))
        print("      data dimension: {}".format(len(self.data_jira)))

    def report(self):
        print('   Generating excel report')
        report = Report(data=self.data_analysis,
                        enablers=self.enablers,
                        enablers_per_name=self.enablers_per_name,
                        start_date=self.start_date,
                        end_date=self.end_date)

        for chapter in self.chapters_name:
            report.chapter_report(chapter_name=chapter)

        '''
        chapters = settings.chapters

        for _chapter in chapters:
            reporter.chapter(_chapter)

        reporter.lab()
        '''

        print(report)
