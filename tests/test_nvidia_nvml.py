import ctypes
from types import SimpleNamespace

import pytest

from device_smi import nvidia


def nvml_stub(**functions):
    nvml = object.__new__(nvidia._NVML)
    nvml._available = True
    nvml._lib = object()
    nvml._shutdown_registered = False
    for name in (
        "nvmlDeviceGetHandleByIndex_v2",
        "nvmlDeviceGetHandleByIndex",
        "nvmlDeviceGetHandleByUUID",
        "nvmlDeviceGetHandleByPciBusId_v2",
        "nvmlDeviceGetHandleByPciBusId",
        "nvmlDeviceGetPciInfo_v3",
        "nvmlDeviceGetPciInfo_v2",
        "nvmlDeviceGetPciInfo",
        "nvmlErrorString",
        "nvmlShutdown",
    ):
        setattr(nvml, f"_{name}", functions.get(name))
    return nvml


def test_missing_symbol_raises_controlled_error():
    nvml = nvml_stub()

    with pytest.raises(RuntimeError, match="nvmlDeviceGetHandleByUUID"):
        nvml.device_handle("GPU-deadbeef")


@pytest.mark.parametrize("gpu_id", ["MIG-deadbeef", "MIG-GPU-deadbeef/1/2"])
def test_mig_identifiers_use_uuid_lookup(gpu_id):
    calls = []

    def by_uuid(uuid, handle):
        calls.append(uuid)
        ctypes.cast(handle, ctypes.POINTER(ctypes.c_void_p)).contents.value = 123
        return 0

    nvml = nvml_stub(nvmlDeviceGetHandleByUUID=by_uuid)

    assert nvml.device_handle(f"  {gpu_id}  ").value == 123
    assert calls == [gpu_id.encode()]


@pytest.mark.parametrize(
    ("symbol", "expected_type"),
    [
        ("nvmlDeviceGetPciInfo_v3", nvidia._nvmlPciInfo_v3_t),
        ("nvmlDeviceGetPciInfo_v2", nvidia._nvmlPciInfo_v2_t),
        ("nvmlDeviceGetPciInfo", nvidia._nvmlPciInfo_v2_t),
    ],
)
def test_pci_info_selects_newest_available_abi(symbol, expected_type):
    calls = []

    def get_pci_info(handle, info_pointer):
        info = ctypes.cast(info_pointer, ctypes.POINTER(expected_type)).contents
        info.busId = b"0000:01:00.0"
        calls.append(handle)
        return 0

    nvml = nvml_stub(**{symbol: get_pci_info})

    assert nvml.pci_info(ctypes.c_void_p(7)) == "0000:01:00.0"
    assert len(calls) == 1


def test_pci_info_prefers_v3():
    def unexpected(*args):
        raise AssertionError("older PCI symbol called")

    def v3(handle, info_pointer):
        info = ctypes.cast(
            info_pointer, ctypes.POINTER(nvidia._nvmlPciInfo_v3_t)
        ).contents
        info.busId = b"0000:02:00.0"
        return 0

    nvml = nvml_stub(
        nvmlDeviceGetPciInfo_v3=v3,
        nvmlDeviceGetPciInfo_v2=unexpected,
        nvmlDeviceGetPciInfo=unexpected,
    )

    assert nvml.pci_info(None) == "0000:02:00.0"


def test_cuda_visible_devices_is_trimmed(monkeypatch):
    device = object.__new__(nvidia.NvidiaDevice)
    device.index = 1
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", " GPU-first , MIG-GPU-second/1/2 ")
    monkeypatch.setattr(nvidia._nvml, "_available", False)
    monkeypatch.setattr(nvidia, "_run_nvidia_smi", lambda *args, **kwargs: "")

    assert device._get_gpu_id() == "MIG-GPU-second/1/2"


def test_optional_metadata_failure_keeps_nvml_device(monkeypatch):
    device = object.__new__(nvidia.NvidiaDevice)
    device.gpu_id = "0"
    target = SimpleNamespace(pcie=None)
    monkeypatch.setattr(nvidia._nvml, "device_handle", lambda gpu_id: object())
    monkeypatch.setattr(nvidia._nvml, "device_name", lambda handle: "NVIDIA Test")
    monkeypatch.setattr(nvidia._nvml, "memory_total", lambda handle: 1024)
    monkeypatch.setattr(nvidia._nvml, "driver_version", lambda: "555.1")
    for name in (
        "vbios_version",
        "compute_capability",
        "pci_info",
        "max_pcie_generation",
        "current_pcie_generation",
    ):
        monkeypatch.setattr(
            nvidia._nvml,
            name,
            lambda *args, _name=name: (_ for _ in ()).throw(RuntimeError(_name)),
        )

    device._init_from_nvml(target)

    assert target.model == "test"
    assert target.memory_total == 1024
    assert target.features == []
    assert target.pcie is None
    assert target.gpu.driver == "555.1"
    assert target.gpu.firmware == ""


def test_core_nvml_failure_still_falls_back_to_nvidia_smi(monkeypatch):
    calls = []
    monkeypatch.setattr(nvidia._nvml, "_available", True)
    monkeypatch.setattr(nvidia.NvidiaDevice, "_get_gpu_id", lambda self: "0")
    monkeypatch.setattr(
        nvidia.NvidiaDevice,
        "_init_from_nvml",
        lambda self, cls: (_ for _ in ()).throw(RuntimeError("core failure")),
    )
    monkeypatch.setattr(
        nvidia.NvidiaDevice,
        "_init_from_nvidia_smi",
        lambda self, cls: calls.append(cls),
    )
    target = SimpleNamespace()

    nvidia.NvidiaDevice(target, 0)

    assert calls == [target]


def test_shutdown_is_idempotent_and_calls_nvml_once():
    calls = []
    nvml = nvml_stub(nvmlShutdown=lambda: calls.append(True) or 0)

    nvml._shutdown()
    nvml._shutdown()

    assert calls == [True]
    assert nvml.available is False
