__author__ = "Manuel Escriche <mev@tid.es>"

from datetime import date, datetime

from kernel.Settings import settings
from kernel.Calendar import agileCalendar
from kernel.ComponentsBook import helpdeskCompBookByKey, accountsDeskBookByKey


class LinkedIssue:
    def __init__(self, item):
        super().__init__()
        _type = [key for key in ('inwardIssue', 'outwardIssue') if key in item][0]
        self.type = _type
        self.status = item[_type]['fields']['status']['name']
        self.key = item[_type]['key']
        self.url = 'https://{}/browse/{}'.format(settings.server['JIRA'].domain, self.key)

    def __str__(self):
        return self.key

    def __repr__(self):
        return self.key


class NIssue:
    def __init__(self, issue):
        # pprint.pprint(issue)
        self.issueType = issue['fields']['issuetype']['name']
        if self.issueType != self._issueType:
            raise Exception('Inconsistent Issue Type')
        self.key = issue['key']
        self.url = "https://{}/browse/{}".format(settings.server['JIRA'].domain,  self.key)
        self.id = issue['id']
        self.project = issue['fields']['project']['key']
        self.component = [item['id'] for item in issue['fields']['components']]
        self.summary = issue['fields']['summary'].strip()
        self.status = issue['fields']['status']['name']
        self.description = issue['fields']['description']
        self.reporter = issue['fields']['reporter']['displayName']

        self.created = datetime.strptime(issue['fields']['created'][:10], '%Y-%m-%d').date()
        self.updated = datetime.strptime(issue['fields']['updated'][:10], '%Y-%m-%d').date()

        try: self.priority = issue['fields']['priority']['name']
        except Exception: self.priority = None

        try: self.assignee = issue['fields']['assignee']['displayName']
        except Exception: self.assignee = None

        try: self.duedate = datetime.strptime(issue['fields']['duedate'][:10], '%Y-%m-%d').date()
        except Exception: self.duedate = None

        try: self.resolution = issue['fields']['resolution']['name']
        except Exception: self.resolution = None

        try: self.resolutionDate = datetime.strptime(issue['fields']['resolutiondate'][:10], '%Y-%m-%d').date()
        except Exception: self.resolutionDate = None

        try: self.version = issue['fields']['fixVersions'][0]['name']
        except Exception: self.version = 'Unscheduled'

        try: self.releaseDate = datetime.strptime(issue['fields']['fixVersions'][0]['releaseDate'][:10], '%Y-%m-%d').date()
        except Exception: self.releaseDate = None

        try: self.linkedIssues = [LinkedIssue(item) for item in issue['fields']['issuelinks']]
        except Exception:  self.linkedIssues = None

    @property
    def resolved(self):
        return self.resolution != None

    @property
    def age(self):
        if self.resolved:
            try:
                return (self.resolutionDate - self.created).days
            except Exception as error:
                print(error, self.url)
                raise
        else: return (date.today() - self.created).days

    @property
    def delay(self):
        assert self.duedate
        if self.resolved and self.duedate:
            return (self.resolutionDate - self.duedate).days
        else: return (date.today() - self.duedate).days

    @property
    def upcoming(self):
        return (self.duedate - date.today()).days


class AccountsDeskIssue(NIssue):
    def __init__(self, issue):
        super().__init__(issue)
    @property
    def name(self):
        return self.summary
    @property
    def channel(self):
        try:
            return accountsDeskBookByKey[self.component[0]]
        except Exception:
            return 'Unassigned'

class AccountRequest(AccountsDeskIssue):
    _issueType = 'UpgradeAccount'
    def __init__(self, issue):
        super().__init__(issue)

class AccountProvision(AccountsDeskIssue):
    _issueType = 'AccountUpgradeByNode'
    def __init__(self, issue):
        super().__init__(issue)


class iHelpDeskIssue(NIssue):
    def __init__(self, issue):
        super().__init__(issue)
    @property
    def channel(self):
        try:
            return helpdeskCompBookByKey[self.component[0]]
        except Exception:
            return None
    @property
    def name(self):
        return self.summary

class iWorkItem(iHelpDeskIssue):
    _issueType = 'WorkItem'
    def __init__(self, issue):
        super().__init__(issue)

class iBug(iHelpDeskIssue):
    _issueType = 'Bug'
    def __init__(self, issue):
        super().__init__(issue)


class HelpDeskIssue(NIssue):
    def __init__(self, issue):
        super().__init__(issue)
        try: self.chapter = issue['fields']['customfield_11103']
        except Exception: self.chapter = None
        try: self.enabler = issue['fields']['customfield_11105']
        except Exception: self.enabler = None

    @property
    def channel(self):
        try:
            return helpdeskCompBookByKey[self.component[0]]
        except Exception:
            return None
    @property
    def name(self):
        return self.summary

class extRequest(HelpDeskIssue):
    _issueType = 'extRequest'
    def __init__(self, issue):
        super().__init__(issue)


class eRequest(HelpDeskIssue):
    _issueType = 'eRequest'
    def __init__(self, issue):
        super().__init__(issue)

class Monitor(HelpDeskIssue):
    _issueType = 'Monitor'
    def __init__(self, issue):
        super().__init__(issue)


class BacklogIssue(NIssue):
    def __init__(self, issue):
        super().__init__(issue)
        _version = self.version.split()
        version = 'Unscheduled' if len(_version) == 1 else _version[1]
        if version == 'Unscheduled': self.frame = 'Foreseen'
        elif version in agileCalendar.pastTimeSlots: self.frame = 'Implemented'
        elif version in agileCalendar.currentTimeSlots: self.frame = 'Working On'
        elif version in agileCalendar.futureTimeSlots: self.frame = 'Foreseen'
        else: self.frame = 'Unknown'

    @property
    def timeSlot(self):
        return self.version
    @property
    def name(self):
        return self.summary

class Epic(BacklogIssue):
    _issueType = 'Epic'
    def __init__(self, issue):
        super().__init__(issue)

class Feature(BacklogIssue):
    _issueType = 'Feature'
    def __init__(self, issue):
        super().__init__(issue)

class Story(BacklogIssue):
    _issueType = 'Story'
    def __init__(self, issue):
        super().__init__(issue)

class WorkItem(BacklogIssue):
    _issueType = 'WorkItem'
    def __init__(self, issue):
        super().__init__(issue)

class Bug(BacklogIssue):
    _issueType = 'Bug'
    def __init__(self, issue):
        super().__init__(issue)

class Risk(BacklogIssue):
    _issueType = 'Risk'
    def __init__(self, issue):
        super().__init__(issue)


if __name__ == "__main__":
    pass
