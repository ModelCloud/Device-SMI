import os
import subprocess

from device import Device
from model import BaseInfo


class NvidiaGPU(BaseInfo):
    pass # TODO, add PCIE & DRIVER


class NvidiaDevice(Device):
    def __init__(self, device):
        super().__init__(device)

    def info(self) -> NvidiaGPU:
        try:
            cudas = os.environ.get("CUDA_VISIBLE_DEVICES", "")
            cuda_list = cudas.split(",") if cudas else []

            if cuda_list and len(cuda_list) >= self.index:
                gpu_id = cuda_list[self.index]
            else:
                gpu_id = self.index  # or raise Exception?

            args = [
                'nvidia-smi',
                f'--id={gpu_id}',
                '--query-gpu='
                'name,'
                'memory.total,'
                'memory.used,'
                'utilization.gpu,'
                'pci.bus_id,'
                'pcie.link.gen.max,'
                'pcie.link.gen.current,'
                'driver_version',
                '--format=csv,noheader,nounits'
            ]
            print(f"command: {''.join(args).replace('--', ' --')}")
            result = subprocess.run(
                args=args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:
                raise RuntimeError(result.stderr)

            output = result.stdout.strip().split('\n')[0]
            name, total_memory, used_memory, utilization, pci_bus_id, pcie_gen, pcie_width, driver_version = output.split(', ')

            return NvidiaGPU(type="GPU",
                             model=name,
                             manufacture="NVIDIA",
                             memory_total=int(total_memory),  # Bytes
                             memory_used=int(used_memory),  # Bytes
                             memory_process=0,  # Bytes, TODO, get this
                             utilization=float(utilization), )

        except FileNotFoundError:
            return NvidiaGPU(error_msg="nvidia-smi command not found. Ensure NVIDIA drivers are installed.")
        except Exception as e:
            return NvidiaGPU(error_msg=str(e))
