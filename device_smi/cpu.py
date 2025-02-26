import os
import platform
import re

from .base import BaseDevice, BaseMetrics, _run


class CPUMetrics(BaseMetrics):
    pass


class CPUDevice(BaseDevice):
    def __init__(self, cls):
        super().__init__(cls, "cpu")

        model = "Unknown Model"
        vendor = "Unknown vendor"
        flags = set()

        if platform.system().lower() == "windows":
            command_result = _run(["wmic", "cpu", "get", "manufacturer,name,numberofcores,numberoflogicalprocessors", "/format:csv"]).strip()
            result = command_result.split("\n")[1].split(",")

            cpu_count = command_result.count('\n')
            model = result[2].strip()
            cpu_cores = int(result[3])
            cpu_threads = int(result[4])
            vendor = result[1].strip()

            command_result = _run(["wmic", "os", "get", "TotalVisibleMemorySize", "/Value", "/format:csv"]).strip()
            result = command_result.split("\n")[1].split(",")

            mem_total = int(result[1])
        elif platform.system().lower() == 'darwin':
            model = (_run(["sysctl", "-n", "machdep.cpu.brand_string"]).replace("Apple", "").strip())
            try:
                vendor = (_run(["sysctl", "-n", "machdep.cpu.vendor"]))
            except BaseException:
                vendor = "apple"

            sysctl_info = self.to_dict(_run(["sysctl", "-a"]))
            cpu_count = 1
            cpu_cores = int(sysctl_info["hw.physicalcpu"])
            cpu_threads = int(sysctl_info["hw.logicalcpu"])

            mem_total = int(_run(["sysctl", "-n", "hw.memsize"]))

            try:
                features = sysctl_info["machdep.cpu.features"].splitlines()
            except Exception:
                features = []

            flags = set(features)
        elif os.name == 'posix':
            try:
                with open("/proc/cpuinfo", "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.startswith("flags"):
                            flags.update(line.strip().split(":")[1].split())
                        if line.startswith("model name"):
                            model = line.split(":")[1].strip()
                        elif line.startswith("vendor_id"):
                            vendor = line.split(":")[1].strip()
            except FileNotFoundError:
                model = platform.processor()
                vendor = platform.uname().system

            cpu_info = self.to_dict(_run(['lscpu']))

            cpu_count = int(cpu_info["Socket(s)"])
            cpu_cores_per_socket = int(cpu_info["Core(s) per socket"])
            cpu_cores = cpu_count * cpu_cores_per_socket
            cpu_threads = int(cpu_info["CPU(s)"])

            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
                mem_total = 0
                for line in lines:
                    if line.startswith("MemTotal:"):
                        mem_total = int(line.split()[1]) * 1024
                        break
        else:
            print("not support")

        model = " ".join(i for i in model.lower().split() if not any(x in i for x in ["ghz", "cpu", "(r)", "(tm)", "intel", "amd", "core", "processor", "@"]))
        cls.model = model

        if "intel" in vendor.lower():
            vendor = "intel"
        elif "amd" in vendor.lower():
            vendor = "amd"
        cls.vendor = vendor.lower().replace("authentic", "")
        cls.memory_total = mem_total  # Bytes
        self.memory_total = mem_total  # Bytes
        cls.count = cpu_count
        cls.cores = cpu_cores
        cls.threads = cpu_threads
        cls.features = sorted({f.lower() for f in flags})

    def _utilization(self):
        # check if is macOS
        if platform.system().lower() == "darwin":
            output = _run(["top", "-l", "1", "-stats", "cpu"])

            # CPU usage: 7.61% user, 15.23% sys, 77.15% idle
            for line in output.splitlines():
                if line.startswith("CPU usage"):
                    parts = line.split()
                    user_time = float(parts[2].strip("%"))
                    sys_time = float(parts[4].strip("%"))
                    idle_time = float(parts[6].strip("%"))
                    total_time = user_time + sys_time + idle_time
                    return total_time, idle_time
        else:
            with open("/proc/stat", "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith("cpu "):
                        parts = line.split()
                        total_time = sum(int(part) for part in parts[1:])
                        idle_time = int(parts[4])
                        return total_time, idle_time

    def metrics(self):
        if platform.system().lower() == "windows":
            if platform.system().lower() == "windows":
                command_result = _run(["wmic", "cpu", "get", "loadpercentage"]).strip()
                try:
                    result = command_result.split("\n")[1].split(",")
                    utilization = int(result[0])
                except BaseException as e:
                    print("error occurred, command_result: ")
                    print(f"{command_result}")
                    print("------------")
                    raise e

                try:
                    command_result = _run(["wmic", "os", "get", "FreePhysicalMemory"]).strip()
                    result = command_result.split("\n")[1].split(",")
                    memory_used = int(result[0])
                except BaseException as e:
                    print("error occurred, command_result: ")
                    print(f"{command_result}")
                    print("------------")
                    raise e
                return CPUMetrics(
                    memory_used=memory_used,  # bytes
                    memory_process=0,  # bytes
                    utilization=utilization,
                )

        total_time_1, idle_time_1 = self._utilization()
        # read CPU status second time here, read too quickly will get inaccurate results
        total_time_2, idle_time_2 = self._utilization()

        total_diff = total_time_2 - total_time_1
        idle_diff = idle_time_2 - idle_time_1

        # total_diff might be 0
        if total_diff <= 0:
            utilization = 0
        else:
            if platform.system().lower() == "darwin":
                utilization = idle_time_2 - idle_time_1
            else:
                utilization = (1 - (idle_diff / total_diff)) * 100

        if platform.system().lower() == "darwin":
            available_mem = _run(["vm_stat"]).replace(".", "").lower()

            result = self.to_dict(available_mem)

            available_mem = available_mem.splitlines()
            page_size = int(re.findall(r'\d+', available_mem[0])[0])

            free_pages = int(result["pages free"])

            mem_free = free_pages * page_size
        else:
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
                mem_free = 0
                for line in lines:
                    if line.startswith("MemAvailable:"):
                        mem_free = int(line.split()[1]) * 1024
                        break

        memory_used = self.memory_total - mem_free

        process_id = os.getpid()
        if platform.system().lower() == "darwin":
            result = _run(["ps", "-p", str(process_id), "-o", "rss="])
            memory_current_process = int(result) * 1024
        else:
            with open(f"/proc/{process_id}/status", "r") as f:
                lines = f.readlines()
                memory_current_process = 0
                for line in lines:
                    if line.startswith("VmRSS:"):
                        memory_current_process = int(line.split()[1]) * 1024
                        break

        return CPUMetrics(
            memory_used=memory_used,  # bytes
            memory_process=memory_current_process,  # bytes
            utilization=utilization,
        )
