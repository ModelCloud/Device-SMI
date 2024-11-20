import os
import platform
import subprocess

from .base import BaseDevice, BaseInfo, BaseMetrics


class IntelGPU(BaseInfo):
    pass  # TODO, add PCIE & DRIVER


class IntelGPUMetrics(BaseMetrics):
    pass


class IntelDevice(BaseDevice):
    def __init__(self, index: int = 0):
        super().__init__(index)
        self.gpu_id = index
        self._info = self.info()


    def info(self) -> IntelGPU:
        try:
            args = ["xpu-smi", "discovery", "-d", f"{self.gpu_id}"]

            result = subprocess.run(
                args=args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            if result.returncode != 0:
                raise RuntimeError(result.stderr)

            for output in result.stdout.strip().split("\n"):
                if "device name" in output.lower():
                    model = output.split(":")[1].split("(")[0].strip()
                if "vendor" in output.lower():
                    vendor = output.split(":")[1].split("(")[0].strip()
                if "Memory Physical Size" in output.lower():
                    total_memory = output.split(":")[1].strip().split(" ")[0]

            return IntelGPU(
                type="gpu",
                model=model,
                memory_total=int(total_memory) * 1024,  # bytes
                vendor=vendor,
            )

        except FileNotFoundError:
            raise FileNotFoundError("'xpu-smi' command not found. Please ensure it is installed")
        except Exception as e:
            raise e

    def metrics(self):
        try:
            args = [
                "xpu-smi", "dump",
                "-d", f"{self.gpu_id}",
                "-m", "0,18",
                "-n", "1"
            ]
            result = subprocess.run(
                args=args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            if result.returncode != 0:
                raise RuntimeError(result.stderr)

            #xpu-smi dump -d 0 -m 0,1,2 -i 1 -n 5
            #Timestamp, DeviceId, GPU Utilization (%), GPU Power (W), GPU Frequency (MHz)
            #06:14:46.000,    0, 0.00, 14.61,    0

            output = result.stdout.strip().split("\n")[-1]
            memory_used = output.split(",")[-1].strip()
            utilization = output.split(",")[-2].strip()

            return IntelGPUMetrics(
                memory_used=int(memory_used) * 1024,  # bytes
                memory_process=0,  # Bytes, TODO, get this
                utilization=float(utilization),
            )
        except FileNotFoundError:
            raise FileNotFoundError("'xpu-smi' command not found. Please ensure it is installed")
        except Exception as e:
            raise e
