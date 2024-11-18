import torch

from device_smi import DeviceSMI

for d in ["cuda:0", "cpu"]:
    device = torch.device(d)
    smi = DeviceSMI(device)
    info = smi.info()
    print(info.__dict__)

