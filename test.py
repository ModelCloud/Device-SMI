import torch

from DeviceSMI import DeviceSMI

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
smi = DeviceSMI(device)
info = smi.get_device_info()
print(info)
