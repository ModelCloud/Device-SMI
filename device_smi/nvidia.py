import os
import platform
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
        self._info = self.info()

    def _get_gpu_id(self):
        cudas = os.environ.get("CUDA_VISIBLE_DEVICES", "")
        cuda_list = cudas.split(",") if cudas else []
        if cuda_list and len(cuda_list) > self.index:
            return cuda_list[self.index]
        else:
            return str(self.index)

    def info(self) -> NvidiaGPU:
        if platform.system() == "Darwin":
            args = ["system_profiler", "SPDisplaysDataType"]

            result = subprocess.run(
                args=args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            output = result.stdout.strip().split("\n")
            for o in output:
                if "Chipset Model" in o:
                    model = o.split(":")[1].replace("Apple", "").strip()
                if "Vendor" in o:
                    vender = o.split(":")[1].strip().split(" ")[0].strip()

            memory_total = int(subprocess.check_output(["sysctl", "-n", "hw.memsize"]))

            return NvidiaGPU(
                type="gpu",
                model=model,
                memory_total=memory_total,  # bytes
                vendor=vender,
            )
        else:
            try:
                args = [
                    "nvidia-smi",
                    f"--id={self.gpu_id}",
                    "--query-gpu="
                    "name,"
                    "memory.total,"
                    "pci.bus_id,"
                    "pcie.link.gen.max,"
                    "pcie.link.gen.current,"
                    "driver_version",
                    "--format=csv,noheader,nounits",
                ]

                result = subprocess.run(
                    args=args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )

                if result.returncode != 0:
                    raise RuntimeError(result.stderr)

                output = result.stdout.strip().split("\n")[0]
                model, total_memory, pci_bus_id, pcie_gen, pcie_width, driver_version = (
                    output.split(", ")
                )

                if model.lower().startswith("nvidia"):
                    model = model[len("nvidia"):]

                return NvidiaGPU(
                    type="gpu",
                    model=model.strip(),
                    memory_total=int(total_memory) * 1024 * 1024,  # bytes
                    vendor="NVIDIA",
                )
            except FileNotFoundError:
                raise FileNotFoundError()
            except Exception as e:
                raise e

    def metrics(self):
        if platform.system() == "Darwin":
            result = subprocess.run(
                ["top", "-l", "1", "-stats", "cpu"], stdout=subprocess.PIPE
            )
            output = result.stdout.decode("utf-8")

            for line in output.splitlines():
                if line.startswith("CPU usage"):
                    parts = line.split()
                    user_time = float(parts[2].strip("%"))
                    sys_time = float(parts[4].strip("%"))
                    utilization = user_time + sys_time

            total_memory = int(subprocess.check_output(['sysctl', 'hw.memsize']).split(b':')[1].strip())
            free_memory = int(subprocess.check_output(['sysctl', 'vm.page_free_count']).split(b':')[1].strip())
            page_size = int(subprocess.check_output(['sysctl', 'hw.pagesize']).split(b':')[1].strip())

            used_memory = total_memory - (free_memory * page_size)

            return NvidiaGPUMetrics(
                memory_used=int(used_memory),  # bytes
                memory_process=0,  # Bytes, TODO, get this
                utilization=float(utilization),
            )
        else:
            try:
                args = [
                    "nvidia-smi",
                    f"--id={self.gpu_id}",
                    "--query-gpu=" "memory.used," "utilization.gpu,",
                    "--format=csv,noheader,nounits",
                ]

                result = subprocess.run(
                    args=args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )

                if result.returncode != 0:
                    raise RuntimeError(result.stderr)

                output = result.stdout.strip().split("\n")[0]
                used_memory, utilization = output.split(", ")

                return NvidiaGPUMetrics(
                    memory_used=int(used_memory) * 1024 * 1024,  # bytes
                    memory_process=0,  # Bytes, TODO, get this
                    utilization=float(utilization),
                )

            except FileNotFoundError:
                raise FileNotFoundError(
                    error_msg="nvidia-smi command not found. Ensure NVIDIA drivers are installed."
                )
            except Exception as e:
                raise e
