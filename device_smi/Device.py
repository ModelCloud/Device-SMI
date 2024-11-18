from .cpu import CPUDevice
from .nvidia import NvidiaDevice


class Device():
    def __init__(self, device):
        try:
            import torch
            device_type = device.type.lower()
            device_index = device.index
        except:
            device_type = f'{device}'.lower()
            device_index = 0
        if device_type == 'cuda' or device_type == 'gpu':
            self.device = NvidiaDevice(device_index)
        elif device_type == 'cpu':
            self.device = CPUDevice(device_index)
        else:
            raise Exception(f"Device {device_type} is not supported")
        self.info = self._info()

    def _info(self):
        return self.device.info()

    def info(self):
        return self.info

    def memory_total(self):
        return self.info.memory_total

    def memory_used(self):
        return self.device.metrics().memory_used

    def utilization(self):
        return self.device.metrics().utilization
