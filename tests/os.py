from device_smi import Device

dev = Device("os")
print(dev)

assert dev.type == "os"
assert dev.name
assert dev.version
assert dev.arch in ["x86", "x86_64", "aarch64"]
