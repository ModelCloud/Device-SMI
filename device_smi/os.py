import os
import platform
import re

from .base import BaseDevice, BaseMetrics, _run


class OSMetrics(BaseMetrics):
    pass


class OSDevice(BaseDevice):
    def __init__(self, cls):
        super().__init__(cls, "os")

        if platform.system().lower() == "linux" or platform.system().lower() == "freebsd" or platform.system().lower() == "solaris" or platform.system().lower() == "sunos":
            release_info = self.to_dict(_run(["cat", "/etc/os-release"]).replace("\"", "").lower(), "=")
            cls.name = release_info["name"]

            cls.version = release_info["version_id"]
            match = re.match(r"(\d+\.\d+)", cls.version)
            if match:
                cls.version = match.group(1)

            cls.arch = _run(["uname", "-m"]).lower()
        elif platform.system().lower() == "darwin":
            release_info = self.to_dict(_run(["sw_vers"]).lower())
            cls.name = release_info["productname"]
            cls.version = release_info["productversion"]
            cls.arch = _run(["uname", "-m"]).lower()
        elif platform.system().lower() == "windows":
            result = _run(["wmic", "os", "get", "caption,version", "/format:csv"]).strip().split("\n")[1].split(",")
            name = result[1]
            version = result[2]
            name = name.lower().removeprefix("microsoft").strip()
            cls.name = name
            cls.version = version
            cls.arch = os.environ.get("PROCESSOR_ARCHITECTURE").lower()
        else:
            cls.name = platform.system().lower()
            cls.version = platform.version().lower()
            cls.arch = platform.architecture()[0].lower().strip()

        if cls.arch in ["amd64", "x64", "64bit"]:
            cls.arch = "x86_64"
        if cls.arch in ["i386", "i86pc"]:
            cls.arch = "x86"

    def metrics(self):
        pass
