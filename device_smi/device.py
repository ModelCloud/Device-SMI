import platform
import re
import subprocess

try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class Device:
    def __init__(self, device):
        if TORCH_AVAILABLE and isinstance(device, torch.device):
            device_type = device.type.lower()
            device_index = device.index
        else:
            match = re.match(r"(cuda|gpu|rocm|cpu)(:\d+)?", f"{device}".lower())
            if not match:
                raise Exception(f"The device {device} is not supported")
            device_type = match.group(1)
            device_index = int(match.group(2)[1:]) if match.group(2) else 0

        if device_type in ["cuda", "gpu"]:
            if platform.system() == "Darwin":
                if platform.machine() == 'x86_64':
                    raise Exception("Not supported for macOS on Intel chips.")
                from .apple import AppleDevice

                self.device = AppleDevice(device_index)
            else:
                if self._is_nvidia_available():
                    from .nvidia import NvidiaDevice

                    self.device = NvidiaDevice(device_index)
                else:
                    raise Exception("NVIDIA GPU not detected or CUDA not available.")
        elif device_type == "rocm":
            from .amd import AMDDevice

            if self._is_amd_available():
                self.device = AMDDevice(device_index)
            else:
                raise Exception("AMD GPU not detected or ROCm not available.")

        elif device_type == "cpu":
            from .cpu import CPUDevice

            self.device = CPUDevice(device_index)
        else:
            raise Exception(f"The device {device_type} is not supported")

    def info(self):
        return self.device._info

    def memory_total(self):
        return self.info().memory_total

    def memory_used(self):
        return self.device.metrics().memory_used

    def utilization(self):
        return self.device.metrics().utilization

    @staticmethod
    def _is_amd_available():
        try:
            subprocess.run(["rocm-smi"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False

    @staticmethod
    def _is_nvidia_available():
        try:
            subprocess.run(["nvidia-smi"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False
