import abc
import re
from collections import defaultdict, OrderedDict
from kernel.IssuesModel import backlogIssuesModel as entryModel
from kernel.IssuesWorkflow import issuesWorkflow as entryWorkflow
from kernel.Calendar import agileCalendar
from kernel.TrackerBook import trackersBookByName, trackersBookByKey
from kernel.ComponentsBook import enablersBookByKey, toolsBookByKey, coordinationBookByKey

__author__ = "Manuel Escriche <mev@tid.es>"


class BacklogItemRule(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, name):
        self.name = name
        self.description = defaultdict(str)
    @property
    def status(self): return '--> Item status: NT= no test done, OK= test passed; KO= test not passed'

    @abc.abstractmethod
    def __call__(self, *args, **kwargs):
        raise NotImplementedError()

    def __iter__(self):
        for key in sorted(self.description.keys()): yield key
    keys = __iter__

    def values(self):
        for key in self.description.keys(): yield self.description[key]

    def items(self):
        for key in self.description.keys(): yield (key, self.description[key])

    def __getitem__(self, item): return self.description[item]

class BasicFieldsBacklogTest(BacklogItemRule):
    def __init__(self, name):
        super().__init__(name)
        _key = lambda i: '{0}.{1}'.format(name, i)
        self.description[_key(1)] = 'Test for valid project: FIWARE'
        self.description[_key(2)] = 'Test for valid entry types: {0}'.format(entryModel.types)
        self.description[_key(3)] = 'Test for valid tracker'
        self.description[_key(4)] = 'Test for valid component'
        self.description[_key(5)] = 'Test for valid status: {0}'.format(entryWorkflow.status)
        self.description[_key(6)] = 'Test for valid time slot (fix version field)'

    def _rule_valid_project(self, item):
        return True if item.project == 'FIWARE' else False

    def _rule_valid_issueType(self, item):
        return True if item.issueType in entryModel.types else False

    def _rule_valid_tracker(self, item):
        return True if item.tracker in trackersBookByKey else False

    def _rule_valid_enabler(self, item):
        if not item.component: return False
        if item.component in coordinationBookByKey: return True
        if item.component in enablersBookByKey: return True
        if item.component in toolsBookByKey: return True
        return False

    def _rule_valid_status(self, item):
        return True if item.status in entryWorkflow.status else False

    def _rule_valid_timeSlot(self, item):
        return True if item.nVersions <= 1 else False

    def __call__(self, item):
        _key = lambda i: '{0}.{1}'.format(self.name, i)
        output = defaultdict(str)
        output[_key(1)] = 'OK' if self._rule_valid_project(item) else 'KO'
        output[_key(2)] = 'OK' if self._rule_valid_issueType(item) else 'KO'
        output[_key(3)] = 'OK' if self._rule_valid_tracker(item) else 'KO'
        output[_key(4)] = 'OK' if output[_key(3)] == 'OK' and self._rule_valid_enabler(item) else 'KO'
        output[_key(5)] = 'OK' if self._rule_valid_status(item) else 'KO'
        output[_key(6)] = 'OK' if self._rule_valid_timeSlot(item) else 'KO'
        status = 'OK' if all(value == 'OK' for value in output.values()) else 'KO'
        item.test.test[self.name] = output
        item.test.status[self.name] = status
        return


class TimeFrameBacklogTest(BacklogItemRule):
    def __init__(self, name):
        super().__init__(name)
        _key = lambda i: '{0}.{1}'.format(self.name, i)
        self.description[_key(1)] = 'Test for time slot structure: Release x.y ; Sprint x.y.x'
        self.description[_key(2)] = 'Test for time slot meaningful for FI-WARE calendar'
        self.description[_key(3)] = 'Test for time slot consistency according to issue type'
        self._sprint_pattern = re.compile(r'^Sprint\s\d[.]\d[.]\d$')
        self._release_pattern = re.compile(r'^Release\s\d[.]\d$')

    def _filter_excluded(self, item):
        if item.test.status['BasicField'] == 'KO': return True
        return False

    def _rule_structure(self, item):
        if item.timeSlot == 'Unscheduled': return True
        if re.match(self._release_pattern, item.timeSlot): return True
        if re.match(self._sprint_pattern, item.timeSlot): return True
        return False

    def _rule_valid_timeframe(self, item):
        assert self._rule_structure(item), 'wrong structure in timeframe'
        if item.timeSlot == 'Unscheduled': return True
        if agileCalendar.isValidRelease(item.timeSlot): return True
        if agileCalendar.isValidSprint(item.timeSlot): return True
        return False

    def _rule_consistent_entryType_timeframe(self, item):
        assert self._rule_valid_timeframe(item), 'invalid timeframe'
        if item.timeSlot == 'Unscheduled': return True
        if item.issueType in entryModel.shortTermTypes:
            return True if agileCalendar.isValidSprint(item.timeSlot) else False
        elif item.issueType in entryModel.midTermTypes:
            return True if agileCalendar.isValidRelease(item.timeSlot) else False
        elif item.issueType in entryModel.longTermTypes:
            return True if item.timeSlot == 'Unscheduled' else False

    def __call__(self, item):
        _key = lambda i: '{0}.{1}'.format(self.name, i)
        if self._filter_excluded(item):
            item.test.status[self.name] = 'NT'
            return
        output = defaultdict(str)
        output[_key(1)] = 'OK' if self._rule_structure(item) else 'KO'
        if output[_key(1)] == 'OK':
            output[_key(2)] = 'OK' if self._rule_valid_timeframe(item) else 'KO'
            if output[_key(2)] == 'OK':
                output[_key(3)] = 'OK' if self._rule_consistent_entryType_timeframe(item) else 'KO'
        status = 'OK' if all(value == 'OK' for value in output.values()) else 'KO'
        item.test.test[self.name] = output
        item.test.status[self.name] = status
        return


