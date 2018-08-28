__author__ = "Manuel Escriche <mev@tid.es>"

import os
from collections import OrderedDict
from xml.etree import ElementTree as ET
from kernel.Connector import Connector


class Node:
    def __init__(self, node):
        self.name = node.get('name')
        tagsList = [child.tag for child in node]
        self.support = node.find('support').text if 'support' in tagsList else None
        self.mode = node.find('mode').text if 'mode' in tagsList else None
        self.helpdeskKeyword = node.find('helpdeskKeyword') if 'helpdeskKeyword' in tagsList else self.name
        self.workers = [item.text for item in node.findall('worker')]
        try: self.owner = Connector.getInstance().displayName(self.support)
        except: self.owner = self.support
        # print('owner=', self.owner)


class NodesBook(OrderedDict):
    _singlenton = None

    def __new__(cls, *args, **kwargs):
        if not cls._singlenton:
            cls._singlenton = super(NodesBook, cls).__new__(cls, *args, **kwargs)
        return cls._singlenton

    def __init__(self):
        super().__init__()
        codeHome = os.path.dirname(os.path.abspath(__file__))
        self.configHome = os.path.join(os.path.split(codeHome)[0], 'site_config')
        xmlfile = os.path.join(self.configHome, 'HDNodes.xml')

        tree = ET.parse(xmlfile)
        root = tree.getroot()
        for item in root.findall('node'):
            name = item.get('name')
            self[name] = Node(item)
        self.nodeByWorker = {worker:node for node in self for worker in self[node].workers}

    def getNode(self, worker):
        try:
            return self.nodeByWorker[worker]
        except Exception:
            return 'Unknown'


tHelpDeskNodesBook = NodesBook()
helpdeskNodesBook = tHelpDeskNodesBook

if __name__ == "__main__":
    pass
