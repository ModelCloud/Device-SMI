from device_smi import Device

dev = Device("cpu")
print(dev)

assert dev.type == "cpu"
assert dev.model
assert dev.vendor
assert dev.memory_total > 10
assert dev.features
