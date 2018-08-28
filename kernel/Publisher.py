import abc
import requests
import re
import logging
import sys
from html.parser import HTMLParser
from collections import defaultdict, OrderedDict
from kernel.IssuesModel import backlogIssuesModel
from kernel.IssuesWorkflow import issuesWorkflow
from kernel.WebReaders import TextAreaExtractor

__author__ = "Manuel Escriche <mev@tid.es>"


class PageParser(HTMLParser):
    def __init__(self):
        if sys.version_info[:2] == (3, 6):
            super().__init__()
        elif sys.version_info[:2] == (3, 4):
            super().__init__(self)
        else:
            logging.error("Backlog tool requires python3.4 or python3.6")
            exit()

        self._filter = re.compile(r'\s*(FIWARE[\w\-\.]+)\s*')
        self._recording = False
        self._link = ''
        self._reference = ''
        self._data = list()

    def handle_starttag(self, tag, attrs):
        # print("tag=", tag, "attrs=", attrs)
        if tag != 'a':
            return

        for name, value in attrs:
            if name == 'href':
                if self._filter.search(value):
                    self._recording = True
                    self._link = value

    def handle_data(self, data):
        # print("data=", data)
        if not self._recording:
            return

        m = self._filter.search(data)
        if m:
            self._reference = m.group()
        else:
            self._recording = False

    def handle_endtag(self, tag):
        if not self._recording:
            return

        if tag != 'a':
            return

        self._data.append(self._reference.strip())
        self._recording = False

    @property
    def data(self):
        return self._data


class PublisherItemRule(metaclass=abc.ABCMeta):
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
        for key in sorted(self.description.keys()):
            yield key
    keys = __iter__

    def values(self):
        for key in self.description.keys():
            yield self.description[key]

    def items(self):
        for key in self.description.keys():
            yield (key, self.description[key])

    def __getitem__(self, item): return self.description[item]


class RoadMapTest(PublisherItemRule):
    def __init__(self, name, publisher):
        super().__init__(name)
        self.publisher = publisher
        _key = lambda i: '{0}.{1}'.format(name, i)
        self.description[_key(1)] = "Test for Technical Roadmap - undue publishing"
        self.description[_key(2)] = "Test for Technical Roadmap - missing publication"

    def _filter_excluded(self, item):
        if item.issueType not in backlogIssuesModel.open:
            return True

        if item.resolution == 'Dismissed':
            return True

        return False

    def _rule_correct_publication(self, item):
        return True

    def _rule_valid_no_publication(self, item):
        return False

    def __call__(self, item):
        _key = lambda i: '{0}.{1}'.format(self.name, i)
        if self._filter_excluded(item):
            item.test.status[self.name] = 'NT'
            return

        output = defaultdict(str)
        self.roadmap = self.publisher.readRoadmap(item.chapter)

        if item.reference in self.roadmap:
            output[_key(1)] = 'OK' if self._rule_correct_publication(item) else 'KO'
        else:
            output[_key(2)] = 'OK' if self._rule_valid_no_publication(item) else 'KO'

        status = 'OK' if all(value == 'OK' for value in output.values()) else 'KO'

        item.test.test[self.name] = output
        item.test.status[self.name] = status
        return


class MaterializingTest(PublisherItemRule):
    def __init__(self, name, publisher):
        super().__init__(name)
        self.publisher = publisher
        _key = lambda i: '{0}.{1}'.format(name, i)
        self.description[_key(1)] = "Test for Materializing - undue publishing"
        self.description[_key(2)] = "Test for Materializing - missing publication"

    def _filter_excluded(self, item):
        if item.issueType not in backlogIssuesModel.open:
            return True

        if item.resolution == 'Dismissed':
            return True

        return False

    def _rule_correct_publication(self, item):
        assert item.reference in self.materializing
        if item.issueType in backlogIssuesModel.midTermTypes:
            if item.status in issuesWorkflow.closed:
                return True

            return True if item.resolution == 'Done' else False
        else:
            return True if any([son.reference in self.materializing and
                                son.status in issuesWorkflow.closed for son in item.sons]) else False

    def _rule_valid_no_publication(self, item):
        assert item.reference not in self.materializing
        if item.issueType in backlogIssuesModel.midTermTypes:
            return False if item.status in issuesWorkflow.closed else True
        else:
            return False if any([son.reference in self.materializing for son in item.sons]) else True

    def __call__(self, item):
        _key = lambda i: '{0}.{1}'.format(self.name, i)
        if self._filter_excluded(item):
            item.test.status[self.name] = 'NT'
            return
        output = defaultdict(str)
        self.materializing = self.publisher.readMaterializing(item.chapter)
        if item.reference in self.materializing:
            output[_key(1)] = 'OK' if self._rule_correct_publication(item) else 'KO'
        else:
            output[_key(2)] = 'OK' if self._rule_valid_no_publication(item) else 'KO'

        status = 'OK' if all(value == 'OK' for value in output.values()) else 'KO'
        item.test.test[self.name] = output
        item.test.status[self.name] = status
        return


