__author__ = 'Manuel Escriche'

import os
import pickle
from kernel.Settings import settings


class Recorder:
    def __init__(self, filename):
        self.filename = filename

    def __getstate__(self):
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

    def save(self):
        longFilename = os.path.join(settings.storeHome, self.filename)
        with open(longFilename, 'wb') as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)

    @classmethod
    def fromFile(cls, filename):
        with open(os.path.join(settings.storeHome, filename), 'rb') as f:
            return pickle.load(f)


if __name__ == "__main__":
    pass
