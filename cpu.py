import os
import platform

from device import Device
from model import BaseInfo


class CPUInfo(BaseInfo):
    pass # TODO extend for cpu

class CPUDevice(Device):
    def __init__(self, index: int = 0):
        super().__init__(index)

    def info(self) -> CPUInfo:
        def cpu_utilization():
            with open('/proc/stat', 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith('cpu '):
                        parts = line.split()
                        total_time = sum(int(part) for part in parts[1:])
                        idle_time = int(parts[4])
                        return total_time, idle_time

        total_time_1, idle_time_1 = cpu_utilization()

        model = "Unknown Model"
        manufacturer = "Unknown Manufacturer"
        try:
            with open('/proc/cpuinfo', 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith('model name'):
                        model = line.split(':')[1].strip()

                        if "amd" in model.lower():
                            if "epyc" in model.lower():
                                split = model.split(" ")
                                model = " ".join(split[1:3])
                            elif "ryzen" in model.lower():
                                split = model.split(" ")
                                model = " ".join(split[1:4])
                        elif "intel" in model.lower():
                            model = model.split(" ")[-1]

                    elif line.startswith('vendor_id'):
                        manufacturer = line.split(':')[1].strip()
        except FileNotFoundError:
            model = platform.processor()
            manufacturer = platform.uname().system

        # read CPU status second time here, read too quickly will get inaccurate results
        total_time_2, idle_time_2 = cpu_utilization()

        total_diff = total_time_2 - total_time_1
        idle_diff = idle_time_2 - idle_time_1
        # total_diff might be 0
        if total_diff == 0:
            utilization = 0
        else:
            utilization = (1 - (idle_diff / total_diff)) * 100


        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
            mem_total = mem_free = 0
            for line in lines:
                if line.startswith('MemTotal:'):
                    mem_total = int(line.split()[1]) * 1024
                elif line.startswith('MemAvailable:'):
                    mem_free = int(line.split()[1]) * 1024
                    break
        memory_total = mem_total
        memory_used = memory_total - mem_free

        process_id = os.getpid()
        with open(f'/proc/{process_id}/status', 'r') as f:
            lines = f.readlines()
            memory_current_process = 0
            for line in lines:
                if line.startswith('VmRSS:'):
                    memory_current_process = int(line.split()[1]) * 1024
                    break

        if 'intel' in manufacturer.lower():
            manufacturer = 'Intel'
        elif 'amd' in manufacturer.lower():
            manufacturer = 'AMD'

        return CPUInfo(type="CPU",
                        model=model,
                        manufacture=manufacturer,
                        memory_total=memory_total,  # Bytes
                        memory_used=memory_used,  # Bytes
                        memory_process=memory_current_process,  # Bytes
                        utilization=utilization,)
