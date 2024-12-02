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
            cls.name = release_info["name"].replace("oracle", "").strip()

            cls.version = release_info["version_id"]
            match = re.match(r"(\d+\.\d+)", cls.version)
            if match:
                cls.version = match.group(1)

            cls.kernel, cls.arch = _run(["uname", "-mr"]).lower().split()
        elif platform.system().lower() == "darwin":
            release_info = self.to_dict(_run(["sw_vers"]).lower())
            cls.name = release_info["productname"]
            cls.version = release_info["productversion"]
            cls.kernel, cls.arch = _run(["uname", "-mr"]).lower().split()
        elif platform.system().lower() == "windows":
            command_result = _run(["wmic", "os", "get", "caption", "/format:csv"]).strip()
            command_result = re.sub(r'\n+', '\n', command_result)  # windows uses \n\n
            result = command_result.split("\n")[1].split(",")
            cls.name = "windows"
            cls.version = result[1].lower().removeprefix("microsoft windows").strip()
            cls.arch = os.environ.get("PROCESSOR_ARCHITECTURE").lower()

            cls.kernel = _run(["cmd", "/c", "ver"])
            match = re.search(r'(\d+\.\d+\.\d+\.\d+)', cls.kernel)
            if match:
                cls.kernel = match.group(1)
        else:
            cls.name = platform.system().lower()
            cls.version = platform.version().lower()
            cls.arch = platform.architecture()[0].lower().strip()

        if cls.arch in ["amd64", "x64"]:
            cls.arch = "x86_64"
        if cls.arch in ["i386", "i86pc"]:
            cls.arch = "x86"
        if cls.arch in ["arm64"]:
            cls.arch = "aarch64"

    def metrics(self):
        pass
