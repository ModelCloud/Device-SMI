import os
import subprocess

import torch

from cpu import CPUDevice
from device import Device
from nvidia import NvidiaDevice

DEVICE_NAME = "Name"
MEMORY_TOTAL = "Memory-total"
MEMORY_USED = "Memory-in-use"
MEMORY_PROCESS = "Process memory"
UTILIZATION = "Utilization"
PCIE_BUS_ID = "PCIe Bus ID"
PCIE_GEN = "PCIe Gen"
PCIE_LINK = "PCIe Link"
DRIVER_VERSION = "Driver Version"
MANUFACTURE = "Manufacturer"



class DeviceSMI():
    def __init__(self, device: torch.device):
        if device.type.lower() == 'cuda':
            self.device = NvidiaDevice(device)
        elif device.type.lower() == 'cpu':
            self.device = CPUDevice(device)
        else:
            raise Exception(f"Device {device} is not supported")

    def info(self):
        return self.device.info()
