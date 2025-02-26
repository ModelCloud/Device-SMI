import re
import subprocess
from abc import abstractmethod
from typing import Optional

INSTALLATION_HINTS = {
    "lspci": "`lspci` is not installed, you can install it via `sudo apt install pciutils`.",
    "nvidia-smi": "`nvidia-smi` is not installed. You need to install NVIDIA driver support binaries by `sudo apt install nvidia-utils-<NVIDIA-DRIVER-VERSION>`",
    "powershell": "`PowerShell` is not installed. Please follow the instructions at `https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell`",
    "xpu-smi": "`xpu-smi` is not installed. Please follow the instructions at  https://github.com/intel/xpumanager/blob/master/doc/smi_install_guide.md`",
    "amd-smi": "`amd-smi` is not installed. Please follow the instructions at  `https://rocm.docs.amd.com/projects/amdsmi/en/latest/install/install.html`",
}

class BaseDevice:
    def __init__(self, cls, type: str):
        cls.type = type

    @abstractmethod
    def metrics(self):
        pass

    def __str__(self):
        return str(self.__dict__)

    def to_dict(self, text, split: str = ":"):
        return {k.strip(): v.strip() for k, v in (line.split(split, 1) for line in text.splitlines() if split in line)}


class GPUDevice(BaseDevice):
    def __init__(self, cls, index):
        super().__init__(cls, "gpu")
        self.index = index

    @abstractmethod
    def metrics(self):
        pass


class BaseMetrics:
    def __init__(
        self,
        memory_used: int = 0,
        memory_process: int = 0,
        utilization: float = 0.0,
    ):
        self.memory_used = memory_used
        self.memory_process = memory_process
        self.utilization = max(0.0, utilization)

    def __str__(self):
        return str(self.__dict__)


class Pcie:
    def __init__(self, gen: int, speed: int, id: str):
        self.gen = gen
        self.speed = speed
        self.id = id

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


class GPU:
    def __init__(self, driver: str, firmware: str):
        self.driver = driver
        self.firmware = firmware

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


def _run(args, line_start: Optional[str] = None, seperator: str=None): # -> str | list[str] disable type hint, because solaris test is using python 3.7 which doesn't support | usage
    try:
        result = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        install_hint = INSTALLATION_HINTS.get(args[0], f"Command not found: `{args[0]}`, please check if it was installed.")
        raise RuntimeError(install_hint)

    if result.returncode != 0 or result.stderr.strip() != "":
        raise RuntimeError(result.stderr)

    result = result.stdout.strip()
    result = re.sub(r'\n+', '\n', result) # remove consecutive \n
    if line_start:
        return " ".join([line for line in result.splitlines() if line.strip().startswith(line_start)])
    if seperator:
        return [l.strip() for l in result.split(seperator)]
    return result
