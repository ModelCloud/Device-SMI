import ctypes
import ctypes.util
import logging
import os
import platform
import re
import threading
import time
import warnings
from collections import OrderedDict

from .base import GPU, BaseMetrics, GPUDevice, Pcie, _run
from .config import config

logger = logging.getLogger(__name__)

_NVML_ERROR_NOT_SUPPORTED = 3
_NVML_ERROR_FUNCTION_NOT_FOUND = 13
_NVML_COMPATIBILITY_ERRORS = {
    _NVML_ERROR_NOT_SUPPORTED,
    _NVML_ERROR_FUNCTION_NOT_FOUND,
}


class NvidiaGPUMetrics(BaseMetrics):
    pass


class _nvmlMemory_t(ctypes.Structure):
    _fields_ = [
        ("total", ctypes.c_ulonglong),
        ("free", ctypes.c_ulonglong),
        ("used", ctypes.c_ulonglong),
    ]


class _nvmlUtilization_t(ctypes.Structure):
    _fields_ = [
        ("gpu", ctypes.c_uint),
        ("memory", ctypes.c_uint),
    ]


class _nvmlPciInfo_v3_t(ctypes.Structure):
    _fields_ = [
        ("busIdLegacy", ctypes.c_char * 16),
        ("domain", ctypes.c_uint),
        ("bus", ctypes.c_uint),
        ("device", ctypes.c_uint),
        ("pciDeviceId", ctypes.c_uint),
        ("pciSubSystemId", ctypes.c_uint),
        ("busId", ctypes.c_char * 32),
    ]


class _nvmlPciInfo_v2_t(ctypes.Structure):
    """Legacy PCI info ABI used by both the v2 and unversioned symbols."""

    _fields_ = [
        ("busId", ctypes.c_char * 16),
        ("domain", ctypes.c_uint),
        ("bus", ctypes.c_uint),
        ("device", ctypes.c_uint),
        ("pciDeviceId", ctypes.c_uint),
        ("pciSubSystemId", ctypes.c_uint),
    ]


def _nvml_library_candidates():
    system = platform.system()
    if system == "Linux":
        return [
            "/usr/lib/wsl/lib/libnvidia-ml.so.1",
            "/usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1",
            "/usr/lib/x86_64-linux-gnu/libnvidia-ml.so",
            "/usr/lib64/libnvidia-ml.so.1",
            "/usr/lib64/libnvidia-ml.so",
            "libnvidia-ml.so.1",
            "libnvidia-ml.so",
        ]
    if system == "Windows":
        return [
            os.path.join(
                os.environ.get("SYSTEMROOT", r"C:\Windows"), "System32", "nvml.dll"
            ),
            os.path.join(
                os.environ.get("ProgramW6432", r"C:\Program Files"),
                "NVIDIA Corporation",
                "NVSMI",
                "nvml.dll",
            ),
            "nvml.dll",
        ]
    return ["libnvidia-ml.dylib"]


def _load_nvml_library():
    lib_path = ctypes.util.find_library("nvidia-ml")
    candidates = [lib_path] if lib_path else []
    candidates.extend(_nvml_library_candidates())
    for path in candidates:
        if not path:
            continue
        try:
            return ctypes.CDLL(path)
        except OSError:
            continue
    return None


