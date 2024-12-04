from device_smi import Device

dev = Device("cpu")
print(dev)

assert dev.type == "cpu"
assert dev.model

for i in ["ghz", "cpu", "(r)", "(tm)", "intel", "amd", "core", "processor", "@"]:
    assert i not in dev.model, f"{i} should be removed in model"

assert dev.vendor in "amd, intel, apple", f"check vendor: {dev.vendor}"
assert dev.memory_total() > 10, f"wrong memory size: {dev.memory_total()}"
assert dev.features is not None

memory_used = dev.memory_used()
assert memory_used > 0, f"dev.memory_used()={memory_used}"

utilization = dev.utilization()
assert utilization >= 0.0, f"dev.utilization()={utilization}"

print(f"mem used={dev.memory_used() / 1024 / 1024 / 1024:.2f} GB | utilization={dev.utilization()}%")

if __name__ == '__main__':
    print()