class StatusBacklogTest(BacklogItemRule):
    def __init__(self, name):
        super().__init__(name)
        _key = lambda i: '{0}.{1}'.format(self.name, i)
        self.description[_key(1)] = 'Test for status - consistency with issue type'
        self.description[_key(2)] = 'Test for status - consistency with time slot'
        self.description[_key(3)] = 'Test for status - consistency with calendar'
        self.description[_key(4)] = "Test for status - close dates consistency - it's a forge error"
        #self.description[_key(4)] = '--> test for status - hierarchy consistency'

    def _filter_excluded(self, item):
        if item.test.status['BasicField'] == 'KO': return True
        if item.test.status['TimeFrame'] == 'KO': return True
        return False

    def _rule_status_entryType_consistency(self, item):
        return True
        #if item.issueType in entryModel.longTermTypes: return True
        #return False if item.issueType in entryModel.longTermTypes \
        #    and item.status not in (entryWorkflow.defined + entryWorkflow.closed) else  True

    def _rule_status_timeFrame_consistency(self, item):
        if item.issueType in entryModel.longTermTypes: return True
        if item.status in entryWorkflow.defined: return True
        return True if item.status not in entryWorkflow.defined and item.timeSlot != 'Unscheduled'else False

    def _rule_status_calendar_consistency(self, item):
        if item.issueType in entryModel.longTermTypes:
            return True

        if item.status in entryWorkflow.defined and item.timeSlot == 'Unscheduled':
            return True

        if item.status in entryWorkflow.future and item.nTimeSlot in agileCalendar.futureTimeSlots:
            return True

        if item.status in entryWorkflow.present and item.nTimeSlot in agileCalendar.currentTimeSlots():
            return True

        if item.status in entryWorkflow.past and item.nTimeSlot in agileCalendar.pastTimeSlots:
            return True

        return False

    def _rule_status_dates_consistency(self, item):
        # activate whenever needed to check close dates
        #return False if item.status in entryWorkflow.resolved and not self.__calendar.isProjectDate(item.close_date) else True
        return True

    def __call__(self, item):
        _key = lambda i: '{0}.{1}'.format(self.name, i)
        if self._filter_excluded(item):
            item.test.status[self.name] = 'NT'
            return
        output = defaultdict(str)
        output[_key(1)] = 'OK' if self._rule_status_entryType_consistency(item) else 'KO'
        if output[_key(1)] == 'OK':
            output[_key(2)] = 'OK' if self._rule_status_timeFrame_consistency(item) else 'KO'
            if output[_key(2)] == 'OK':
                output[_key(3)] = 'OK' if self._rule_status_calendar_consistency(item) else 'KO'
        # output[_key(4)] = 'OK' if output[_key(3)] == 'OK' and self.__rule_status_dates_consistency(item) else 'KO'
        status = 'OK' if all(value == 'OK' for value in output.values()) else 'KO'
        item.test.test[self.name] = output
        item.test.status[self.name] = status
        return

