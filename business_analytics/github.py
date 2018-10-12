from business_analytics.analysis import Analysis
import json
from functools import reduce
import time
import requests
import json
from kernel.Settings import settings


class Github:
    def __init__(self, enablers_dict):
        self.remaining = 0
        self.token = settings.server['GITHUB'].password
        self.username = settings.server['GITHUB'].username
        self.baseurl = 'https://' + settings.server['GITHUB'].domain
        self.list_enablers = list(
            reduce(lambda x, y: x + y,
                   map(lambda x: x['enablers'],
                       filter(lambda y: len(y['enablers']) != 0, enablers_dict['tracker'])
                       )
                   )
        )

    def get_data_issues(self, enabler, key, issue):
        labels = list(filter(lambda x: x['name'] == "bug", issue['labels']))

        if len(labels) == 0:
            issuetype = 'WorkItem'
        else:
            issuetype = 'Bug'

        a_dict = dict([
            ("issuetype", issuetype),
            ("component_name", enabler),
            ("component_id", key),
            ("status", issue['state'].title()),
            ("created", Analysis.format_datetime(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ')),
            ("updated", Analysis.format_datetime(issue['updated_at'], '%Y-%m-%dT%H:%M:%SZ')),
            ("resolved", Analysis.format_datetime(issue['closed_at'], '%Y-%m-%dT%H:%M:%SZ')),
            ("released", Analysis.format_datetime(issue['closed_at'], '%Y-%m-%dT%H:%M:%SZ'))
        ])

        return a_dict

    def get_issues_repo_github(self, repository, enabler, key):
        repository = repository['repo'].split("/")

        print('        Repository: {}'.format(repository))

        data = self.get_issues(repository[0], repository[1])

        total_issues = list(filter(lambda x: x.get('pull_request') is None, data))

        total_issues = list(map(lambda x: self.get_data_issues(enabler=enabler, key=key, issue=x), total_issues))

        return total_issues

    def get_issues_github(self, enabler):
        name = enabler['name']
        cmp_key = enabler['cmp_key']

        total_issues = list(
            map(lambda x: self.get_issues_repo_github(repository=x, enabler=name, key=cmp_key), enabler['github']))

        return total_issues

    def get_issues(self, owner, repository):
        repoissues = list()
        remaining = self.remaining
        url = self.baseurl + '/repos/{}/{}/issues?state=all&per_page=100'.format(owner, repository)

        while True:
            r = requests.get(url, auth=(self.username, self.token))
            if r.ok:
                repoissues = repoissues + json.loads(r.text or r.content)

            try:
                url = r.links['next']['url']
            except KeyError:
                break

            remaining = r.headers['X-RateLimit-Remaining']
            reset_time = r.headers['X-RateLimit-Reset']

            if remaining == 0:
                now = time.time()
                seconds_left = float(reset_time) - now + 1
                time.sleep(seconds_left)

        print("            Remaining requests GitHub API {}".format(remaining))

        return repoissues

    def get_ratelimit(self):
        url = self.baseurl + '/rate_limit'
        r = requests.get(url=url, auth=(self.username, self.token))

        print('        GitHub Rate Limit: {}\n        GitHub Rate Remaining: {}'
              .format(r.headers['X-RateLimit-Limit'], r.headers['X-RateLimit-Remaining']))

        self.remaining = float(r.headers['X-RateLimit-Remaining'])

    def get_data(self):
        self.get_ratelimit()

        data = list(
            reduce(lambda x, y: x + y,
                   reduce(lambda x, y: x + y,
                          map(lambda x: self.get_issues_github(enabler=x), self.list_enablers))))

        return data
