from device_smi import Device

for d in ["gpu", "cpu"]:
    smi = Device(d)
    info = smi.info()
    print(info.__dict__)
    print(f"{d} used {smi.memory_used() / 1024 / 1024 / 1024:.2f} GB")
