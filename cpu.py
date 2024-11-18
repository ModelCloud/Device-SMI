import os
import platform
import subprocess

from device import Device
from model import BaseInfo


class CPUInfo(BaseInfo):
    pass # TODO extend for cpu

class CPUDevice(Device):
    def __init__(self, index: int = 0):
        super().__init__(index)

    def info(self) -> CPUInfo:
        def cpu_utilization():
            # check if is macos
            if platform.system() == 'Darwin':
                result = subprocess.run(['top', '-l', '1', '-stats', 'cpu'], stdout=subprocess.PIPE)
                output = result.stdout.decode('utf-8')

                # CPU usage: 7.61% user, 15.23% sys, 77.15% idle
                for line in output.splitlines():
                    if line.startswith('CPU usage'):
                        parts = line.split()
                        user_time = float(parts[2].strip('%'))
                        sys_time = float(parts[4].strip('%'))
                        idle_time = float(parts[6].strip('%'))
                        total_time = user_time + sys_time + idle_time
                        return total_time, idle_time
            else:
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
        vendor = "Unknown vendor"
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
                        vendor = line.split(':')[1].strip()
        except FileNotFoundError:
            if platform.system() == "Darwin":
                model = subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string']).decode().replace("Apple", "").strip()
                try:
                    vendor = subprocess.check_output(['sysctl', '-n', 'machdep.cpu.vendor']).decode().strip()
                except subprocess.CalledProcessError:
                    vendor = "Apple"
            else:
                model = platform.processor()
                vendor = platform.uname().system

        # read CPU status second time here, read too quickly will get inaccurate results
        total_time_2, idle_time_2 = cpu_utilization()

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


        if platform.system() == 'Darwin':
            mem_total = int(subprocess.check_output(['sysctl', '-n', 'hw.memsize']))

            available_mem = subprocess.check_output(['vm_stat'])
            available_mem = available_mem.decode().splitlines()

            free_pages = 0
            for line in available_mem:
                if "Pages free" in line:
                    free_pages = int(line.split(":")[1].strip().replace(".", ""))
                    break

            mem_free = free_pages * 16384

        else:
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
        if platform.system() == 'Darwin':
            result = subprocess.run(['ps', '-p', str(process_id), '-o', 'rss='], stdout=subprocess.PIPE)
            memory_current_process = int(result.stdout.decode().strip()) * 1024
        else:
            with open(f'/proc/{process_id}/status', 'r') as f:
                lines = f.readlines()
                memory_current_process = 0
                for line in lines:
                    if line.startswith('VmRSS:'):
                        memory_current_process = int(line.split()[1]) * 1024
                        break


        if 'intel' in vendor.lower():
            vendor = 'Intel'
        elif 'amd' in vendor.lower():
            vendor = 'AMD'

        return CPUInfo(type="CPU",
                        model=model,
                        vendor=vendor,
                        memory_total=memory_total,  # Bytes
                        memory_used=memory_used,  # Bytes
                        memory_process=memory_current_process,  # Bytes
                        utilization=utilization,)
