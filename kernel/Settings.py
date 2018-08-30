import os
from xml.etree import ElementTree as ET
from datetime import datetime
from collections import namedtuple

__author__ = "Manuel Escriche < mev@tid.es>"


class Settings:
    def __init__(self):
        self._dashboard = dict()
        self._review = dict()
        self.home = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]
        self.configHome = os.path.join(self.home, 'config')
        # self.storeHome = os.path.join(self.home, 'store')
        # self.inHome = os.path.join(self.home, 'INDATA')
        self.storeHome = os.path.join(self.home, 'store')
        self.backlogHome = os.path.join(self.home, 'BACKLOGS')
        self._logoshome = os.path.join(self.home, 'LOGOS')
        self.outHome = os.path.join(self.home, 'REPORTS')
        xmlfile = os.path.join(self.configHome, 'settings.xml')
        # print(xmlfile)

        tree = ET.parse(xmlfile)
        root = tree.getroot()
        self.logoAzul = os.path.join(self._logoshome, root.find('logo1').text)
        self.logoAzulOsc = os.path.join(self._logoshome, root.find('logo2').text)
        self.logofiware = os.path.join(self._logoshome, root.find('logo3').text)

        self._today = datetime.now().strftime("%Y%m%d")
        self._dashboard['deliverable'] = root.find('dashboard').find('deliverable').text
        self.domain = root.find('domain').text

        self._servers = dict()
        record = namedtuple('record', ('domain, username, password'))
        for _server in root.findall('server'):
            name = _server.get('name')
            domain = _server.find('domain').text
            username = _server.find('username').text
            password = _server.find('password').text
            self._servers[name] = record(domain, username, password)

        # print(len(self.__chapters))

    @property
    def server(self):
        return self._servers

    @property
    def chapters(self):
        return 'Apps', 'Cloud', 'Data', 'IoT', 'I2ND', 'Security', 'WebUI', 'Ops', 'Academy', 'Catalogue', 'Lab'

    @property
    def management(self):
        return 'Coordination', 'TechnicalCoordination'

    @property
    def deliverable(self):
        return self._dashboard['deliverable']


settings = Settings()

if __name__ == "__main__":
    pass
