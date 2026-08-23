import ctypes
from types import SimpleNamespace

import pytest

from device_smi import nvidia


class LegacyPciInfoCLayout(ctypes.Structure):
    _fields_ = [
        ("busId", ctypes.c_char * 16),
        ("domain", ctypes.c_uint),
        ("bus", ctypes.c_uint),
        ("device", ctypes.c_uint),
        ("pciDeviceId", ctypes.c_uint),
        ("pciSubSystemId", ctypes.c_uint),
    ]


class PciInfoV3CLayout(ctypes.Structure):
    _fields_ = [
        ("busIdLegacy", ctypes.c_char * 16),
        ("domain", ctypes.c_uint),
        ("bus", ctypes.c_uint),
        ("device", ctypes.c_uint),
        ("pciDeviceId", ctypes.c_uint),
        ("pciSubSystemId", ctypes.c_uint),
        ("busId", ctypes.c_char * 32),
    ]


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
        "nvmlDeviceGetVbiosVersion",
        "nvmlDeviceGetCudaComputeCapability",
        "nvmlDeviceGetMaxPcieLinkGeneration",
        "nvmlDeviceGetCurrPcieLinkGeneration",
        "nvmlErrorString",
        "nvmlShutdown",
    ):
        setattr(nvml, f"_{name}", functions.get(name))
    return nvml


def test_missing_symbol_raises_controlled_error():
    nvml = nvml_stub()

    with pytest.raises(RuntimeError, match="nvmlDeviceGetHandleByUUID"):
        nvml.device_handle("GPU-deadbeef")


def test_legacy_pci_info_matches_c_abi_layout():
    expected_offsets = {
        "busId": 0,
        "domain": 16,
        "bus": 20,
        "device": 24,
        "pciDeviceId": 28,
        "pciSubSystemId": 32,
    }

    assert ctypes.sizeof(LegacyPciInfoCLayout) == 36
    assert ctypes.sizeof(nvidia._nvmlPciInfo_v2_t) == 36
    for field, expected_offset in expected_offsets.items():
        assert getattr(LegacyPciInfoCLayout, field).offset == expected_offset
        assert getattr(nvidia._nvmlPciInfo_v2_t, field).offset == expected_offset


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
    ("gpu_id", "symbol", "expected_argument"),
    [
        ("GPU-deadbeef", "nvmlDeviceGetHandleByUUID", b"GPU-deadbeef"),
        (" 7 ", "nvmlDeviceGetHandleByIndex_v2", 7),
        (
            " 0000:65:00.0 ",
            "nvmlDeviceGetHandleByPciBusId_v2",
            b"0000:65:00.0",
        ),
    ],
)
def test_device_handle_routing(gpu_id, symbol, expected_argument):
    calls = []

    def lookup(identifier, handle):
        calls.append(identifier)
        ctypes.cast(handle, ctypes.POINTER(ctypes.c_void_p)).contents.value = 42
        return 0

    nvml = nvml_stub(**{symbol: lookup})

    assert nvml.device_handle(gpu_id).value == 42
    assert calls == [expected_argument]


@pytest.mark.parametrize(
    ("symbol", "c_layout"),
    [
        ("nvmlDeviceGetPciInfo_v3", PciInfoV3CLayout),
        ("nvmlDeviceGetPciInfo_v2", LegacyPciInfoCLayout),
        ("nvmlDeviceGetPciInfo", LegacyPciInfoCLayout),
    ],
)
def test_pci_info_selects_newest_available_abi(symbol, c_layout):
    calls = []

    def get_pci_info(handle, info_pointer):
        info = ctypes.cast(info_pointer, ctypes.POINTER(c_layout)).contents
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
        info = ctypes.cast(info_pointer, ctypes.POINTER(PciInfoV3CLayout)).contents
        info.busId = b"0000:02:00.0"
        return 0

    nvml = nvml_stub(
        nvmlDeviceGetPciInfo_v3=v3,
        nvmlDeviceGetPciInfo_v2=unexpected,
        nvmlDeviceGetPciInfo=unexpected,
    )

    assert nvml.pci_info(None) == "0000:02:00.0"


@pytest.mark.parametrize("compatibility_error", [3, 13])
def test_pci_info_falls_back_after_v3_compatibility_error(compatibility_error):
    calls = []

    def v3(handle, info_pointer):
        calls.append("v3")
        return compatibility_error

    def v2(handle, info_pointer):
        calls.append("v2")
        info = ctypes.cast(
            info_pointer, ctypes.POINTER(LegacyPciInfoCLayout)
        ).contents
        info.busId = b"0000:03:00.0"
        return 0

    nvml = nvml_stub(
        nvmlDeviceGetPciInfo_v3=v3,
        nvmlDeviceGetPciInfo_v2=v2,
        nvmlDeviceGetPciInfo=lambda *args: pytest.fail("legacy symbol called"),
    )

    assert nvml.pci_info(None) == "0000:03:00.0"
    assert calls == ["v3", "v2"]


@pytest.mark.parametrize("compatibility_error", [3, 13])
def test_pci_info_falls_back_from_v2_to_legacy(compatibility_error):
    calls = []

    def v2(handle, info_pointer):
        calls.append("v2")
        return compatibility_error

    def legacy(handle, info_pointer):
        calls.append("legacy")
        info = ctypes.cast(
            info_pointer, ctypes.POINTER(LegacyPciInfoCLayout)
        ).contents
        info.busId = b"0000:04:00.0"
        return 0

    nvml = nvml_stub(
        nvmlDeviceGetPciInfo_v2=v2,
        nvmlDeviceGetPciInfo=legacy,
    )

    assert nvml.pci_info(None) == "0000:04:00.0"
    assert calls == ["v2", "legacy"]


