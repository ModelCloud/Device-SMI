class BaseInfo:
    def __init__(self, name: str, model: str, manufacture: str, memory_total: int, memory_used: int, memory_process: int, utilization: float):
        self.name = name
        self.model = model
        self.manufacture = manufacture
        self.memory_total = memory_total
        self.memory_used = memory_used
        self.memory_process = memory_process
        self.utilization = utilization
