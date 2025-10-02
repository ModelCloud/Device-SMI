import time
import pytest

from device_smi.device import Device


class DummyDevice:
    """A minimal fake device that pretends to provide metrics."""

    fast_metrics_same_as_slow = False

    def __init__(self, parent):
        self.parent = parent
        self._counter = 0

    def metrics(self):
        self._counter += 1
        return type("Metrics", (), {
            "memory_used": 42,
            "utilization": 0.5,
        })()


def test_close_does_not_crash():
    """
    Ensure that calling close() stops the metrics thread cleanly
    without raising AttributeError: 'NoneType' object has no attribute 'wait'.
    """
    d = Device("cpu", fast_metrics_interval=0.05)
    # Patch the device with our dummy (to avoid depending on real hardware)
    d.device = DummyDevice(d)

    # Let the thread run at least once
    time.sleep(0.1)

    # Close repeatedly to simulate race conditions
    for _ in range(5):
        d.close()
        time.sleep(0.05)

    # If we get here without exception, test passes
    assert True


def test_close_allows_metrics_reuse():
    """
    After closing, calling metrics() should still work (using slow path).
    """
    d = Device("cpu", fast_metrics_interval=0.05)
    d.device = DummyDevice(d)

    # Grab metrics normally
    m1 = d.metrics()
    assert m1.memory_used == 42
    assert isinstance(m1.utilization, float)

    # Close and check metrics still available
    d.close()
    m2 = d.metrics()
    assert m2.memory_used == 42
