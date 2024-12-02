import platform

from .base import BaseDevice, BaseMetrics


class OSMetrics(BaseMetrics):
    pass


class OSDevice(BaseDevice):
    def __init__(self, cls):
        super().__init__(0)

        cls.type = "os"
        cls.name = platform.system().lower()
        cls.version = platform.version().lower()
        cls.arch = platform.architecture()[0].lower().removesuffix("bit").strip()

    def metrics(self):
        pass