class OpenDescriptionTest(PublisherItemRule):
    def __init__(self, name, url):
        super().__init__(name)
        _key = lambda i: '{0}.{1}'.format(name, i)
        self.description[_key(1)] = 'Test for Open Description - page availability'
        self.description[_key(2)] = \
            "Test for Open Description - right structure: Name, Chapter, Goal, Description and Rational"

        self.description[_key(3)] = "Test for Open Description - Over-consistency between reference and name"
        self.description[_key(4)] = "Test for Open Description - Incorrect chapter name"
        self.description[_key(5)] = "Test for Open Description - less than 10 words in goal field"
        self.description[_key(6)] = "Test for Open Description - less than 30 words in description field"
        self.description[_key(7)] = "Test for Open Description - less than 20 words in rational field"
        self.description[_key(8)] = "Test for Open Description - more than 250 words in record"

        self._reader = TextAreaExtractor(url)

    def _filter_excluded(self, item):
        if item.issueType not in backlogIssuesModel.open:
            return True

        if item.test.status['RoadMap'] == 'KO':
            return True

        if item.test.status['Materializing'] == 'KO':
            return True

        return False

    def _rule_available_page(self, item):
        description = self._reader(item.reference)
        item.openDescription = description if description['exist'] else None
        # print(item.openDescription)
        return True if item.openDescription else False

    def _rule_right_description_structure(self, item):
        if 'Name' not in item.openDescription:
            return False

        if 'Chapter' not in item.openDescription:
            return False

        if 'Goal' not in item.openDescription:
            return False

        if 'Description' not in item.openDescription:
            return False

        if 'Rationale' not in item.openDescription:
            return False

        return True

    def _rule_overconsistency_name_reference(self, item):
        if item.openDescription['Name'] == item.reference:
            return True

        if item.openDescription['Name'] == item.shortReference:
            return True

        return False

    def _rule_proper_chapter(self, item):
        return True if item.chapter == item.openDescription['Chapter'] else False

    def _rule_proper_goal_size(self, item):
        return True if item.openDescription.size('Goal') >= 10 else False

    def _rule_proper_description_size(self, item):
        return True if item.openDescription.size('Description') >= 30 else False

    def _rule_proper_rationale_size(self, item):
        return True if item.openDescription.size('Rationale') >= 20 else False

    def _rule_proper_record_size(self, item):
        return True if item.openDescription.NSize <= 250 else False

    def __call__(self, item):
        _key = lambda i: '{0}.{1}'.format(self.name, i)
        if self._filter_excluded(item):
            item.test.status[self.name] = 'NT'
            return
        output = defaultdict(str)
        output[_key(1)] = 'OK' if self._rule_available_page(item) else 'KO'
        if output[_key(1)] == 'OK':
            output[_key(2)] = 'OK' if self._rule_right_description_structure(item) else 'KO'
            if output[_key(2)] == 'OK':
                output[_key(3)] = 'KO' if self._rule_overconsistency_name_reference(item) else 'OK'
                output[_key(4)] = 'OK' if self._rule_proper_chapter(item) else 'KO'
                output[_key(5)] = 'OK' if self._rule_proper_goal_size(item) else 'KO'
                output[_key(6)] = 'OK' if self._rule_proper_description_size(item) else 'KO'
                output[_key(7)] = 'OK' if self._rule_proper_rationale_size(item) else 'KO'
            output[_key(8)] = 'OK' if self._rule_proper_record_size(item) else 'KO'
        status = 'OK' if all(value == 'OK' for value in output.values()) else 'KO'
        item.test.test[self.name] = output
        item.test.status[self.name] = status
        return


