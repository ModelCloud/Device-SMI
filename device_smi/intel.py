import json
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
            args = ["xpu-smi", "discovery", "-d", f"{self.gpu_id}", "-j"]

            result = subprocess.run(
                args=args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            if result.returncode != 0:
                raise RuntimeError(result.stderr)

            data = json.loads(result.stdout)

            model = data["device_name"]

            if model and model.lower().startswith("intel(r)"):
                model = model[8:].strip()
            vendor = data["vendor_name"]
            if vendor and vendor.lower().startswith("intel"):
                vendor = "Intel"
            total_memory = data["max_mem_alloc_size_byte"]

            return IntelGPU(
                type="gpu",
                model=model.lower(),
                memory_total=int(total_memory),  # bytes
                vendor=vendor.lower(),
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

            # xpu-smi dump -d 0 -m 0,1,2 -i 1 -n 5
            # Timestamp, DeviceId, GPU Utilization (%), GPU Power (W), GPU Frequency (MHz)
            # 06:14:46.000,    0, 0.00, 14.61,    0

            output = result.stdout.strip().split("\n")[-1]
            memory_used = output.split(",")[-1].strip()
            utilization = output.split(",")[-2].strip()
            if utilization.lower() == "n/a":
                utilization = "0.0"

            return IntelGPUMetrics(
                memory_used=int(float(memory_used) * 1024 * 1024),  # bytes
                memory_process=0,
                utilization=float(utilization),
            )
        except FileNotFoundError:
            raise FileNotFoundError("'xpu-smi' command not found. Please ensure it is installed")
        except Exception as e:
            raise e
