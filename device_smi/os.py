import platform

from .base import BaseDevice, BaseMetrics


class OSMetrics(BaseMetrics):
    pass


class OSDevice(BaseDevice):
    def __init__(self, cls):
        super().__init__(0)

        cls.name = platform.system()
        cls.version = platform.version()
        cls.arch = platform.architecture()[0]

    def metrics(self):
        pass
