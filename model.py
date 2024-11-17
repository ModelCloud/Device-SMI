class BaseInfo:
    def __init__(self,
                 name: str = "UNKNOWN",
                 model: str = "UNKNOWN",
                 manufacture: str = "UNKNOWN",
                 memory_total: int = 0,
                 memory_used: int = 0,
                 memory_process: int = 0,
                 utilization: float = 0.0,
                 ):
        self.name = name
        self.model = model
        self.manufacture = manufacture
        self.memory_total = memory_total
        self.memory_used = memory_used
        self.memory_process = memory_process
        self.utilization = utilization
