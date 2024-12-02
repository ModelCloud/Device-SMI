import platform

from .base import BaseDevice, BaseMetrics, _run


class OSMetrics(BaseMetrics):
    pass


class OSDevice(BaseDevice):
    def __init__(self, cls):
        super().__init__(cls, "os")

        if platform.system().lower() == "linux" or platform.system().lower() == "freebsd" or platform.system().lower() == "solaris":
            release_info = self.to_dict(_run(["cat", "/etc/os-release"]).replace("\"", "").lower(), "=")
            cls.name = release_info["name"]
            cls.version = release_info["version_id"]
            cls.arch = _run(["uname", "-m"])
            return
        if platform.system().lower() == "darwin":
            release_info = self.to_dict(_run(["sw_vers"]).lower())
            cls.name = release_info["productname"]
            cls.version = release_info["productversion"]
            cls.arch = _run(["uname", "-m"])
            return


        cls.name = platform.system().lower()
        cls.version = platform.version().lower()  # TODO, get distribution name
        cls.arch = platform.architecture()[0].lower().strip()  # TODO, get x86

    def metrics(self):
        pass
