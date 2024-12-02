import json
import re

from .base import GPUDevice, BaseMetrics, _run, Pcie, GPU


class IntelGPUMetrics(BaseMetrics):
    pass


class IntelDevice(GPUDevice):
    def __init__(self, cls, index: int = 0):
        super().__init__(cls, index)
        self.gpu_id = index

        try:
            args = ["xpu-smi", "discovery", "-d", f"{self.gpu_id}", "-j"]

            result = _run(args=args)

            data = json.loads(result)

            model = data["device_name"]

            if model:
                model = model.lower().replace("intel(r)", "").replace("core(tm)", "").replace("cpu @", "")
                model = re.sub(r"\s?\d+(\.\d+)?ghz", "", model).strip()
            vendor = data["vendor_name"]
            if vendor and vendor.lower().startswith("intel"):
                vendor = "Intel"
            total_memory = data["max_mem_alloc_size_byte"]

            pcie_gen = int(data["pcie_generation"])
            pcie_speed = int(data["pcie_max_link_width"])
            pcie_id = data["pci_device_id"]
            driver = data["driver_version"]
            firmware = data["gfx_firmware_version"]

            cls.model = model.lower()
            cls.memory_total = int(total_memory)  # bytes
            cls.vendor = vendor.lower()
            cls.pcie = Pcie(gen=pcie_gen, speed=pcie_speed, id=pcie_id)
            cls.gpu = GPU(driver=driver, firmware=firmware)

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
            result = _run(args=args)

            # xpu-smi dump -d 0 -m 0,1,2 -i 1 -n 5
            # Timestamp, DeviceId, GPU Utilization (%), GPU Power (W), GPU Frequency (MHz)
            # 06:14:46.000,    0, 0.00, 14.61,    0

            output = result.split("\n")[-1]
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
