from device_smi import Device

dev = Device("cpu")
print(dev)

assert dev.type == "cpu"
assert dev.model

for i in ["ghz", "cpu", "(r)", "(tm)", "intel", "amd", "core", "processor", "@"]:
    assert i not in dev.model

assert dev.vendor in "amd, intel"
assert dev.memory_total > 10
assert dev.features is not None
assert dev.memory_used() >= 0
assert dev.utilization() >= 0

print(f"mem used={dev.memory_used() / 1024 / 1024 / 1024:.2f} GB | utilization={dev.utilization()}%")

if __name__ == '__main__':
    print()
