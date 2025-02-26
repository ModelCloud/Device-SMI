import platform
import warnings

from .amd import AMDDevice
from .apple import AppleDevice
from .base import _run
from .cpu import CPUDevice
from .intel import IntelDevice
from .nvidia import NvidiaDevice
from .os import OSDevice

IS_ROCM = False
try:
    import torch

    HAS_TORCH = True
    if torch.version.hip is not None:
        IS_ROCM = True
except BaseException:
    HAS_TORCH = False


class Device:
    def __init__(self, device):
        # init attribute first to avoid IDE not attr warning
        # CPU/GPU Device
        self.memory_total = None
        self.type = None
        self.features = []
        self.vendor = None
        self.model = None
        self.device = None
        # OS Device
        self.arch = None
        self.version = None
        self.name = None
        if HAS_TORCH and isinstance(device, torch.device):
            device_type = device.type.lower()
            device_index = device.index
        elif f"{device}".lower() == "os":
            self.device = OSDevice(self)
            assert self.arch
            assert self.version
            assert self.name
            return
        else:
            d = f"{device}".lower()
            if ":" in d:
                type, index = d.split(":")
                device_type = type
                device_index = (int(index))
            else:
                device_type = d
                device_index = 0

        self.pcie = None
        self.gpu = None

        if device_type == "cpu":
            self.device = CPUDevice(self)
        elif device_type == "xpu":
            self.device =  IntelDevice(self, device_index)
        elif device_type == "rocm" or IS_ROCM:
            self.device = AMDDevice(self, device_index)
        elif device_type == "cuda" and not IS_ROCM:
            self.device = NvidiaDevice(self, device_index)
        elif device_type == "gpu":
            if platform.system().lower() == "darwin":
                if platform.machine() == 'x86_64':
                    raise Exception("Not supported for macOS on Intel chips.")

                self.device = AppleDevice(self, device_index)
            else:
                if platform.system().lower() == "windows":
                    for d in ["NVIDIA", "AMD", "INTEL"]:
                        result = _run(["powershell", "-Command", "Get-CimInstance", "Win32_VideoController", "-Filter", f"\"Name like '%{d}%'\""]).lower().splitlines()
                        if result:
                            if d == "INTEL":
                                self.device = IntelDevice(self, device_index)
                            elif d == "AMD":
                                self.device = AMDDevice(self, device_index)
                            else:
                                self.device = NvidiaDevice(self, device_index)
                            break
                else:
                    result = _run(["lspci"]).lower().splitlines()
                    result = "\n".join([
                        line for line in result
                        if any(keyword.lower() in line.lower() for keyword in ['vga', '3d', 'display'])
                    ]).lower()
                    if "nvidia" in result:
                        self.device = NvidiaDevice(self, device_index)
                    elif "amd" in result:
                        self.device = AMDDevice(self, device_index)
                    elif "intel" in result:
                        self.device = IntelDevice(self, device_index)
            if not self.device:
                raise ValueError(f"Unable to find requested device: {device}")
        else:
            raise Exception(f"The device {device_type} is not supported")

        assert self.memory_total
        assert self.type
        assert self.features is not None
        assert self.vendor
        assert self.model

    def info(self):
        warnings.warn(
            "info() method is deprecated and will be removed in next release.",
            DeprecationWarning,
            stacklevel=2
        )
        return self

    def memory_used(self) -> int:
        return self.device.metrics().memory_used

    def utilization(self) -> float:
        return self.device.metrics().utilization

    def __str__(self):
        return str({k: v for k, v in self.__dict__.items() if k != 'device' and v is not None})
