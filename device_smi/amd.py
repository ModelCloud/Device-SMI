import os
import re

from .base import GPU, BaseMetrics, GPUDevice, Pcie, _run


class AMDGPUMetrics(BaseMetrics):
    pass

class AMDDevice(GPUDevice):
    def __init__(self, cls, index):
        super().__init__(cls, index)
        self.gpu_id = self._get_gpu_id()

        try:
            args = ["amd-smi", "static", "--gpu", f"{self.gpu_id}"]

            result = self.to_dict(_run(args=args).lower())
            market_name = re.findall(r'\[(.*?)]', result["market_name"])[0]
            model = market_name.split("/")[0].strip()
            total_memory= result["size"].removesuffix("mb").strip()
            pci_bus_id = result["bdf"]
            pcie_gen = result['pcie_interface_version'].removeprefix("gen").strip()
            pcie_width = result['max_pcie_width']
            driver = result["driver"]
            features = [result['target_graphics_version']]

            args = ["amd-smi", "firmware", "--gpu", f"{self.gpu_id}"]
            lines = _run(args=args).lower().splitlines()

            result = {}
            current_id = None
            for line in lines:
                line = line.strip()
                if line.startswith("fw_id:"):
                    current_id = line.split(":")[1].strip()
                elif line.startswith("fw_version:") and current_id:
                    result[current_id] = line.split(":")[1].strip()
            firmware = f"{result}"

            if model.lower().startswith("amd"):
                model = model[len("amd"):]

            cls.model = model.strip().lower()
            cls.memory_total = int(total_memory) * 1024 * 1024  # bytes
            cls.vendor = "amd"
            cls.features = features
            cls.pcie = Pcie(gen=int(pcie_gen), speed=int(pcie_width), id=pci_bus_id)
            cls.gpu = GPU(driver=driver, firmware=firmware)
        except FileNotFoundError:
            raise FileNotFoundError()
        except Exception as e:
            raise e

    def _get_gpu_id(self):
        hips = os.environ.get("HIP_VISIBLE_DEVICES", "")
        hip_list = hips.split(",") if hips else []
        if hip_list and len(hip_list) > self.index:
            return hip_list[self.index]
        else:
            return str(self.index)

    def metrics(self):
        try:
            args = ["amd-smi", f"--id={self.gpu_id}", "--query-gpu=memory.used,utilization.gpu",
                    "--format=csv,noheader,nounits"]
            used_memory, utilization = _run(args=args, seperator="\n")[0].split(", ")

            return AMDGPUMetrics(
                memory_used=int(used_memory) * 1024 * 1024,  # bytes
                memory_process=0,  # Bytes, TODO, get this
                utilization=float(utilization),
            )

        except FileNotFoundError:
            raise FileNotFoundError(
                "The 'amd-smi' command was not found. Please ensure that the 'amd-utils' package is installed."
            )
        except Exception as e:
            raise e