class ReferenceBacklogTest(BacklogItemRule):
    def __init__(self, name):
        super().__init__(name)
        pattern = "(<project>\w+)[.](<entry>\w+)[.](<chapter>\w+)[.](<keyword>[a-zA-Z0-9_\-]+)[.](<item>[a-zA-Z0-9_\-]+([.][a-zA-Z0-9_\-]+)*)"
        self._filter = re.compile(r'^(?P<project>\w+)[.](?P<entry>\w+)[.](?P<chapter>\w+)[.](?P<keyword>[a-zA-Z0-9_\-]+)[.](?P<item>[a-zA-Z0-9_\-]+([.][a-zA-Z0-9_\-]+)*$)')
        _key = lambda i: '{0}.{1}'.format(self.name, i)
        self.description[_key(1)] = 'Test for reference - Not enough fields FIWARE.<issueType>.<chapter>.<GE-GEI keyword>.<item>'
        self.description[_key(2)] = 'Test for reference - 1st field: FIWARE'
        self.description[_key(3)] = "Test for reference - 2nd field: entry type"
        self.description[_key(4)] = "Test for reference - 3rd field: chapter"
        self.description[_key(5)] = "Test for reference - 4th field: GE-GEI keyword"
        self.description[_key(6)] = "Test for reference - 5th field: item pattern is wrong"
        self.description[_key(7)] = "Test for reference - 5th field for work items is <object>.<action>"

    def _filter_excluded(self, item):
        if item.test.status['BasicField'] == 'KO': return True
        return False
    def _rule_name_pattern(self, item):
        return True if len(item.reference.split('.')) >= 5 else False
    def _rule_project_consistency(self, item):
        project = item.reference.split('.')[0]
        return True if re.match('\w+', project) and project == item.project else False
    def _rule_entryType_consistency(self, item):
        entryType = item.reference.split('.')[1]
        return True if re.match('\w+', entryType) and entryType == item.issueType else False
    def _rule_chapter_consistency(self, item):
        trackername = item.reference.split('.')[2]
        if not trackername in trackersBookByName: return False
        tracker = trackersBookByName[trackername]
        return True if re.match('\w+', trackername) and trackername == tracker.name else False
    def _rule_keyword_consistency(self, item):
        keyword = item.reference.split('.')[3]
        if not re.match('[a-zA-Z0-9_\-]+', keyword): return False
        if item.component in coordinationBookByKey:
            return True if keyword == 'Coordination' else False
        if item.component in enablersBookByKey:
            enabler = enablersBookByKey[item.component]
            return True if keyword in (enabler.backlogKeyword, 'Bundle') else False
        if item.component in toolsBookByKey:
            tool = toolsBookByKey[item.component]
            return True if keyword == tool.backlogKeyword else False
        return False
    def _rule_item_pattern(self, item):
        chunks = item.reference.split('.')
        item = '.'.join(chunks[4:])
        if not re.match('[a-zA-Z0-9_\-]+([.][a-zA-Z0-9_\-]+)*$', item): return False
        for chunk in chunks[4:]:
            if not re.match('[A-Z0-9].', chunk): return False
        else: return True
    def _rule_item_workitem(self, item):
        assert item.issueType == entryModel.workitem
        chunks = item.reference.split('.')
        #item = '.'.join(chunks[4:])
        return True if len(chunks) >= 6 else False


    def __call__(self, item):
        _key = lambda i: '{0}.{1}'.format(self.name, i)
        if self._filter_excluded(item):
            item.test.status[self.name] = 'NT'
            return
        output = defaultdict(str)
        output[_key(1)] = 'OK' if self._rule_name_pattern(item) else 'KO'
        if output[_key(1)] == 'OK':
            output[_key(2)] = 'OK' if self._rule_project_consistency(item) else 'KO'
            output[_key(3)] = 'OK' if self._rule_entryType_consistency(item) else 'KO'
            output[_key(4)] = 'OK' if self._rule_chapter_consistency(item) else 'KO'
            output[_key(5)] = 'OK' if self._rule_keyword_consistency(item) else 'KO'
            output[_key(6)] = 'OK' if self._rule_item_pattern(item) else 'KO'
            if item.issueType == entryModel.workitem:
                output[_key(7)] = 'OK' if self._rule_item_workitem(item) else 'KO'

        status = 'OK' if all(value == 'OK' for value in output.values()) else 'KO'
        item.test.test[self.name] = output
        item.test.status[self.name] = status
        return

