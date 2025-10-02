import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from device_smi import Device

dev = Device("os")
print(dev)

assert dev.type == "os", f"type is wrong, expected: `cpu`, actual: `{dev.type}`"
assert dev.name
assert dev.version
assert dev.arch in ["x86", "x86_64", "aarch64"]
