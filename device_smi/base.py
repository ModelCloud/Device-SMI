import subprocess
from abc import abstractmethod


class BaseDevice:
    def __init__(self, type: str):
        self.type = type

    @abstractmethod
    def metrics(self):
        pass

    def __str__(self):
        return str(self.__dict__)


class BaseInfo:
    def __init__(
        self,
        type: str = "UNKNOWN",
        model: str = "UNKNOWN",
        vendor: str = "UNKNOWN",
        memory_total: int = 0,
    ):
        self.type = type
        self.model = model
        self.vendor = vendor
        self.memory_total = memory_total

    def __str__(self):
        return str(self.__dict__)


class BaseMetrics:
    def __init__(
        self,
        memory_used: int = 0,
        memory_process: int = 0,
        utilization: float = 0.0,
    ):
        self.memory_used = memory_used
        self.memory_process = memory_process
        self.utilization = utilization

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


def _run(args, line_start: str = None) -> str:
    result = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0 or result.stderr.strip() != "":
        raise RuntimeError(result.stderr)

    result = result.stdout.strip()
    if line_start:
        return " ".join([line for line in result.splitlines() if line.strip().startswith(line_start)])
    return result
