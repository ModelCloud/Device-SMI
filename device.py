from abc import abstractmethod

import torch


class Device():
    def __init__(self, device:torch.device):
        self.type = device.type
        self.index = device.index

    @abstractmethod
    def info(self):
        pass

