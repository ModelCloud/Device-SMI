from device_smi import Device

dev = Device("gpu")
print(dev)

assert dev.type == "gpu"
assert dev.pcie
assert dev.gpu
assert dev.model
assert dev.memory_total > 10
assert dev.vendor
assert dev.features
