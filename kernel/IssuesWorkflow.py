__author__ = "Manuel Escriche <mev@tid.es>"

class IssuesWorkflow:
    # open, In Progress, Impeded, Closed,
    # bugs : Fixed, Rejected, Analysing
    def __init__(self):
        self.defined = ('Open',)
        self._process = ('In Progress', 'Impeded', 'Analysing', 'Fixed', 'Rejected')
        self.closed = ('Closed', )
        self.status = self.defined + self._process  + self.closed

    @property
    def started(self):
        return self._process + self.closed
    @property
    def onProcess(self): return self._process
    @property
    def future(self): return self.defined
    @property
    def present(self): return self.defined + self._process + self.closed
    @property
    def past(self): return self.closed

issuesWorkflow = IssuesWorkflow()

if __name__ == "__main__":
    pass
