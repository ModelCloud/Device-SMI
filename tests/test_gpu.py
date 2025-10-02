import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from device_smi import Device
from device_smi.base import BaseMetrics, GPUDevice, Pcie, GPU


@pytest.fixture()
def gpu_device():
    try:
        return Device("gpu")
    except Exception as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"GPU device not available or tooling missing: {exc}")


def test_gpu_device_basic_attributes(gpu_device):
    assert gpu_device.type == "gpu"
    assert isinstance(gpu_device.device, GPUDevice)
    assert isinstance(gpu_device.model, str) and gpu_device.model
    assert isinstance(gpu_device.vendor, str) and gpu_device.vendor
    assert isinstance(gpu_device.memory_total, int) and gpu_device.memory_total > 0


def test_gpu_device_optional_components(gpu_device):
    if gpu_device.pcie is not None:
        assert isinstance(gpu_device.pcie, Pcie)
        assert isinstance(gpu_device.pcie.gen, int)
        assert isinstance(gpu_device.pcie.speed, int)
        assert isinstance(gpu_device.pcie.id, str) and gpu_device.pcie.id
    if gpu_device.gpu is not None:
        assert isinstance(gpu_device.gpu, GPU)
        assert isinstance(gpu_device.gpu.driver, str) and gpu_device.gpu.driver
        assert isinstance(gpu_device.gpu.firmware, str)


@pytest.mark.parametrize("fast", [False, True])
def test_gpu_metrics(gpu_device, fast):
    try:
        metrics = gpu_device.metrics(fast=fast)
    except RuntimeError as exc:  # pragma: no cover - depends on vendor tooling
        pytest.skip(f"GPU metrics unavailable: {exc}")

    assert isinstance(metrics, BaseMetrics)
    assert metrics.memory_used >= 0
    assert metrics.memory_process >= 0
    assert metrics.utilization >= 0
