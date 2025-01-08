from device_smi import Device
import torch

dev = Device("gpu")
print(dev)

assert dev.type == "gpu", f"wrong type: {dev.type}"
if dev.pcie:
    assert dev.pcie.gen is not None
    assert dev.pcie.speed is not None
    assert dev.pcie.id is not None
if dev.gpu:
    assert dev.gpu.driver is not None
    assert dev.gpu.firmware is not None
assert dev.model
assert dev.memory_total > 10, f"wrong memory size: {dev.memory_total()}"
