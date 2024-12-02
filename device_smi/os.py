import platform

from .base import BaseDevice, BaseMetrics, _run


class OSMetrics(BaseMetrics):
    pass


class OSDevice(BaseDevice):
    def __init__(self, cls):
        super().__init__(cls, "os")

        if platform.system().lower() == "linux":
            release_info = self.to_dict(_run(["cat", "/etc/os-release"]).replace("\"", "").lower(), "=")
            cls.name = release_info["name"]
            cls.version = release_info["version_id"]
            cls.arch = _run(["uname", "-m"])
            return

        cls.name = platform.system().lower()
        cls.version = platform.version().lower()  # TODO, get distribution name
        cls.arch = platform.architecture()[0].lower().strip()  # TODO, get x86

    def metrics(self):
        pass
