from abc import abstractmethod


class Device():
    def __init__(self, index: int = 0):
        self.index = index

    @abstractmethod
    def info(self):
        pass
