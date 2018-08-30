__author__ = "Manuel Escriche <mev@tid.es>"

import os, re, pickle, time
from datetime import date, datetime
from collections import namedtuple
from kernel.TrackerBook import trackersBook, chaptersBook, labsBook
from kernel.ComponentsBook import enablersBook, coordinationBook, toolsBook, tComponentsBook
from kernel.Backlog import Backlog
from kernel.Settings import settings


class BacklogFactory:
    _singlenton = None

    def __new__(cls, *args, **kwargs):
        if not cls._singlenton:
            cls._singlenton = super(BacklogFactory, cls).__new__(cls, *args, **kwargs)
        return cls._singlenton

    def __init__(self):
        self.trackersData = dict()
        for trackername in trackersBook:
            tracker = trackersBook[trackername]
            self.trackersData[tracker.key] = self.__load(trackername)

    def _load(self, trackername):
        fileList = os.listdir(settings.storeHome)
        mfilter = re.compile(r'\bFIWARE\.tracker\.(?P<tracker>[\w\-]+)\.(?P<day>\d{8})[-](?P<hour>\d{4})\.pkl\b')
        record = namedtuple('record', 'tracker, filename, day, time')
        files = [record(mfilter.match(f).group('tracker'),
                                   mfilter.match(f).group(0),
                                   mfilter.match(f).group('day'),
                                   mfilter.match(f).group('hour'))
                            for f in fileList if mfilter.match(f) if mfilter.match(f).group('tracker') == trackername]

        # print(files)
        files.sort(key=lambda e: (e.day, e.time), reverse=True)
        filename = files[0].filename
        _timestamp = '{}-{}'.format(files[0].day, files[0].time)
        timestamp = datetime.strptime(_timestamp, '%Y%m%d-%H%M').strftime("%Y%m%d-%H:%M")
        # print(timestamp)

        with open(os.path.join(settings.storeHome, filename), 'rb') as f:
            data = pickle.load(f)

        return data, timestamp

    def __load(self, trackername):
        filename = 'FIWARE.Engine.Tracker.{}.pkl'.format(trackername)
        with open(os.path.join(settings.storeHome, filename), 'rb') as f:
            timestamp, data= pickle.load(f)
        return data, timestamp

    def getChapterBacklog(self, chaptername):
        trackerkey = trackersBook[chaptername].keystone
        #print(chaptername, trackerkey)
        start_time = time.time()
        #trackerData, timestamp = self.trackersData[trackerkey]
        backlog =  Backlog.fromData(*self.trackersData[trackerkey])
        #print('{}-{}: time = {}'.format(chaptername, trackerkey, time.time() - start_time))
        return backlog

    def getEnablerBacklog(self, enablername):
        start_time = time.time()
        enabler = enablersBook[enablername]
        trackerData, timestamp = self.trackersData[enabler.tracker]
        data = list()
        for item in trackerData:
            try:key = item['fields']['components'][0]['id']
            except Exception: continue
            if enabler.key == key: data.append(item)
        backlog = Backlog.fromData(data, timestamp)
        #print('{}-{}: time = {}'.format(enablername, enablersBook[enablername].chapter, time.time() - start_time))
        return backlog

    def getToolBacklog(self, toolname):
        tool = toolsBook[toolname]
        trackerData, timestamp = self.trackersData[tool.tracker]
        data = list()
        for item in trackerData:
            try:key = item['fields']['components'][0]['id']
            except Exception: continue
            if tool.key == key: data.append(item)
        backlog = Backlog.fromData(data, timestamp)
        #print('{}-{}: time = {}'.format(enablername, enablersBook[enablername].chapter, time.time() - start_time))
        return backlog

    def getCoordinationBacklog(self, coordinationkey):
        coordination = coordinationBook[coordinationkey]
        trackerData, timestamp = self.trackersData[coordination.tracker]
        data = list()
        for item in trackerData:
            try:
                key = item['fields']['components'][0]['id']
            except Exception:
                continue

            if coordination.key == key:
                data.append(item)

        backlog = Backlog.fromData(data, timestamp)

        return backlog

    def getTechChaptersBacklog(self):
        data = list()
        _timestamp = list()

        for chaptername in chaptersBook:
            trackerkey = chaptersBook[chaptername].keystone
            trackerData, timestamp = self.trackersData[trackerkey]
            data.extend(trackerData)
            _timestamp.extend(timestamp)

        backlog = Backlog.fromData(data, max(_timestamp))

        return backlog

    def getLabChapterBacklog(self):
        data = list()
        _timestamp = list()

        for labname in labsBook:
            trackerkey = labsBook[labname].keystone
            trackerData, timestamp = self.trackersData[trackerkey]
            data.extend(trackerData)
            _timestamp.extend(timestamp)

        backlog = Backlog.fromData(data, max(_timestamp))

        return backlog


if __name__ == "__main__":
    pass


