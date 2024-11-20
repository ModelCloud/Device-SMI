from pyrsmi import rocml
from .base import BaseDevice, BaseInfo, BaseMetrics


class AMDGPU(BaseInfo):
    pass


class AMDGPUMetrics(BaseMetrics):
    pass


class AMDDevice(BaseDevice):
    def __init__(self, index: int = 0):
        super().__init__(index)
        rocml.smi_initialize()
        self.gpu_id = rocml.smi_get_device_id(index)
        self._info = self.info()

    def __del__(self):
        rocml.smi_shutdown()

    def info(self) -> AMDGPU:
        return AMDGPU(
            type="gpu",
            model=rocml.smi_get_device_name(self.gpu_id),
            memory_total=rocml.smi_get_device_memory_total(self.gpu_id),  # bytes
            vendor="AMD",
        )

    def metrics(self):
        return AMDGPUMetrics(
            memory_used=rocml.smi_get_device_memory_used(self.gpu_id),  # bytes
            memory_process=rocml.smi_get_device_memory_busy(self.gpu_id),  # Bytes, TODO, get this
            utilization=rocml.smi_get_device_utilization(self.gpu_id),
        )