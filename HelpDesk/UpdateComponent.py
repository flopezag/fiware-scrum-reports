__author__ = 'Manuel Escriche'

import re
from jira.client import JIRA
from kernel.Settings import settings

server = settings.server['JIRA']
options = {'server': 'https://{}'.format(server.domain), 'verify': False}
jira = JIRA(options, basic_auth=(server.username, server.password))

users = ('aalonsog', 'fermin', 'frb', 'aarranz', 'amagan', 'fdelavega', 'meth', 'knagin', 'tali', 'ckan-fiware-okfn',
         'llopez', 'ralli', 'gessler', 'telsaleh', 'cdangerville', 'olivier.bettan', 'ariokkon', 'cvetan', 'jhyvarinen',
         'sami_jylkk', 'jonne.vaisanen', 'tospie', 'cschlinkmann', 'glikson', 'jesus.movilla', 'jesus.perezgonzalez')

user = 'sergg'
query = 'project = HELP AND component = FIWARE-LAB-HELP and assignee = {}'.format(user)
# query = 'project = HELP AND component = FIWARE-TECH-HELP and assignee = {}'.format(user)

issues = jira.search_issues(query, maxResults=False)
# issues = [issue for issue in issues if re.search(r'FIWARE\.Request\.',issue.fields.summary)]
for n, issue in enumerate(issues):
    issue.update(fields={"components": [{'name': 'FIWARE-TECH-HELP'}]})
    print('updated : ', n, issue, issue.fields.assignee.key, issue.fields.components, issue.fields.summary)
