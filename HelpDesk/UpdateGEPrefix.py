__author__ = 'Manuel Escriche'

import re
from jira.client import JIRA
from kernel.Settings import settings

server = settings.server['JIRA']
options = {'server': 'https://{}'.format(server.domain), 'verify': False}
# jira = JIRA(options, basic_auth=(server.username, server.password))

users = ('aalonsog', 'fermin', 'frb', 'aarranz', 'amagan', 'fdelavega', 'meth', 'henar', 'knagin', 'tali',
         'ckan-fiware-okfn', 'llopez', 'artusio', 'ralli', 'gessler', 'telsaleh', 'cdangerville', 'olivier.bettan',
         'ariokkon', 'cvetan', 'jhyvarinen', 'sami_jylkk', 'jonne.vaisanen', 'loorni', 'tospie', 'glikson',
         'jesus.movilla', 'jesus.perezgonzalez')

user = 'sergg'
chapter = 'Data'
keyword = 'CKAN'

query = 'project = HELP and status in (Closed, Done, Dismissed) AND component = FIWARE-TECH-HELP and assignee = {}'\
    .format(user)

issues = jira.search_issues(query, maxResults=False)

issues = [issue for issue in issues if not re.match(r'FIWARE\.(Request|Question)\.Tech\.Data', issue.fields.summary)]

for n, issue in enumerate(issues):
    print(n, issue, issue.fields.summary)
# exit()

for n, issue in enumerate(issues):
    if re.match(r'FIWARE\.(Question|Request)\.Tech\.{}\.{}'.format(chapter, keyword), issue.fields.summary):
        # print('->right', n, issue.fields.summary)
        continue
    if re.match(r'FIWARE\.(Question|Request)\.{}'.format('Tech'), issue.fields.summary):
        if re.match(r'FIWARE\.(Question|Request)\.Tech\.FIWARE\.(Question|Request)\.Tech', issue.fields.summary):
            summary = re.sub(r'FIWARE\.(Question|Request)\.Tech\.FIWARE\.', 'FIWARE.', issue.fields.summary)
            issue.update(fields={'summary': summary})
            print('updated ->', issue, issue.fields.summary)
        else:
            summary = issue.fields.summary.strip().split('.')
            prefix = '.'.join(summary[0:3])
            issuename = '.'.join(summary[3:]).strip()
            summary = prefix + '.{}.{}.'.format(chapter, keyword) + issuename
            issue.update(fields={'summary': summary})
            print('updated ->', issue, issue.fields.summary)
        continue

    if re.match(r'FIWARE\.(Question|Request)\.Lab', issue.fields.summary.strip()):
        # print(n, issue, issue.fields.summary)
        summary = re.sub(r'\.Lab\.', '.Tech.', issue.fields.summary.strip())
        issue.update(fields={'summary': summary})
        print('updated ->', issue, issue.fields.summary)
        continue

    # print(n, issue, issue.fields.issuetype, issue.fields.summary)
    summary = re.sub(r'\[[^\]]+?\]', '', issue.fields.summary)
    if issue.fields.issuetype.name == 'Monitor':
        summary = 'FIWARE.Question.Tech.{}'.format(summary.strip())

    if issue.fields.issuetype.name == 'extRequest':
        summary = 'FIWARE.Request.Tech.{}'.format(summary.strip())

    issue.update(fields={'summary': summary})

    print('updated->', issue, summary)
