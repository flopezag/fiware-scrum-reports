__author__ = 'Manuel Escriche'

from kernel.DataFactory import DataFactory
from kernel.ComponentsBook import helpdeskCompBook
from kernel.Settings import settings


class Data:
    @staticmethod
    def getHelpDeskTechChannel():
        techChannel = helpdeskCompBook['Tech']
        return DataFactory(settings.storeHome).getComponentData(techChannel.key)

    @staticmethod
    def getChapterHelpDesk(chapter):
        techChannel = helpdeskCompBook['Tech']
        return DataFactory(settings.storeHome).getComponentData(techChannel.key)

    @staticmethod
    def getEnablerHelpDesk(enabler):
        techChannel = helpdeskCompBook['Tech']
        return DataFactory(settings.storeHome).getComponentData(techChannel.key)
