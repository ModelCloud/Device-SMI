from device_smi import Device

dev = Device("cpu")
print(dev)

assert dev.type == "cpu"
assert dev.model
assert dev.vendor
assert dev.memory_total > 10
assert dev.features is not None

print(f"mem used={dev.memory_used() / 1024 / 1024 / 1024:.2f} GB | utilization={dev.utilization()}%")

if __name__ == '__main__':
    print()