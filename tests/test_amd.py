import sys
import types

import pytest

from device_smi import amd


def _fake_torch(name, free=0, total=0, hip="6.4"):
    torch = types.ModuleType("torch")
    torch.version = types.SimpleNamespace(hip=hip)
    torch.cuda = types.SimpleNamespace(
        get_device_name=lambda index: name,
        mem_get_info=lambda index: (free, total),
    )
    return torch


def _amd_device(index=0, gpu_id="0"):
    device = amd.AMDDevice.__new__(amd.AMDDevice)
    device.index = index
    device.gpu_id = gpu_id
    return device


def test_rocm_vf_metrics_use_torch_memory(monkeypatch):
    monkeypatch.setitem(sys.modules, "torch", _fake_torch("AMD Instinct MI355X VF", 3, 4))
    monkeypatch.setattr(
        amd,
        "_run",
        lambda *args, **kwargs: pytest.fail("amd-smi should not be queried for ROCm VFs"),
    )

    metrics = _amd_device().metrics()

    assert isinstance(metrics, amd.AMDGPUMetrics)
    assert metrics.memory_used == 1
    assert metrics.memory_process == 0
    assert metrics.utilization == 0.0


def test_rocm_physical_gpu_keeps_amd_smi_metrics(monkeypatch):
    monkeypatch.setitem(sys.modules, "torch", _fake_torch("AMD Instinct MI355X"))
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return ["1024, 37.5"]

    monkeypatch.setattr(amd, "_run", fake_run)

    metrics = _amd_device(gpu_id="2").metrics()

    assert calls == [[
        "amd-smi",
        "--id=2",
        "--query-gpu=memory.used,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]]
    assert metrics.memory_used == 1024 * 1024 * 1024
    assert metrics.utilization == 37.5


def test_rocm_vf_metrics_fall_back_without_torch(monkeypatch):
    monkeypatch.setitem(sys.modules, "torch", None)
    monkeypatch.setattr(amd, "_run", lambda *args, **kwargs: ["512, 12.5"])

    metrics = _amd_device().metrics()

    assert metrics.memory_used == 512 * 1024 * 1024
    assert metrics.utilization == 12.5


def test_torch_cuda_metrics_do_not_claim_rocm_vfs(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "torch",
        _fake_torch("AMD Instinct MI355X VF", hip=None),
    )
    monkeypatch.setattr(amd, "_run", lambda *args, **kwargs: ["256, 5.0"])

    metrics = _amd_device().metrics()

    assert metrics.memory_used == 256 * 1024 * 1024
    assert metrics.utilization == 5.0
