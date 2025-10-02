import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from device_smi import Device
from device_smi.os import OSDevice


@pytest.fixture()
def os_device():
    device = Device("os")
    try:
        yield device
    finally:
        device.close()


def test_os_device_basic_attributes(os_device):
    assert os_device.type == "os"
    assert isinstance(os_device.device, OSDevice)
    assert isinstance(os_device.name, str) and os_device.name

    version = os_device.version
    assert isinstance(version, str) and version
    if version[0].isdigit():
        assert re.match(r"[0-9]+(\.[0-9]+)*", version)

    assert isinstance(os_device.kernel, str) and os_device.kernel
    assert isinstance(os_device.arch, str) and os_device.arch
    assert os_device.arch == os_device.arch.lower()
    assert re.match(r"[0-9a-z_\-]+", os_device.arch)


def test_os_device_metrics(os_device):
    assert os_device.metrics() is None
    assert os_device.device.fast_metrics_same_as_slow is True
    with pytest.raises(AttributeError):
        os_device.memory_used()
