import platform
import re
import subprocess

from .apple import AppleDevice
from .cpu import CPUDevice
from .nvidia import NvidiaDevice
from .amd import AMDDevice
try:
    import torch

    HAS_TORCH = True
except:
    HAS_TORCH = False


class Device:
    def __init__(self, device):
        if HAS_TORCH and isinstance(device, torch.device):
            device_type = device.type.lower()
            device_index = device.index
        else:
            device_type = f"{device}".lower()
            device_index = 0
        if (
            device_type == "cuda"
            or device_type == "gpu"
            or re.match(r"(gpu|cuda):\d+", device_type)
        ):
            if platform.system() == "Darwin":
                if platform.machine() == 'x86_64':
                    raise Exception(error_msg="Not supported for macOS on Intel chips.")

                self.device = AppleDevice(device_index)
            else:
                if self._is_nvidia_available():
                    self.device = NvidiaDevice(device_index)
                else:
                    raise Exception("NVIDIA GPU not detected or CUDA not available.")
        elif device_type == "rocm" or re.match(r"(gpu|rocm):\d+", device_type):
            if self._is_amd_available():
                self.device = AMDDevice(device_index)
            else:
                raise Exception("AMD GPU not detected or ROCm not available.")

        elif device_type == "cpu":
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
