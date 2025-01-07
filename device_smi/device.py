import platform
import re
import warnings

from .apple import AppleDevice
from .base import _run
from .cpu import CPUDevice
from .intel import IntelDevice
from .nvidia import NvidiaDevice
from .os import OSDevice

try:
    import torch

    HAS_TORCH = True
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

        if (
            device_type == "cuda"
            or device_type == "gpu"
            or device_type == "xpu"
            or re.match(r"(gpu|cuda|xpu):\d+", device_type)
        ):
            if platform.system().lower() == "darwin":
                if platform.machine() == 'x86_64':
                    raise Exception("Not supported for macOS on Intel chips.")

                self.device = AppleDevice(self, device_index)
            else:
                try:
                    result = _run(["lspci"]).lower().splitlines()
                    result = "\n".join([
                        line for line in result
                        if any(keyword.lower() in line.lower() for keyword in ['vga', '3d', 'display'])
                    ])
                    if "intel" in result:
                        self.device = IntelDevice(self, device_index)
                    else:
                        self.device = NvidiaDevice(self, device_index)
                except BaseException:
                    self.device = NvidiaDevice(self, device_index)

        elif device_type == "cpu":
            self.device = CPUDevice(self)
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
