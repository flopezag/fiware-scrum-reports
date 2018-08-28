__author__ = "Manuel Escriche <mev@tid.es>"

import os, pickle, base64, requests
from datetime import datetime
from kernel.TrackerBook import trackersBook, trackersBookByKey
from kernel.ComponentsBook import tComponentsBook
from kernel.Jira import JIRA

class DataEngine:
    class DataObject:
        def __init__(self, name, storage):
            self.storage = storage
            self.name = name

        def save(self, data):
            timestamp = datetime.now().strftime("%Y%m%d-%H%M")
            filename = 'FIWARE.Engine.{}.{}.pkl'.format(self._type, self.name)
            longFilename = os.path.join(self.storage, filename)

            with open(longFilename, 'wb') as f:
                pickle.dump((timestamp, data), f, pickle.HIGHEST_PROTOCOL)

            return filename

        def load(self):
            filename = 'FIWARE.Engine.{}.{}.pkl'.format(self._type, self.name)
            try:
                f = open(os.path.join(self.storage, filename), 'rb')
                timestamp, data = pickle.load(f)
            except FileNotFoundError:
                raise
            else:
                f.close()
            return data, timestamp

    class Tracker(DataObject):
        _type = 'Tracker'
        def __init__(self, trackername, storage):
            super().__init__(trackername, storage)

    class Comp(DataObject):
        _type = 'Component'
        def __init__(self, cmpname, storage):
            super().__init__(cmpname, storage)



    class Query(DataObject):
        _type = 'Query'
        def __init__(self, name, storage):
            super().__init__(name, storage )

    def __init__(self, storage):
        self.storage = storage
        #self.jira = JIRA()

    @classmethod
    def snapshot(cls, storage):
        jira = JIRA()
        files = list()
        for trackername in trackersBook:
            tracker = trackersBook[trackername]
            data = jira.getTrackerData(tracker.keystone)
            filename = DataEngine.Tracker(trackername, storage).save(data)
            files.append(filename)
        return files

    def getTrackerData(self, tracker_id):
        tracker = trackersBookByKey[tracker_id]
        return DataEngine.Tracker(tracker.name, self.storage).load()

    def saveTrackerData(self, tracker_id, data):
        tracker = trackersBookByKey[tracker_id]
        DataEngine.Tracker(tracker.name, self.storage).save(data)

    def getComponentData(self, cmp_id):
        comp = tComponentsBook[cmp_id]
        name = '{}-{}'.format(comp.name, cmp_id)
        try:
            return DataEngine.Comp(name, self.storage).load()
        except Exception:
            tracker = trackersBookByKey[comp.tracker]
            trackerData, timestamp = DataEngine.Tracker(tracker.name, self.storage).load()
            data = list()
            for item in trackerData:
                try:key = item['fields']['components'][0]['id']
                except Exception: continue
                if cmp_id == key: data.append(item)
            return data, timestamp

    def saveComponentData(self, cmp_id, data):
        cmp = tComponentsBook[cmp_id]
        name = '{}-{}'.format(cmp.name, cmp_id)
        DataEngine.Comp(name, self.storage).save(data)

    def getQueryData(self, name):
        return DataEngine.Query(name, self.storage).load()

    def saveQueryData(self, name, data):
        DataEngine.Query(name, self.storage).save(data)

class DataFactory:
    def __init__(self, storage):
        self.engine = DataEngine(storage)

    def getTrackerData(self, tracker_id):
        data, timestamp = self.engine.getTrackerData(tracker_id)
        source = 'store'
        return data, timestamp, source

    def getComponentData(self, cmp_id):
        try:
            data = JIRA().getComponentData(cmp_id)
            self.engine.saveComponentData(cmp_id, data)
            timestamp = datetime.now().strftime("%Y%m%d-%H%M")
            source = 'jira'
        except Exception:
            data, timestamp = self.engine.getComponentData(cmp_id)
            source = 'store'
        return data, timestamp, source

    def getQueryData(self, name, jql):
        try:
            data = JIRA().getQuery(jql)
            self.engine.saveQueryData(name, data)
            timestamp = datetime.now().strftime("%Y%m%d-%H%M")
            source = 'jira'
        except:
            data, timestamp = self.engine.getQueryData(name)
            source = 'store'
        return data, timestamp, source

    def getTrackerNoComponentData(self, tracker_id):
        jql = 'project = {} AND component = EMPTY'.format(tracker_id)
        name = '{}-NoComp'.format(tracker_id)
        try:
            data = JIRA().getQuery(jql)
            self.engine.saveQueryData(name, data)
            timestamp = datetime.now().strftime("%Y%m%d-%H%M")
            source = 'jira'
        except Exception:
            data, timestamp = self.engine.getQueryData(name)
            source = 'store'
        return data, timestamp, source


if __name__ == "__main__":
    pass