class PublisherTestBook:
    def __init__(self, publisher, url):
        self._store = OrderedDict()
        criteria = 'RoadMap'
        self._store[criteria] = RoadMapTest(criteria, publisher)
        criteria = 'Materializing'
        self._store[criteria] = MaterializingTest(criteria, publisher)
        criteria = 'OpenDescription'
        self._store[criteria] = OpenDescriptionTest(criteria, url)

    @property
    def store(self):
        return self._store

    def __iter__(self):
        for rule in self._store.keys():
            yield rule

    keys = __iter__

    def values(self):
        for rule in self._store.keys():
            yield self._store[rule]

    def items(self):
        for rule in self._store.keys():
            yield (rule, self._store[rule])

    def __getitem__(self, rule): return self._store[rule]

    def __len__(self): return len(self._store)


class Publisher:
    """
    Backlog Publisher
    """
    url_root = 'http://forge.fiware.org/plugins/mediawiki/wiki/fiware/index.php/'
    Roadmap = {'Cloud': 'Roadmap_of_Cloud_Hosting',
               'Data': 'Roadmap_of_Data/Context_Management',
               'IoT': 'Roadmap_of_Internet_of_Things_(IoT)_Services',
               'Apps': 'Roadmap_of_Applications/Services_Ecosystem_and_Delivery_Framework',
               'Security': 'Roadmap_of_Security',
               'I2ND': 'Roadmap_of_Advanced_middleware,_Interface_to_Networks_and_Robotics',
               'WebUI': 'Roadmap_of_Advanced_Web-based_UI'}
    Materializing = {'Cloud': 'Materializing_Cloud_Hosting_in_FI-WARE',
                     'Data': 'Materializing_Data/Context_Management_in_FI-WARE',
                     'IoT': 'Materializing_Internet_of_Things_(IoT)_Services_Enablement_in_FI-WARE',
                     'Apps': 'Materializing_Applications/Services_Ecosystem_and_Delivery_Framework_in_FI-WARE',
                     'Security': 'Materializing_Security_in_FI-WARE',
                     'I2ND': 'Materializing_the_Interface_to_Networks_and_Devices_(I2ND)_in_FI-WARE',
                     'WebUI': 'Materializing_Advanced_Middleware_and_Web_User_Interfaces_in_FI-WARE'}

    def __init__(self):
        # self.roadmap = self._read_docs(Publisher.Roadmap)
        # self.materializing = self._read_docs(Publisher.Materializing)
        self.roadmap = dict()
        self.materializing = dict()
        self.testBook = PublisherTestBook(self, Publisher.url_root)

    def _readPage(self, page_url):
        try:
            page = requests.get(Publisher.url_root + page_url)
        except Exception as e:
            logging.error(e)
            logging.error('Failure when reading {}'.format(Publisher.url_root + page_url))
            page = None
            raise

        parser = PageParser()
        parser.feed(page.text)
        return parser.data

    def readRoadmap(self, chapter):
        if chapter not in self.roadmap:
            url = Publisher.Roadmap[chapter]
            data = self._readPage(url)
            data.extend(self._readPage(url + '(previous_releases)'))
            self.roadmap[chapter] = data
        return self.roadmap[chapter]

    def readMaterializing(self, chapter):
        if chapter not in self.materializing:
            self.materializing[chapter] = self._readPage(Publisher.Materializing[chapter])
        return self.materializing[chapter]

    def _read_docs(self, doc):
        # print('_read_docs')
        __filter = re.compile(r'\[\s*(FIWARE[\w\-\.]+)\s*\]')
        data = dict()
        for chapter in doc:
            # print(Publisher.url_root + doc[chapter])
            page = requests.get(Publisher.url_root + doc[chapter])
            parser = PageParser()
            parser.feed(page.text)
            # print(parser.data)
            # _input = html2text(page.text)
            # if chapter == 'Data': print(_input)
            # data[chapter] = list(re.findall(__filter, html2text(page.text)))
            data[chapter] = parser.data
            # if chapter == 'Data': print(data[chapter])
        return data

if __name__ == "__main__":
    pass
