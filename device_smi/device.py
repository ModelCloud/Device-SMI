from .cpu import CPUDevice
from .nvidia import NvidiaDevice

try:
    import torch

    HAS_TORCH = True
except:
    HAS_TORCH = False


class Device():
    def __init__(self, device):
        if HAS_TORCH and isinstance(device, torch.device):
            device_type = device.type.lower()
            device_index = device.index
        else:
            device_type = f'{device}'.lower()
            device_index = 0
        if device_type == 'cuda' or device_type == 'gpu':
            self.device = NvidiaDevice(device_index)
        elif device_type == 'cpu':
            self.device = CPUDevice(device_index)
        else:
            raise Exception(f"Device {device_type} is not supported")

    def info(self):
        return self.device.info()

    def memory_total(self):
        return self.device.info().memory_total

    def memory_used(self):
        return self.device.info().memory_used

    def utilization(self):
        return self.device.info().utilization
