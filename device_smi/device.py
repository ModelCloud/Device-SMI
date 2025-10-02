import platform
import threading
import warnings
from typing import Optional

from .amd import AMDDevice
from .apple import AppleDevice
from .base import _run
from .cpu import CPUDevice
from .intel import IntelDevice
from .nvidia import NvidiaDevice
from .os import OSDevice

IS_ROCM = False
try:
    import torch

    HAS_TORCH = True
    if torch.version.hip is not None:
        IS_ROCM = True
except BaseException:
    HAS_TORCH = False


class Device:
    def __init__(self, device, *, fast_metrics_interval: float = 0.200):
        # init attribute first to avoid IDE not attr warning
        # CPU/GPU Device
        self.memory_total = None
        self.type = None
        self.features = []
        self.vendor = None
        self.model = None
        self.device = None
        # OS Device
        self.arch = None
        self.version = None
        self.name = None
        self._fast_metrics_thread: Optional[threading.Thread] = None
        self._fast_metrics_cache = None
        self._fast_metrics_error: Optional[RuntimeError] = None
        self._fast_metrics_lock = threading.Lock()
        self._metrics_lock = threading.Lock()
        self._fast_metrics_stop_event: Optional[threading.Event] = None
        self._fast_metrics_interval = self._validate_fast_metrics_interval(fast_metrics_interval)
        self._fast_metrics_same_as_slow = False
        if HAS_TORCH and isinstance(device, torch.device):
            device_type = device.type.lower()
            device_index = device.index
        elif f"{device}".lower() == "os":
            self.device = OSDevice(self)
            self._configure_fast_metrics()
            return
        else:
            d = f"{device}".lower()
            if ":" in d:
                type, index = d.split(":")
                device_type = type
                device_index = (int(index))
            else:
                device_type = d
                device_index = 0

        self.pcie = None
        self.gpu = None

        if device_type == "cpu":
            self.device = CPUDevice(self)
        elif device_type == "xpu":
            self.device =  IntelDevice(self, device_index)
        elif device_type == "rocm" or IS_ROCM:
            self.device = AMDDevice(self, device_index)
        elif device_type == "cuda" and not IS_ROCM:
            self.device = NvidiaDevice(self, device_index)
        elif device_type == "gpu":
            if platform.system().lower() == "darwin":
                if platform.machine() == 'x86_64':
                    raise Exception("Not supported for macOS on Intel chips.")

                self.device = AppleDevice(self, device_index)
            else:
                if platform.system().lower() == "windows":
                    import os
                    import shutil
                    if not shutil.which("powershell.exe"):
                        psdir = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "WindowsPowerShell", "v1.0")
                        os.environ["PATH"] = os.environ.get("PATH", "") + ";" + psdir

                    for d in ["NVIDIA", "AMD", "INTEL"]:
                        result = _run(["powershell", "-Command", "Get-CimInstance", "Win32_VideoController", "-Filter", f"\"Name like '%{d}%'\""]).lower().splitlines()
                        if result:
                            if d == "INTEL":
                                self.device = IntelDevice(self, device_index)
                            elif d == "AMD":
                                self.device = AMDDevice(self, device_index)
                            else:
                                self.device = NvidiaDevice(self, device_index)
                            break
                else:
                    result = _run(["lspci"]).lower().splitlines()
                    result = "\n".join([
                        line for line in result
                        if any(keyword.lower() in line.lower() for keyword in ['vga', '3d', 'display'])
                    ]).lower()
                    if "nvidia" in result:
                        self.device = NvidiaDevice(self, device_index)
                    elif "amd" in result:
                        self.device = AMDDevice(self, device_index)
                    elif "intel" in result:
                        self.device = IntelDevice(self, device_index)
            if not self.device:
                raise ValueError(f"Unable to find requested device: {device}")
        else:
            raise Exception(f"The device {device_type} is not supported")

        self._configure_fast_metrics()

    def info(self):
        warnings.warn(
            "info() method is deprecated and will be removed in next release.",
            DeprecationWarning,
            stacklevel=2
        )
        return self

    def memory_used(self) -> int:
        return self.metrics().memory_used

    def utilization(self) -> float:
        return self.metrics().utilization

    def metrics(self, fast: bool = False):
        if not fast or self._fast_metrics_same_as_slow:
            metrics = self._collect_metrics()
            self._update_fast_cache(metrics)
            return metrics

        metrics, error = self._get_cached_metrics()
        if error is not None:
            raise error
        if metrics is not None:
            return metrics

        metrics = self._collect_metrics()
        self._update_fast_cache(metrics)
        return metrics

    def close(self):
        self._stop_fast_metrics_worker()

    def __str__(self):
        return str({k: v for k, v in self.__dict__.items() if k != 'device' and v is not None})

    def __del__(self):  # pragma: no cover - defensive cleanup only
        try:
            self._stop_fast_metrics_worker()
        except Exception:
            pass

    @staticmethod
    def _validate_fast_metrics_interval(value: float) -> float:
        try:
            interval = float(value)
        except (TypeError, ValueError) as exc:  # pragma: no cover - defensive branch
            raise ValueError("fast_metrics_interval must be a positive number") from exc
        if interval <= 0:
            raise ValueError("fast_metrics_interval must be greater than 0")
        return interval

    def _configure_fast_metrics(self):
        if not self.device:
            return
        self._fast_metrics_same_as_slow = bool(getattr(self.device, "fast_metrics_same_as_slow", False))
        if self._fast_metrics_same_as_slow:
            return

        self._fast_metrics_stop_event = threading.Event()
        thread_name = f"device-smi-metrics-{self.type or 'unknown'}"
        self._fast_metrics_thread = threading.Thread(
            target=self._fast_metrics_worker,
            name=thread_name,
            daemon=True,
        )
        self._fast_metrics_thread.start()

    def _fast_metrics_worker(self):
        assert self._fast_metrics_stop_event is not None
        while not self._fast_metrics_stop_event.is_set():
            try:
                metrics = self._collect_metrics()
            except Exception as exc:
                with self._fast_metrics_lock:
                    self._fast_metrics_error = RuntimeError(str(exc))
                if self._fast_metrics_stop_event.wait(self._fast_metrics_interval):
                    break
                continue

            self._update_fast_cache(metrics)
            if self._fast_metrics_stop_event.wait(self._fast_metrics_interval):
                break

    def _collect_metrics(self):
        with self._metrics_lock:
            return self.device.metrics()

    def _update_fast_cache(self, metrics):
        if self._fast_metrics_same_as_slow:
            return
        with self._fast_metrics_lock:
            self._fast_metrics_cache = metrics
            self._fast_metrics_error = None

    def _get_cached_metrics(self):
        with self._fast_metrics_lock:
            return self._fast_metrics_cache, self._fast_metrics_error

    def _stop_fast_metrics_worker(self):
        if self._fast_metrics_stop_event is None:
            return
        self._fast_metrics_stop_event.set()
        thread = self._fast_metrics_thread
        self._fast_metrics_thread = None
        self._fast_metrics_stop_event = None
        if thread and thread.is_alive():
            thread.join(timeout=0.1)
