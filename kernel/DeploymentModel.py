__author__ = "Fernando Lopez <fernando.lopez@>"

import os
import json
from kernel.Settings import settings


class DeploymentModel:
    deployment = list()
    _roadmaps = list()
    _singlenton = None

    def __new__(cls, *args, **kwargs):
        if not cls._singlenton:
            cls._singlenton = super(DeploymentModel, cls).__new__(cls, *args, **kwargs)
        return cls._singlenton

    def __init__(self):
        if len(self.deployment) == 0:
            code_home = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_home = os.path.join(code_home, 'config')
            json_file = os.path.join(config_home, 'deployment.json')

            with open(json_file, 'r') as f:
                self.deployment = json.load(f)

            self._roadmaps = \
                list(map(lambda x: self.__update_url__(self.deployment['extendedurl'], x), self.deployment['chapters']))

            self._roadmaps = {item['name']: item['roadmap'] for item in self._roadmaps}

    @staticmethod
    def __update_url__(url, chapter):
        if chapter['roadmap'] != '':
            chapter['roadmap'] = 'https://' + settings.server['FORGE'].domain + url + chapter['roadmap']

        return chapter

    @property
    def roadmap(self):
        return self._roadmaps

    @property
    def tracker(self):
        return list()  # self._trackers

    @property
    def materializing(self):
        return list()  # self._material


deploymentBook = DeploymentModel()

if __name__ == "__main__":
    a = DeploymentModel()

    print(a.deployment)

    b = DeploymentModel()

    print(b.deployment)