class _NVML:
    """Lightweight ctypes binding to the NVIDIA Management Library (NVML)."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
                cls._instance._available = False
                cls._instance._lib = None
                cls._instance._shutdown_registered = False
        return cls._instance

    def __init__(self):
        with self._lock:
            if self._initialized:
                return
            lib = _load_nvml_library()
            if lib is None:
                self._initialized = True
                return
            self._lib = lib
            try:
                self._bind_functions()
                code = self._init()
            except (OSError, AttributeError, RuntimeError) as exc:
                logger.debug("NVML initialization failed: %s", exc)
                code = -1
            self._initialized = True
            self._available = code == 0
            if self._available:
                import atexit

                if not self._shutdown_registered:
                    atexit.register(self._shutdown)
                    self._shutdown_registered = True

    @property
    def available(self) -> bool:
        return self._available

    def _bind_functions(self):
        spec = {
            "nvmlInit_v2": ([], ctypes.c_int),
            "nvmlInit": ([], ctypes.c_int),
            "nvmlShutdown": ([], ctypes.c_int),
            "nvmlErrorString": ([ctypes.c_int], ctypes.c_char_p),
            "nvmlSystemGetDriverVersion": ([ctypes.c_char_p, ctypes.c_uint], ctypes.c_int),
            "nvmlDeviceGetCount_v2": ([ctypes.POINTER(ctypes.c_uint)], ctypes.c_int),
            "nvmlDeviceGetCount": ([ctypes.POINTER(ctypes.c_uint)], ctypes.c_int),
            "nvmlDeviceGetHandleByIndex_v2": (
                [ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p)],
                ctypes.c_int,
            ),
            "nvmlDeviceGetHandleByIndex": (
                [ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p)],
                ctypes.c_int,
            ),
            "nvmlDeviceGetHandleByUUID": (
                [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)],
                ctypes.c_int,
            ),
            "nvmlDeviceGetHandleByPciBusId_v2": (
                [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)],
                ctypes.c_int,
            ),
            "nvmlDeviceGetHandleByPciBusId": (
                [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)],
                ctypes.c_int,
            ),
            "nvmlDeviceGetName": (
                [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint],
                ctypes.c_int,
            ),
            "nvmlDeviceGetPciInfo_v3": (
                [ctypes.c_void_p, ctypes.POINTER(_nvmlPciInfo_v3_t)],
                ctypes.c_int,
            ),
            "nvmlDeviceGetPciInfo_v2": (
                [ctypes.c_void_p, ctypes.POINTER(_nvmlPciInfo_v2_t)],
                ctypes.c_int,
            ),
            "nvmlDeviceGetPciInfo": (
                [ctypes.c_void_p, ctypes.POINTER(_nvmlPciInfo_v2_t)],
                ctypes.c_int,
            ),
            "nvmlDeviceGetMaxPcieLinkGeneration": (
                [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)],
                ctypes.c_int,
            ),
            "nvmlDeviceGetCurrPcieLinkGeneration": (
                [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)],
                ctypes.c_int,
            ),
            "nvmlDeviceGetMemoryInfo": (
                [ctypes.c_void_p, ctypes.POINTER(_nvmlMemory_t)],
                ctypes.c_int,
            ),
            "nvmlDeviceGetUtilizationRates": (
                [ctypes.c_void_p, ctypes.POINTER(_nvmlUtilization_t)],
                ctypes.c_int,
            ),
            "nvmlDeviceGetVbiosVersion": (
                [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint],
                ctypes.c_int,
            ),
            "nvmlDeviceGetCudaComputeCapability": (
                [
                    ctypes.c_void_p,
                    ctypes.POINTER(ctypes.c_int),
                    ctypes.POINTER(ctypes.c_int),
                ],
                ctypes.c_int,
            ),
        }
        for name, (argtypes, restype) in spec.items():
            fn = getattr(self._lib, name, None)
            if fn is not None:
                try:
                    fn.argtypes = argtypes
                    fn.restype = restype
                except AttributeError:
                    fn = None
            setattr(self, f"_{name}", fn)

    def _init(self):
        return self._call(["nvmlInit_v2", "nvmlInit"])

    def _shutdown(self):
        with self._lock:
            if not self._available or self._lib is None:
                return
            self._available = False
            try:
                self._check(self._call(["nvmlShutdown"]))
            except (OSError, RuntimeError, AttributeError) as exc:
                logger.debug("NVML shutdown failed: %s", exc)

    def _check(self, code):
        if code == 0:
            return
        msg = "Unknown NVML error"
        if self._nvmlErrorString is not None:
            try:
                raw = self._nvmlErrorString(code)
                if raw:
                    msg = raw.decode("utf-8")
            except (AttributeError, UnicodeDecodeError) as exc:
                logger.debug("Failed to decode NVML error string: %s", exc)
        raise RuntimeError(f"NVML error {code}: {msg}")

    def _call(self, names, *args):
        for name in names:
            fn = getattr(self, f"_{name}", None)
            if fn is not None:
                return fn(*args)
        raise RuntimeError(f"NVML functions {names} not available")

    def device_count(self):
        if not self._available:
            raise RuntimeError("NVML is not available")
        count = ctypes.c_uint()
        self._check(self._call(["nvmlDeviceGetCount_v2", "nvmlDeviceGetCount"], ctypes.byref(count)))
        return count.value

    def device_handle(self, gpu_id: str):
        if not self._available:
            raise RuntimeError("NVML is not available")
        handle = ctypes.c_void_p()
        gpu_id = gpu_id.strip()
        if gpu_id.isdigit():
            self._check(
                self._call(
                    ["nvmlDeviceGetHandleByIndex_v2", "nvmlDeviceGetHandleByIndex"],
                    int(gpu_id),
                    ctypes.byref(handle),
                )
            )
        elif gpu_id.startswith(("GPU-", "MIG-")):
            self._check(
                self._call(
                    ["nvmlDeviceGetHandleByUUID"],
                    gpu_id.encode("utf-8"),
                    ctypes.byref(handle),
                )
            )
        elif ":" in gpu_id:
            self._check(
                self._call(
                    [
                        "nvmlDeviceGetHandleByPciBusId_v2",
                        "nvmlDeviceGetHandleByPciBusId",
                    ],
                    gpu_id.encode("utf-8"),
                    ctypes.byref(handle),
                )
            )
        else:
            self._check(
                self._call(
                    ["nvmlDeviceGetHandleByIndex_v2", "nvmlDeviceGetHandleByIndex"],
                    int(gpu_id),
                    ctypes.byref(handle),
                )
            )
        return handle

    def device_name(self, handle):
        buf = ctypes.create_string_buffer(96)
        self._check(self._call(["nvmlDeviceGetName"], handle, buf, 96))
        return buf.value.decode("utf-8").strip()

    def pci_info(self, handle):
        attempts = (
            ("nvmlDeviceGetPciInfo_v3", _nvmlPciInfo_v3_t),
            ("nvmlDeviceGetPciInfo_v2", _nvmlPciInfo_v2_t),
            ("nvmlDeviceGetPciInfo", _nvmlPciInfo_v2_t),
        )
        attempted = []
        for name, info_type in attempts:
            fn = getattr(self, f"_{name}", None)
            if fn is None:
                continue
            attempted.append(name)
            info = info_type()
            code = self._call([name], handle, ctypes.byref(info))
            if code in _NVML_COMPATIBILITY_ERRORS:
                continue
            self._check(code)
            bus_id = info.busId.decode("utf-8").strip()
            if not bus_id and isinstance(info, _nvmlPciInfo_v3_t):
                bus_id = info.busIdLegacy.decode("utf-8").strip()
            if not re.match(
                r"^[0-9a-fA-F]{4,8}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9]$",
                bus_id,
            ):
                raise RuntimeError(f"Invalid NVML PCI bus id: {bus_id!r}")
            return bus_id
        raise RuntimeError(f"NVML PCI info functions unavailable: {attempted}")

    def max_pcie_generation(self, handle):
        gen = ctypes.c_uint()
        self._check(
            self._call(
                ["nvmlDeviceGetMaxPcieLinkGeneration"], handle, ctypes.byref(gen)
            )
        )
        return gen.value

    def current_pcie_generation(self, handle):
        gen = ctypes.c_uint()
        self._check(
            self._call(
                ["nvmlDeviceGetCurrPcieLinkGeneration"], handle, ctypes.byref(gen)
            )
        )
        return gen.value

    def memory_total(self, handle):
        mem = _nvmlMemory_t()
        self._check(self._call(["nvmlDeviceGetMemoryInfo"], handle, ctypes.byref(mem)))
        return mem.total

    def memory_used(self, handle):
        mem = _nvmlMemory_t()
        self._check(self._call(["nvmlDeviceGetMemoryInfo"], handle, ctypes.byref(mem)))
        return mem.used

    def utilization_gpu(self, handle):
        util = _nvmlUtilization_t()
        self._check(
            self._call(["nvmlDeviceGetUtilizationRates"], handle, ctypes.byref(util))
        )
        return float(util.gpu)

    def driver_version(self):
        buf = ctypes.create_string_buffer(80)
        self._check(self._call(["nvmlSystemGetDriverVersion"], buf, 80))
        return buf.value.decode("utf-8").strip()

    def vbios_version(self, handle):
        buf = ctypes.create_string_buffer(32)
        self._check(self._call(["nvmlDeviceGetVbiosVersion"], handle, buf, 32))
        return buf.value.decode("utf-8").strip()

    def compute_capability(self, handle):
        major = ctypes.c_int()
        minor = ctypes.c_int()
        self._check(
            self._call(
                ["nvmlDeviceGetCudaComputeCapability"],
                handle,
                ctypes.byref(major),
                ctypes.byref(minor),
            )
        )
        return f"{major.value}.{minor.value}"


_nvml = _NVML()


class _NvidiaSmiCache:
    """Thread-safe LRU cache for ``nvidia-smi`` output with a per-entry TTL.

    All reads and writes to the shared ``OrderedDict`` are serialized by a
    ``threading.Lock``, so the cache is safe to use in free-threaded (GIL=0)
    Python builds.
    """

    def __init__(self):
        self._cache = OrderedDict()
        self._lock = threading.Lock()

    def __call__(self, key, fetch):
        with self._lock:
            ttl = config.nvidia_smi_cache_ttl
        if ttl == 0:
            return fetch()

        with self._lock:
            now = time.monotonic()
            if key in self._cache:
                ts, value = self._cache[key]
                if now - ts < ttl:
                    self._cache.move_to_end(key)
                    return value
                del self._cache[key]
            value = fetch()
            self._cache[key] = (now, value)
            self._cache.move_to_end(key)
            maxsize = config.nvidia_smi_cache_maxsize
            while len(self._cache) > maxsize:
                self._cache.popitem(last=False)
            return value


_nvidia_smi_cache = _NvidiaSmiCache()


def _run_nvidia_smi(args, line_start=None, seperator=None):
    """Run ``nvidia-smi`` at most once per TTL; cache keyed by the command."""

    key = (tuple(args), line_start, seperator)
    return _nvidia_smi_cache(key, lambda: _run(args, line_start=line_start, seperator=seperator))


class NvidiaDevice(GPUDevice):
    fast_metrics_same_as_slow = False

    def __init__(self, cls, index):
        super().__init__(cls, index)
        self.gpu_id = self._get_gpu_id()

        if _nvml.available:
            try:
                self._init_from_nvml(cls)
                return
            except (RuntimeError, ValueError, IndexError, AttributeError) as exc:
                logger.debug("NVML device initialization failed, falling back to nvidia-smi: %s", exc)

        self._init_from_nvidia_smi(cls)

    def _get_gpu_id(self):
        if _nvml.available:
            try:
                gpu_count = _nvml.device_count()
            except (RuntimeError, OSError, ValueError) as exc:
                logger.debug("Failed to get NVML device count: %s", exc)
                gpu_count = 0
        else:
            try:
                gpu_count = len(_run_nvidia_smi(["nvidia-smi", "--list-gpus"]).splitlines())
            except (RuntimeError, OSError, ValueError) as exc:
                logger.debug("Failed to list NVIDIA GPUs: %s", exc)
                gpu_count = 0

        cudas = os.environ.get("CUDA_VISIBLE_DEVICES", "")
        cuda_list = [cuda.strip() for cuda in cudas.split(",")] if cudas.strip() else []
        if any(not cuda for cuda in cuda_list):
            raise ValueError("CUDA_VISIBLE_DEVICES contains an empty device entry")
        if gpu_count > 0 and os.environ.get("CUDA_DEVICE_ORDER", "") != "PCI_BUS_ID":
            warnings.warn(
                "Detected different devices in the system. Please make sure to set `CUDA_DEVICE_ORDER=PCI_BUS_ID` to avoid unexpected behavior.",
                RuntimeWarning,
                2,
            )
        if cuda_list and len(cuda_list) > self.index:
            return cuda_list[self.index]
        else:
            return str(self.index)

    def _init_from_nvml(self, cls):
        handle = _nvml.device_handle(self.gpu_id)

        model = _nvml.device_name(handle)
        total_memory = _nvml.memory_total(handle)
        driver = self._optional_nvml(_nvml.driver_version, "")
        firmware = self._optional_nvml(_nvml.vbios_version, "", handle)
        compute_cap = self._optional_nvml(_nvml.compute_capability, None, handle)
        pci_bus_id = self._optional_nvml(_nvml.pci_info, None, handle)
        pcie_gen_max = self._optional_nvml(_nvml.max_pcie_generation, None, handle)
        pcie_gen_current = self._optional_nvml(
            _nvml.current_pcie_generation, None, handle
        )

        if model.lower().startswith("nvidia"):
            model = model[len("nvidia"):]

        cls.model = model.strip().lower()
        cls.memory_total = int(total_memory)
        cls.vendor = "nvidia"
        cls.features = [compute_cap] if compute_cap else []
        cls.pcie = None
        if None not in (pci_bus_id, pcie_gen_max, pcie_gen_current):
            cls.pcie = Pcie(
                gen=int(pcie_gen_max), speed=int(pcie_gen_current), id=pci_bus_id
            )
        cls.gpu = GPU(driver=driver, firmware=firmware)

    @staticmethod
    def _optional_nvml(fetch, default, *args):
        try:
            return fetch(*args)
        except (OSError, RuntimeError, ValueError, AttributeError) as exc:
            logger.debug("Optional NVML metadata unavailable: %s", exc)
            return default

    def _init_from_nvidia_smi(self, cls):
        args = [
            "nvidia-smi",
            f"--id={self.gpu_id}",
            "--query-gpu=name,memory.total,pci.bus_id,pcie.link.gen.max,pcie.link.gen.current,driver_version",
            "--format=csv,noheader,nounits",
        ]

        result = _run_nvidia_smi(args=args, seperator="\n")

        model, total_memory, pci_bus_id, pcie_gen, pcie_width, driver = (result[0].split(", "))

        result = _run_nvidia_smi(args=["nvidia-smi", "-q", "-i", f"{self.gpu_id}"], seperator="\n")
        firmware = " ".join([line.split(":", 1)[1].strip() for line in result if "VBIOS" in line])

        if model.lower().startswith("nvidia"):
            model = model[len("nvidia"):]

        compute_cap = (
            _run_nvidia_smi(["nvidia-smi", "--format=csv", "--query-gpu=compute_cap", "-i", f"{self.gpu_id}"])
            .removeprefix("compute_cap\n")
        )

        cls.model = model.strip().lower()
        cls.memory_total = int(total_memory) * 1024 * 1024  # bytes
        cls.vendor = "nvidia"
        cls.features = [compute_cap]
        cls.pcie = Pcie(gen=int(pcie_gen), speed=int(pcie_width), id=pci_bus_id)
        cls.gpu = GPU(driver=driver, firmware=firmware)

    def _metrics_from_nvml(self):
        handle = _nvml.device_handle(self.gpu_id)
        return NvidiaGPUMetrics(
            memory_used=_nvml.memory_used(handle),
            memory_process=0,
            utilization=_nvml.utilization_gpu(handle),
        )

    def _metrics_from_nvidia_smi(self):
        args = [
            "nvidia-smi",
            f"--id={self.gpu_id}",
            "--query-gpu=memory.used,utilization.gpu",
            "--format=csv,noheader,nounits",
        ]
        used_memory, utilization = _run_nvidia_smi(args=args, seperator="\n")[0].split(", ")

        return NvidiaGPUMetrics(
            memory_used=int(used_memory) * 1024 * 1024,  # bytes
            memory_process=0,  # Bytes, TODO, get this
            utilization=float(utilization),
        )

    def metrics(self):
        try:
            if _nvml.available:
                try:
                    return self._metrics_from_nvml()
                except (RuntimeError, ValueError, IndexError, AttributeError) as exc:
                    logger.debug("NVML metrics failed, falling back to nvidia-smi: %s", exc)
            return self._metrics_from_nvidia_smi()

        except FileNotFoundError:
            raise FileNotFoundError(
                "The 'nvidia-smi' command was not found. Please ensure that the 'nvidia-utils' package is installed."
            )
