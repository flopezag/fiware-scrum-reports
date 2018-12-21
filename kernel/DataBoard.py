__author__ = 'Manuel Escriche'

from kernel.DataFactory import DataFactory
from kernel.ComponentsBook import helpdeskCompBook
from kernel.Settings import settings


class Data:
    @staticmethod
    def getHelpDeskTechChannel():
        tech_channel = helpdeskCompBook['Tech']
        return DataFactory(settings.storeHome).getComponentData(tech_channel.key)

    @staticmethod
    def getChapterHelpDesk(chapter):
        tech_channel = helpdeskCompBook['Tech']
        return DataFactory(settings.storeHome).getComponentData(tech_channel.key)

    @staticmethod
    def getEnablerHelpDesk(enabler):
        tech_channel = helpdeskCompBook['Tech']
        return DataFactory(settings.storeHome).getComponentData(tech_channel.key)

    @staticmethod
    def getHelpDeskLabChannel(period):
        lab_channel = helpdeskCompBook['Lab']
        return DataFactory(settings.storeHome, period).getComponentData(lab_channel.key)