class HierarchyBacklogTest(BacklogItemRule):
    def __init__(self, name):
        super().__init__(name)
        _key = lambda i: '{0}.{1}'.format(self.name, i)
        self.description[_key(1)] = 'Test for Hierarchy - epics missing features as sons'
        self.description[_key(2)] = 'Test for Hierarchy - status inconsistency among epic and its features'

        self.description[_key(3)] = 'Test for Hierarchy - features missing epics as parent'
        self.description[_key(4)] = 'Test for Hierarchy - status inconsistency among feature and its epics'

        self.description[_key(5)] = 'Test for Hierarchy - features missing stories as sons'
        self.description[_key(6)] = 'Test for Hierarchy - status inconsistency among features and its stories'

        self.description[_key(7)] = 'Test for Hierarchy - stories missing a feature as parent'
        self.description[_key(8)] = 'Test for Hierarchy - status inconsistency among story and its features'


    def _filter_excluded(self, item):
        #print(item.status, item.resolution)
        if item.test.status['BasicField'] == 'KO': return True
        if item.test.status['Reference'] == 'KO': return True
        if item.resolution == 'Dismissed': return True
        return False

    def _rule_epics_with_features(self, item):
        featureSons = len([_item  for _item in item.sons if _item.issueType in entryModel.midTermTypes]) if item.sons else 0
        if item.status in entryWorkflow.defined and not featureSons: return True
        return True if  featureSons > 0  else False
    def _rule_epics_with_features_status(self, item):
        if not item.sons:
            return True if item.status in entryWorkflow.defined else False
        open_sons = all([_item.status in entryWorkflow.defined
                            for _item in item.sons if _item.issueType in entryModel.midTermTypes])
        if open_sons and item.status in entryWorkflow.defined: return True
        closed_sons = all([_item.status in entryWorkflow.closed
                            for _item in item.sons if _item.issueType in entryModel.midTermTypes])
        if closed_sons and item.status in entryWorkflow.started: return True
        started_sons = any([_item.status in entryWorkflow.started
                            for _item in item.sons if _item.issueType in entryModel.midTermTypes])
        return True if item.status in entryWorkflow.onProcess and started_sons else False

    def _rule_features_with_epics(self, item):
        epicsFather = len([_item  for _item in item.father if _item.issueType in entryModel.longTermTypes]) if item.father else 0
        return True if epicsFather > 0 else False
    def _rule_features_with_epics_status(self, item):
        if not item.father:
            return True if item.status in entryWorkflow.defined else False
        open_fathers = all([_item.status in entryWorkflow.defined
                            for _item in item.father if _item.issueType in entryModel.longTermTypes])
        if open_fathers:
            return True if item.status in entryWorkflow.defined else False
        closed_fathers = all([_item.status in entryWorkflow.closed
                            for _item in item.father if _item.issueType in entryModel.longTermTypes])
        if closed_fathers:
            return True if item.status in entryWorkflow.closed else False
        return True

    def _rule_features_with_stories(self, item):
        storySons = len([_item  for _item in item.sons if _item.issueType in entryModel.shortTermTypes]) if item.sons else 0
        if item.status in entryWorkflow.defined and not storySons: return True
        return True if  storySons > 0  else False

    def _rule_features_with_stories_status(self, item):
        if not item.sons:
            return True if item.status in entryWorkflow.defined else False
        open_sons = all([_item.status in entryWorkflow.defined
                            for _item in item.sons if _item.issueType in entryModel.story])
        if open_sons and item.status in entryWorkflow.defined: return True
        closed_sons = all([_item.status in entryWorkflow.closed
                            for _item in item.sons if _item.issueType in entryModel.story])
        if closed_sons and item.status in entryWorkflow.started: return True
        started_sons = any([_item.status in entryWorkflow.started
                            for _item in item.sons if _item.issueType in entryModel.story])
        return True if item.status in entryWorkflow.onProcess and started_sons else False

    def _rule_stories_with_features(self, item):
        featureFathers = len([_item for _item in item.father if _item.issueType in entryModel.midTermTypes]) if item.father else 0
        return True if featureFathers > 0 else False
    def _rule_stories_with_features_status(self, item):
        if not item.father:
            return True if item.status in entryWorkflow.defined else False

        open_fathers = all([_item.status in entryWorkflow.defined
                            for _item in item.father if _item.issueType in entryModel.midTermTypes])
        if open_fathers:
            return True if item.status in entryWorkflow.defined else False
        closed_fathers = all([_item.status in entryWorkflow.closed
                            for _item in item.father if _item.issueType in entryModel.midTermTypes])
        if closed_fathers:
             return True if item.status in entryWorkflow.closed else False
        return True

    def __call__(self, item):
        _key = lambda i: '{0}.{1}'.format(self.name, i)
        if self._filter_excluded(item):
            item.test.status[self.name] = 'NT'
            return
        _chunks = item.reference.split('.')
        output = defaultdict(str)
        if item.issueType in entryModel.longTermTypes:
            output[_key(1)] = 'OK' if self._rule_epics_with_features(item) else 'KO'
            output[_key(2)] = 'OK' if self._rule_epics_with_features_status(item) else 'KO'

        if item.issueType in entryModel.midTermTypes and len(_chunks) > 5:
            output[_key(3)] = 'OK' if self._rule_features_with_epics(item) else 'KO'
            output[_key(4)] = 'OK' if self._rule_features_with_epics_status(item) else 'KO'
            output[_key(5)] = 'OK' if self._rule_features_with_stories(item) else 'KO'
            output[_key(6)] = 'OK' if self._rule_features_with_stories_status(item) else 'KO'

        if item.issueType in entryModel.midTermTypes and len(_chunks) == 5:
            output[_key(5)] = 'OK' if self._rule_features_with_stories(item) else 'KO'
            output[_key(6)] = 'OK' if self._rule_features_with_stories_status(item) else 'KO'

        if item.issueType in entryModel.story:
            output[_key(7)] = 'OK' if self._rule_stories_with_features(item) else 'KO'
            output[_key(8)] = 'OK' if self._rule_stories_with_features_status(item) else 'KO'
        status = 'OK' if all(value == 'OK' for value in output.values()) else 'KO'
        item.test.test[self.name] = output
        item.test.status[self.name] = status
        return

