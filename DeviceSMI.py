import subprocess

import psutil

DEVICE_NAME = "Name"
MEMORY_TOTAL = "Memory"
MEMORY_USED = "Memory-in-use"
UTILIZATION = "Utilization"
PCIE_BUS_ID = "PCIe Bus ID"
PCIE_GEN = "PCIe Gen"
PCIE_LINK = "PCIe Link"
DRIVER_VERSION = "Driver Version"
MANUFACTURE = "Manufacturer"


class DeviceSMI():
    def __init__(self, device):
        self.device = device

    def get_device_info(self):
        if self.device.type == 'cuda':  # TODO, get info by device
            try:
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,utilization.gpu,pci.bus_id,pci.link.gen.current,pci.link.width.current,driver_version',
                     '--format=csv,noheader,nounits'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if result.returncode != 0:
                    raise RuntimeError(result.stderr)

                output = result.stdout.strip().split('\n')[0]
                name, total_memory, used_memory, utilization, pci_bus_id, pcie_gen, pcie_width, driver_version = output.split(', ')

                return {
                    DEVICE_NAME: name,
                    MEMORY_TOTAL: int(total_memory),
                    MEMORY_USED: int(used_memory),
                    UTILIZATION: int(utilization),
                    PCIE_BUS_ID: pci_bus_id,
                    PCIE_GEN: f"Gen{pcie_gen}",
                    PCIE_LINK: f"x{pcie_width}",
                    DRIVER_VERSION: driver_version,
                }
            except FileNotFoundError:
                return {"Error": "nvidia-smi command not found. Ensure NVIDIA drivers are installed."}
            except Exception as e:
                return {"Error": str(e)}
        elif self.device.type == 'cpu':
            cpu_info = {
                DEVICE_NAME: "CPU",
                MANUFACTURE: "Generic" if psutil.MACOS else "Intel/AMD",
                UTILIZATION: psutil.cpu_percent(interval=1),
                MEMORY_USED: psutil.virtual_memory().percent,
            }
            return cpu_info
        else:
            return {"Error": "Device not supported or unavailable"}
