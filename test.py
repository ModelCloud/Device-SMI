from device_smi import Device

for d in ["gpu", "cpu"]:
    smi = Device(d)
    print(smi)
    print(f"{d} used {smi.memory_used() / 1024 / 1024 / 1024:.2f} GB")
