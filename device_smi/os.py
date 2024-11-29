import platform

from .base import BaseDevice, BaseMetrics


class OSMetrics(BaseMetrics):
    pass


class Properties():
    def __init__(self, version: str, name: str, arch: str):
        self.version = version
        self.name = name
        self.arch = arch

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


class OSDevice(BaseDevice):
    def __init__(self, cls):
        super().__init__(0)

        cls.name = platform.system()
        cls.version = platform.version()
        cls.arch = platform.architecture()[0]

    def metrics(self):
        pass
