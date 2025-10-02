import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from device_smi import Device
from device_smi.base import BaseMetrics
from device_smi.cpu import CPUDevice, CPUMetrics


@pytest.fixture()
def cpu_device():
    return Device("cpu")


def test_cpu_device_basic_attributes(cpu_device):
    banned_tokens = {"ghz", "cpu", "(r)", "(tm)", "intel", "amd", "core", "processor", "@"}

    assert cpu_device.type == "cpu"
    assert isinstance(cpu_device.device, CPUDevice)
    assert isinstance(cpu_device.model, str) and cpu_device.model
    assert cpu_device.model == cpu_device.model.lower()
    for token in banned_tokens:
        assert token not in cpu_device.model
    assert isinstance(cpu_device.vendor, str) and cpu_device.vendor
    assert isinstance(cpu_device.features, list)
    assert all(isinstance(flag, str) and flag == flag.lower() for flag in cpu_device.features)


def test_cpu_memory_and_utilization(cpu_device):
    assert isinstance(cpu_device.memory_total, int) and cpu_device.memory_total > 0

    metrics = cpu_device.metrics()
    assert isinstance(metrics, CPUMetrics)
    assert 0 <= metrics.memory_used <= cpu_device.memory_total
    assert metrics.memory_process >= 0
    assert 0 <= metrics.utilization <= 100.0 + 1e-6

    mem_used_api = cpu_device.memory_used()
    util_api = cpu_device.utilization()
    allowed_diff = max(int(0.005 * cpu_device.memory_total), 64 * 1024 * 1024)
    assert abs(mem_used_api - metrics.memory_used) <= allowed_diff
    assert 0 <= util_api <= 100.0 + 1e-6


@pytest.mark.parametrize("fast", [False, True])
def test_cpu_metrics_paths(cpu_device, fast):
    metrics = cpu_device.metrics(fast=fast)
    assert isinstance(metrics, BaseMetrics)
    assert metrics.memory_used >= 0
    if metrics.memory_used:
        assert metrics.memory_used <= cpu_device.memory_total
    assert metrics.utilization >= 0
