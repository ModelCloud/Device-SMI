import torch

from device_smi import Device

for d in ["cuda:0", "cpu"]:
    device = torch.device(d)
    smi = Device(device)
    info = smi.info()
    print(info.__dict__)
    print(f"{device} used {smi.memory_used()/1024/1024/1024:.2f} GB")

