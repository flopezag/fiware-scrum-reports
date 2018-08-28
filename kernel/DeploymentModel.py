__author__ = "Manuel Escriche <mev@tid.es>"

import os
from xml.etree import ElementTree as ET
from kernel.Settings import settings

class DeploymentModel:
    _singlenton = None

    def __new__(cls, *args, **kwargs):
        if not cls._singlenton:
            cls._singlenton = super(DeploymentModel, cls).__new__(cls, *args, **kwargs)
        return cls._singlenton

    def __init__(self):
        self.configHome = settings.configHome
        #print(self.configHome)
        xmlfile = os.path.join(self.configHome, 'deployment.xml')
        #print(xmlfile)

        tree = ET.parse(xmlfile)
        root = tree.getroot()

        self._trackers = dict()
        self._roadmaps = dict()
        self._material = dict()

        for _chapter in root.findall('chapter'):
            name = _chapter.get('name')
            tagsList = [child.tag for child in _chapter]
            self._roadmaps[name]  = 'http://{}{}'.format(settings.server['FORGE'].domain, _chapter.find('roadmap').text) \
                if 'roadmap' in tagsList else None
            self._trackers[name] = 'https://{}{}'.format(settings.server['JIRA'].domain, _chapter.find('tracker').text) \
                if 'tracker' in tagsList else None
            self._material[name] = 'http://{}{}'.format(settings.server['FORGE'].domain, _chapter.find('materializing').text) \
                if 'materializing' in tagsList else None

    @property
    def roadmap(self):
        return self._roadmaps

    @property
    def tracker(self):
        return self._trackers

    @property
    def materializing(self):
        return self._material


deploymentBook = DeploymentModel()

if __name__ == "__main__":
    pass