@pytest.mark.parametrize("nvml_error", [1, 6])
def test_pci_info_does_not_fallback_for_noncompatibility_error(nvml_error):
    calls = []

    def v3(handle, info_pointer):
        calls.append("v3")
        return nvml_error

    def unexpected(*args):
        calls.append("older")
        return 0

    nvml = nvml_stub(
        nvmlDeviceGetPciInfo_v3=v3,
        nvmlDeviceGetPciInfo_v2=unexpected,
        nvmlDeviceGetPciInfo=unexpected,
    )

    with pytest.raises(RuntimeError, match=rf"NVML error {nvml_error}:"):
        nvml.pci_info(None)
    assert calls == ["v3"]


@pytest.mark.parametrize(
    ("method_name", "args", "missing_symbol"),
    [
        ("vbios_version", (ctypes.c_void_p(1),), "nvmlDeviceGetVbiosVersion"),
        (
            "compute_capability",
            (ctypes.c_void_p(1),),
            "nvmlDeviceGetCudaComputeCapability",
        ),
        (
            "max_pcie_generation",
            (ctypes.c_void_p(1),),
            "nvmlDeviceGetMaxPcieLinkGeneration",
        ),
        (
            "current_pcie_generation",
            (ctypes.c_void_p(1),),
            "nvmlDeviceGetCurrPcieLinkGeneration",
        ),
    ],
)
def test_missing_optional_bound_symbol_raises_controlled_error(
    method_name, args, missing_symbol
):
    nvml = nvml_stub()

    with pytest.raises(RuntimeError, match=missing_symbol):
        getattr(nvml, method_name)(*args)


def test_cuda_visible_devices_is_trimmed(monkeypatch):
    device = object.__new__(nvidia.NvidiaDevice)
    device.index = 1
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", " GPU-first , MIG-GPU-second/1/2 ")
    monkeypatch.setattr(nvidia._nvml, "_available", False)
    monkeypatch.setattr(nvidia, "_run_nvidia_smi", lambda *args, **kwargs: "")

    assert device._get_gpu_id() == "MIG-GPU-second/1/2"


@pytest.mark.parametrize("visible_devices", ["", "   "])
def test_empty_cuda_visible_devices_uses_device_index(monkeypatch, visible_devices):
    device = object.__new__(nvidia.NvidiaDevice)
    device.index = 2
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", visible_devices)
    monkeypatch.setattr(nvidia._nvml, "_available", False)
    monkeypatch.setattr(nvidia, "_run_nvidia_smi", lambda *args, **kwargs: "")

    assert device._get_gpu_id() == "2"


def test_cuda_visible_devices_rejects_interior_empty_entry(monkeypatch):
    device = object.__new__(nvidia.NvidiaDevice)
    device.index = 1
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0, ,2")
    monkeypatch.setattr(nvidia._nvml, "_available", False)
    monkeypatch.setattr(nvidia, "_run_nvidia_smi", lambda *args, **kwargs: "")

    with pytest.raises(ValueError, match="empty device entry"):
        device._get_gpu_id()


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


def test_one_pcie_metadata_failure_clears_stale_pcie_only(monkeypatch):
    device = object.__new__(nvidia.NvidiaDevice)
    device.gpu_id = "0"
    stale_pcie = object()
    target = SimpleNamespace(pcie=stale_pcie)
    monkeypatch.setattr(nvidia._nvml, "device_handle", lambda gpu_id: object())
    monkeypatch.setattr(nvidia._nvml, "device_name", lambda handle: "NVIDIA Test")
    monkeypatch.setattr(nvidia._nvml, "memory_total", lambda handle: 2048)
    monkeypatch.setattr(nvidia._nvml, "driver_version", lambda: "555.2")
    monkeypatch.setattr(nvidia._nvml, "vbios_version", lambda handle: "VBIOS-1")
    monkeypatch.setattr(
        nvidia._nvml, "compute_capability", lambda handle: "9.0"
    )
    monkeypatch.setattr(nvidia._nvml, "pci_info", lambda handle: "0000:05:00.0")
    monkeypatch.setattr(
        nvidia._nvml,
        "max_pcie_generation",
        lambda handle: (_ for _ in ()).throw(RuntimeError("not supported")),
    )
    monkeypatch.setattr(nvidia._nvml, "current_pcie_generation", lambda handle: 4)

    device._init_from_nvml(target)

    assert target.model == "test"
    assert target.memory_total == 2048
    assert target.features == ["9.0"]
    assert target.gpu.driver == "555.2"
    assert target.gpu.firmware == "VBIOS-1"
    assert target.pcie is None


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


@pytest.mark.parametrize(
    "shutdown",
    [None, lambda: 3, lambda: (_ for _ in ()).throw(OSError("shutdown failed"))],
)
def test_missing_or_erroring_shutdown_is_safe_and_idempotent(shutdown):
    nvml = nvml_stub(nvmlShutdown=shutdown)

    nvml._shutdown()
    nvml._shutdown()

    assert nvml.available is False
