from abc import abstractmethod

class BaseDevice():
    def __init__(self, index: int = 0):
        self.index = index

    @abstractmethod
    def info(self):
        pass

class BaseInfo:
    def __init__(self,
                 type: str = "UNKNOWN",
                 model: str = "UNKNOWN",
                 vendor: str = "UNKNOWN",
                 memory_total: int = 0,
                 memory_used: int = 0,
                 memory_process: int = 0,
                 utilization: float = 0.0,
                 ):
        self.type = type
        self.model = model
        self.vendor = vendor
        self.memory_total = memory_total
        self.memory_used = memory_used
        self.memory_process = memory_process
        self.utilization = utilization