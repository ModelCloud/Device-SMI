from .base import GPUDevice, BaseMetrics, _run


class AppleGPUMetrics(BaseMetrics):
    pass


class AppleDevice(GPUDevice):
    def __init__(self, cls, index):
        super().__init__(cls, index)
        self.gpu_id = 0

        args = ["system_profiler", "SPDisplaysDataType"]

        result = _run(args=args)

        output = result.split("\n")
        model = ""
        vendor = ""
        for o in output:
            if "Chipset Model" in o:
                model = o.split(":")[1].replace("Apple", "").strip()
            if "Vendor" in o:
                vendor = o.split(":")[1].strip().split(" ")[0].strip()

        memory_total = int(_run(["sysctl", "-n", "hw.memsize"]))

        cls.model = model.lower()
        cls.memory_total = memory_total  # bytes
        cls.vendor = vendor.lower()

    def metrics(self):
        output = _run(["top", "-l", "1", "-stats", "cpu"])

        utilization = "0.0"
        for line in output.splitlines():
            if line.startswith("CPU usage"):
                parts = line.split()
                user_time = float(parts[2].strip("%"))
                sys_time = float(parts[4].strip("%"))
                utilization = user_time + sys_time

        total_memory = int(_run(['sysctl', 'hw.memsize']).split(':')[1].strip())
        free_memory = int(_run(['sysctl', 'vm.page_free_count']).split(':')[1].strip())
        page_size = int(_run(['sysctl', 'hw.pagesize']).split(':')[1].strip())

        used_memory = total_memory - (free_memory * page_size)

        return AppleGPUMetrics(
            memory_used=int(used_memory),  # bytes
            memory_process=0,  # Bytes, TODO, get this
            utilization=float(utilization),
        )
