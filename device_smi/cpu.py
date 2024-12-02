import os
import platform

from .base import BaseDevice, BaseMetrics, _run


class CPUMetrics(BaseMetrics):
    pass


class CPUDevice(BaseDevice):
    def __init__(self, cls):
        super().__init__(cls, "cpu")

        model = "Unknown Model"
        vendor = "Unknown vendor"
        flags = set()
        try:
            with open("/proc/cpuinfo", "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith("flags"):
                        flags.update(line.strip().split(":")[1].split())
                    if line.startswith("model name"):
                        model = line.split(":")[1].strip()

                        if "amd" in model.lower():
                            if "epyc" in model.lower():
                                split = model.split(" ")
                                model = " ".join(split[1:3])
                            elif "ryzen" in model.lower():
                                split = model.split(" ")
                                model = " ".join(split[1:4])
                        elif "intel" in model.lower():
                            model = model.split(" ")[-1]

                    elif line.startswith("vendor_id"):
                        vendor = line.split(":")[1].strip()
        except FileNotFoundError:
            if platform.system() == "Darwin":
                model = (
                    _run(["sysctl", "-n", "machdep.cpu.brand_string"])
                    .replace("Apple", "")
                    .strip()
                )
                try:
                    vendor = (_run(["sysctl", "-n", "machdep.cpu.vendor"]))
                except BaseException:
                    vendor = "Apple"
            else:
                model = platform.processor()
                vendor = platform.uname().system

        if platform.system() == "Darwin":
            sysctl_info = self.to_dict(_run(["sysctl", "-a"]))
            cpu_count = 1
            cpu_cores = int(sysctl_info["hw.physicalcpu"])
            cpu_threads = int(sysctl_info["hw.logicalcpu"])

            mem_total = int(_run(["sysctl", "-n", "hw.memsize"]))

            try:
                features = sysctl_info["machdep.cpu.features"].splitlines()
            except Exception:
                # machdep.cpu.features is not available on arm arch
                features = []

            flags = set(features)
        else:

            cpu_info = self.to_dict(_run(['lscpu']))

            cpu_count = int(cpu_info["Socket(s)"])
            cpu_thread_per_core = int(cpu_info["Thread(s) per core"])
            cpu_cores_per_socket = int(cpu_info["Core(s) per socket"])
            cpu_cores = cpu_thread_per_core * cpu_cores_per_socket
            cpu_threads = int(cpu_info["CPU(s)"])

            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
                mem_total = 0
                for line in lines:
                    if line.startswith("MemTotal:"):
                        mem_total = int(line.split()[1]) * 1024
                        break

        if "intel" in vendor.lower():
            vendor = "Intel"
        elif "amd" in vendor.lower():
            vendor = "AMD"

        cls.model = model.lower()
        cls.vendor = vendor.lower()
        cls.memory_total = mem_total  # Bytes
        self.memory_total = mem_total  # Bytes
        cls.count = cpu_count
        cls.cores = cpu_cores
        cls.threads = cpu_threads
        cls.features = sorted(set(f.lower() for f in flags))

    def _utilization(self):
        # check if is macOS
        if platform.system() == "Darwin":
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
        total_time_1, idle_time_1 = self._utilization()
        # read CPU status second time here, read too quickly will get inaccurate results
        total_time_2, idle_time_2 = self._utilization()

        total_diff = total_time_2 - total_time_1
        idle_diff = idle_time_2 - idle_time_1

        # total_diff might be 0
        if total_diff == 0:
            utilization = 0
        else:
            if platform.system() == "Darwin":
                utilization = idle_time_2 - idle_time_1
            else:
                utilization = (1 - (idle_diff / total_diff)) * 100

        if platform.system() == "Darwin":
            available_mem = _run(["vm_stat"])
            available_mem = available_mem.splitlines()

            free_pages = 0
            for line in available_mem:
                if "Pages free" in line:
                    free_pages = int(line.split(":")[1].strip().replace(".", ""))
                    break

            mem_free = free_pages * 16384
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
        if platform.system() == "Darwin":
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
