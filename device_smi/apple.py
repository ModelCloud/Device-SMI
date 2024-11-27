import subprocess

from .base import BaseDevice, BaseInfo, BaseMetrics


class AppleGPU(BaseInfo):
    pass  # TODO, add PCIE & DRIVER


class AppleGPUMetrics(BaseMetrics):
    pass


class AppleDevice(BaseDevice):
    def __init__(self, index: int = 0):
        super().__init__(index)
        self.gpu_id = 0
        self._info = self.info()

    def info(self) -> AppleGPU:
        args = ["system_profiler", "SPDisplaysDataType"]

        result = subprocess.run(
            args=args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        output = result.stdout.strip().split("\n")
        model = ""
        vendor = ""
        for o in output:
            if "Chipset Model" in o:
                model = o.split(":")[1].replace("Apple", "").strip()
            if "Vendor" in o:
                vendor = o.split(":")[1].strip().split(" ")[0].strip()

        memory_total = int(subprocess.check_output(["sysctl", "-n", "hw.memsize"]))

        return AppleGPU(
            type="gpu",
            model=model.lower(),
            memory_total=memory_total,  # bytes
            vendor=vendor.lower(),
        )

    def metrics(self):
        result = subprocess.run(
            ["top", "-l", "1", "-stats", "cpu"], stdout=subprocess.PIPE
        )
        output = result.stdout.decode("utf-8")

        for line in output.splitlines():
            if line.startswith("CPU usage"):
                parts = line.split()
                user_time = float(parts[2].strip("%"))
                sys_time = float(parts[4].strip("%"))
                utilization = user_time + sys_time

        total_memory = int(subprocess.check_output(['sysctl', 'hw.memsize']).split(b':')[1].strip())
        free_memory = int(subprocess.check_output(['sysctl', 'vm.page_free_count']).split(b':')[1].strip())
        page_size = int(subprocess.check_output(['sysctl', 'hw.pagesize']).split(b':')[1].strip())

        used_memory = total_memory - (free_memory * page_size)

        return AppleGPUMetrics(
            memory_used=int(used_memory),  # bytes
            memory_process=0,  # Bytes, TODO, get this
            utilization=float(utilization),
        )
