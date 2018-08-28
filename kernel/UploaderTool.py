__author__ = "Manuel Escriche < mev@tid.es>"

import os, re
from requests import session
from xml.etree import ElementTree as ET
from collections import namedtuple
from kernel.Settings import settings


upload_record = namedtuple('upload_record', 'group_id, at_id')


class UploaderBook(dict):
    def __init__(self):
        super().__init__()
        codefile = os.path.dirname(os.path.abspath(__file__))
        home = os.path.split(codefile)[0]
        xmlfile = os.path.join(os.path.join(home, 'config'), 'uploader.xml')
        root = ET.parse(xmlfile).getroot()
        for _upload in root.findall('upload'):
            _target = _upload.get('target')
            _group_id = _upload.find('docman').get('group_id')
            _at_id = _upload.find('docman').get('at_id')
            self[_target] = upload_record(_group_id, _at_id)

uploaderBook = UploaderBook()

class Uploader:
    def __init__(self):
        server = settings.server['FORGE']
        self._domain = server.domain
        self._loginData = {'login':'Login with SSL',
                           'form_loginname':server.username,
                           'form_pw': server.password}
        self._ubook = UploaderBook()

    def _upload_file(self, filename, **kwargs):
        ses = session()
        print("Accessing FIWARE forgefusion...")
        urlLogin = 'https://{0}/account/login.php'.format(self._domain)

        con = ses.post(urlLogin, data=self._loginData, verify=False)

        mfile = os.path.basename(filename)

        payload1 = {'group_id': kwargs['group_id']}

        files = { 'uploaded_data': (mfile, open(filename, 'rb'))}

        urlDocman = 'https://{0}/docman/new.php'.format(self._domain)

        with open(filename, 'rb') as upfile:
            payload2 = {'title':kwargs['title'],
                        'description':kwargs['description'],
                        'doc_group':kwargs['doc_group'],
                        'language_id':'1',
                        'type':'httpupload',
                        'submit':'Submit Information '}
            response = ses.post(urlDocman, params=payload1, data=payload2, files=files, verify=False)

        print(response.url)
        print(response.status_code)
        return

    def _upload_backlog(self, doc, scope):
        print("--upload backlog-- dest = forge-private-docs object = {0} topic = {1}".format(doc, scope))
        fileList = os.listdir(settings.outHome)
        mfilter = re.compile(r'\bFIWARE\.backlog\.(?P<doc>\w+)\.(?P<scope>[\w\-]+)\.(?P<day>\d{8})-(?P<hour>\d{4})\.xlsx\b')
        #print(fileList)
        xlsxfiles = [f for f in fileList if mfilter.match(f)]
        #print(xlsxfiles)
        record = namedtuple('record','filename, day, time')
        files = [record(mfilter.match(f).group(0),
                        mfilter.match(f).group('day'),
                        mfilter.match(f).group('hour'))
                 for f in xlsxfiles
                 if mfilter.match(f).group('doc') == doc and mfilter.match(f).group('scope') == scope]
        if not len(files):
            print('There is no object {0} in {1} to be uploaded'.format(doc, scope))
            return
        files.sort(key = lambda e:(e.day, e.time), reverse=True)
        mfile= files[0].filename
        #mfile = files[-1][0]
        print('--upload-- file = {0}'.format(mfile))

        filename = os.path.join(settings.outHome, mfile)

        fields = re.split('\.', mfile)
        title = '{0}.{1}.{2}-{3}'.format(fields[1], fields[2],fields[3], fields[4])
        description = '{1} {0} report for {2} created on {3}'.format(fields[1], fields[2],fields[3], fields[4])
        print(self._ubook)
        self._upload_file(filename,
                          title=title,
                          description= description,
                          group_id=self._ubook['backlog'].group_id,
                          doc_group=self._ubook['backlog'].at_id)

    def _upload_helpdesktech(self, doc, scope):
        print("--upload helpdesk-tech - dest = forge-private-docs doc = {0} scope = {1}".format(doc, scope))
        fileList = os.listdir(settings.outHome)
        mfilter = re.compile(r'\bFIWARE\.helpdesk-tech\.(?P<doc>\w+)\.(?P<scope>[\w\-]+)\.(?P<day>\d{8})\.xlsx\b')
        #print(fileList)
        xlsxfiles = [f for f in fileList if mfilter.match(f)]
        #print(xlsxfiles)
        record = namedtuple('record','filename, day')
        files = [record(mfilter.match(f).group(0),
                        mfilter.match(f).group('day'))
                 for f in xlsxfiles
                 if mfilter.match(f).group('doc') == doc and mfilter.match(f).group('scope') == scope]
        if not len(files):
            print('There is no object {0} in {1} to be uploaded'.format(doc, scope))
            return
        files.sort(key = lambda e:(e.day), reverse=True)
        mfile= files[0].filename
        #mfile = files[-1][0]
        print('--upload-- file = {0}'.format(mfile))

        filename = os.path.join(settings.outHome, mfile)

        fields = re.split('\.', mfile)
        title = '{0}.{1}.{2}-{3}'.format(fields[1], fields[2],fields[3], fields[4])
        description = '{1} {0} report for {2} created on {3}'.format(fields[1], fields[2],fields[3], fields[4])
        print(self._ubook)
        self._upload_file(filename,
                          title=title,
                          description= description,
                          group_id=self._ubook['helpdesk-tech'].group_id,
                          doc_group=self._ubook['helpdesk-tech'].at_id)


    def upload(self, target, doc, chapters):
        print(target, doc)
        for k,chapter in enumerate(chapters, start=1):
            print(k, '-', chapter)
            eval('self._upload_{}(doc, chapter)'.format(target))


if __name__ == "__main__":
    pass
