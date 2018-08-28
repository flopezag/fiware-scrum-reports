__author__ = 'Manuel Escriche'

from jira.client import JIRA
from _Kernel.Settings import settings

server = settings.server['JIRA']
options={'server': 'https://{}'.format(server.domain)}
#jira = JIRA(options, basic_auth=(server.username, server.password))
jira = JIRA(options, basic_auth=('mev', 'CaDrie74'))

query = "project in (HELP, HELC) and status not in (closed, done) and updated>=-24h order by updated desc"
query = "project in (HELP, HELC) and status not in (closed, done) and updated<=-24h and updated>=-5d order by updated desc"
#query = "project in (HELP, HELC) AND status = closed and updated >= -16h ORDER BY updated DESC"
#query = "project in (HELP, HELC) and assignee = 'Manuel Escriche'"

issues = jira.search_issues(query, maxResults=False)

for issue in issues:
    if 'SPAM' in [comp.name for comp in issue.fields.components]: continue
    print('http://jira.fiware.org/browse/{}'.format(issue))
    print('--> {}'.format(issue.fields.summary))
    print('--> {}'.format(issue.fields.assignee))