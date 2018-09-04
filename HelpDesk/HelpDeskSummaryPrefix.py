__author__ = "Manuel Escriche <mev@tid.es>"

import re
from jira.client import JIRA
from kernel.Settings import settings

server = settings.server['JIRA']
options = {'server': 'https://{}'.format(server.domain), 'verify': False}
jira = JIRA(options, basic_auth=(server.username, server.password))

project = 'HELP'
cmp_lab = '10279'
cmp_tech = '10278'

# issues = jira.search_issues('assignee=admin')
assignee = 'aalonsog'
issues = jira.search_issues('component in ({}, {}) and assignee={}'
                            .format(cmp_lab, cmp_tech, assignee), maxResults=None)

print(len(issues))

pattern = re.compile(r'FIWARE\.Request\.Lab')

for issue in issues:
    print(issue.key, issue.fields.summary)

    if re.match(pattern, issue.fields.summary):
        print(issue.key, issue.fields.summary)
        continue

    summary = re.sub(r'\[.+\]', '', issue.fields.summary)
    summary = 'FIWARE.Request.Lab.' + summary.strip()
    issue.update(summary=summary)

    print(issue.key, issue.fields.summary)
