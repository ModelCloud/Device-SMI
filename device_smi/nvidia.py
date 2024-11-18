import os
import subprocess

from .base import BaseDevice, BaseInfo, BaseMetrics


class NvidiaGPU(BaseInfo):
    pass  # TODO, add PCIE & DRIVER

class NvidiaGPUMetrics(BaseMetrics):
    pass

class NvidiaDevice(BaseDevice):
    def __init__(self, index: int = 0):
        super().__init__(index)
        self.gpu_id = self._get_gpu_id()

    def _get_gpu_id(self):
        cudas = os.environ.get("CUDA_VISIBLE_DEVICES", "")
        cuda_list = cudas.split(",") if cudas else []
        if cuda_list and len(cuda_list) > self.index:
            return cuda_list[self.index]
        else:
            return str(self.index)

    def info(self) -> NvidiaGPU:
        try:
            args = [
                'nvidia-smi',
                f'--id={self.gpu_id}',
                '--query-gpu='
                'name,'
                'memory.total,'
                'pci.bus_id,'
                'pcie.link.gen.max,'
                'pcie.link.gen.current,'
                'driver_version',
                '--format=csv,noheader,nounits'
            ]

            result = subprocess.run(
                args=args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:
                raise RuntimeError(result.stderr)

            output = result.stdout.strip().split('\n')[0]
            model, total_memory, pci_bus_id, pcie_gen, pcie_width, driver_version = output.split(', ')

            if model.lower().startswith("nvidia"):
                model = model[len("nvidia"):]

            return NvidiaGPU(
                type="gpu",
                model=model.strip(),
                memory_total=int(total_memory) * 1024 * 1024,  # bytes
                vendor="NVIDIA",
            )
        except FileNotFoundError:
            raise FileNotFoundError(error_msg="nvidia-smi command not found. Ensure NVIDIA drivers are installed.")
        except Exception as e:
            raise e

    def metrics(self):
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
                'memory.used,'
                'utilization.gpu,'
                '--format=csv,noheader,nounits'
            ]

            result = subprocess.run(
                args=args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:
                raise RuntimeError(result.stderr)

            output = result.stdout.strip().split('\n')[0]
            total_memory, used_memory, utilization = output.split(', ')

            return NvidiaGPUMetrics(
                memory_used=int(used_memory) * 1024 * 1024, #bytes
                memory_process=0,  # Bytes, TODO, get this
                utilization=float(utilization),
            )

        except FileNotFoundError:
            raise FileNotFoundError(error_msg="nvidia-smi command not found. Ensure NVIDIA drivers are installed.")
        except Exception as e:
            raise e