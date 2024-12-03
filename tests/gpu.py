from device_smi import Device

dev = Device("gpu")
print(dev)

assert dev.type == "gpu", f"wrong type: {dev.type}"
if dev.pcie:
    assert dev.pcie.gen
    assert dev.pcie.speed
    assert dev.pcie.id
if dev.gpu:
    assert dev.gpu.driver
    assert dev.gpu.firmware
assert dev.model
assert dev.memory_total > 10, f"wrong memory size: {dev.memory_total}"