class ItemDescriptionBacklogTest(BacklogItemRule):
    def __init__(self, name):
        super().__init__(name)
        self._pattern = r'\w+'
        _key = lambda i: '{0}.{1}'.format(self.name, i)
        self.description[_key(1)] = "Test for Open Description - right structure: Goal, Description and Rational"
        self.description[_key(2)] = "Test for Open Description - less than 10 words in goal field"
        self.description[_key(3)] = "Test for Open Description - less than 30 words in description field"
        self.description[_key(4)] = "Test for Open Description - less than 20 words in rational field"
        self.description[_key(5)] = "Test for Open Description - more than 250 words in record"

    def _filter_excluded(self, item):
        if item.test.status['BasicField'] == 'KO': return True
        if item.entryType in entryModel.private: return True
        return False
    def _rule_right_description_structure(self, item):
        if not item.description.goal: return False
        if not item.description.description: return False
        if not item.description.rationale: return False
        return True
    def _rule_proper_goal_size(self, item):
        return True if item.description.size('Goal') >= 10 else False
    def _rule_proper_description_size(self, item):
        return True if item.description.size('Description') >= 30 else False
    def _rule_proper_rationale_size(self, item):
        return True if item.description.size('Rationale') >= 20 else False
    def _rule_proper_record_size(self, item):
        return True if item.description.NSize <= 250 else False

    def __call__(self, item):
        _key = lambda i: '{0}.{1}'.format(self.name, i)
        if self._filter_excluded(item):
            item.test.status[self.name] = 'NT'
            return

        output = defaultdict(str)
        output[_key(1)] = 'OK' if self._rule_right_description_structure(item) else 'KO'
        if output[_key(1)] == 'OK':
            output[_key(2)] = 'OK' if self._rule_proper_goal_size(item) else 'KO'
            output[_key(3)] = 'OK' if self._rule_proper_description_size(item) else 'KO'
            output[_key(4)] = 'OK' if self._rule_proper_rationale_size(item) else 'KO'
        output[_key(5)] = 'OK' if self._rule_proper_record_size(item) else 'KO'

        status = 'OK' if all(value == 'OK' for value in output.values()) else 'KO'

        item.test.test[self.name] = output
        item.test.status[self.name] = status
        return

class BacklogTestBook():
    def __init__(self):
        self._store = OrderedDict()
        criteria = 'BasicField'
        self._store[criteria] = BasicFieldsBacklogTest(criteria)
        criteria = 'TimeFrame'
        self._store[criteria] = TimeFrameBacklogTest(criteria)
        criteria = 'Status'
        self._store[criteria] = StatusBacklogTest(criteria)
        criteria = 'Reference'
        self._store[criteria] = ReferenceBacklogTest(criteria)
        criteria = 'Hierarchy'
        self._store[criteria] = HierarchyBacklogTest(criteria)
        #criteria = 'Description'
        #self._store[criteria] = ItemDescriptionBacklogTest(criteria)

    @property
    def store(self):
        return self._store
    def __iter__(self):
        for rule in self._store.keys(): yield rule
    keys = __iter__
    def values(self):
        for rule in self._store.keys(): yield self._store[rule]
    def items(self):
        for rule in self._store.keys(): yield (rule, self._store[rule])
    def __getitem__(self, rule): return self._store[rule]
    def __len__(self): return len(self._store)


class Reviewer:
    def __init__(self):
        self.testBook = BacklogTestBook()

if __name__ == "__main__":
    pass
