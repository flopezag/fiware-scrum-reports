__author__ = "Manuel Escriche <mev@tid.es>"

class BacklogIssuesModel:
    def __init__(self):
        self.__entryTypes = ('Epic', 'Feature', 'Story', 'Bug', 'WorkItem')
        self.longTermTypes = ('Epic',)
        self.midTermTypes = ('Feature',)
        self.shortTermTypes = ('Story','Bug','WorkItem')

    @property
    def types(self): return self.__entryTypes
    @property
    def story(self): return ('Story',)
    @property
    def operativeTypes(self): return self.shortTermTypes + self.midTermTypes
    @property
    def organizingTypes(self): return self.longTermTypes
    @property
    def open(self):
        return self.longTermTypes + self.midTermTypes
    @property
    def private(self):
        return self.shortTermTypes
    @property
    def workitem(self):
        return 'WorkItem'


backlogIssuesModel = BacklogIssuesModel()

if __name__ == "__main__":
    pass
