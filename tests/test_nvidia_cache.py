import threading
import time

import pytest

from device_smi import Device, config
from device_smi.nvidia import _NvidiaSmiCache, _nvml, _run_nvidia_smi


def test_config_ttl_and_maxsize():
    original_ttl = config.nvidia_smi_cache_ttl
    original_maxsize = config.nvidia_smi_cache_maxsize
    try:
        assert config.nvidia_smi_cache_ttl == 0.0

        config.nvidia_smi_cache_ttl = 2.0
        config.nvidia_smi_cache_maxsize = 8
        assert config.nvidia_smi_cache_ttl == 2.0
        assert config.nvidia_smi_cache_maxsize == 8

        # TTL may be 0 (disabled); maxsize must remain positive.
        config.nvidia_smi_cache_ttl = 0
        with pytest.raises(ValueError):
            config.nvidia_smi_cache_maxsize = 0
        with pytest.raises(ValueError):
            config.nvidia_smi_cache_maxsize = -1
        with pytest.raises(ValueError):
            config.nvidia_smi_cache_ttl = -1
    finally:
        config.nvidia_smi_cache_ttl = original_ttl
        config.nvidia_smi_cache_maxsize = original_maxsize


def test_device_config_exposed():
    assert Device.config is config
    assert hasattr(config, "nvidia_smi_cache_ttl")
    assert hasattr(config, "nvidia_smi_cache_maxsize")


def test_nvidia_smi_cache_disabled_when_ttl_zero():
    original_ttl = config.nvidia_smi_cache_ttl
    config.nvidia_smi_cache_ttl = 0
    try:
        cache = _NvidiaSmiCache()
        call_count = 0

        def fetch():
            nonlocal call_count
            call_count += 1
            return f"result-{call_count}"

        v1 = cache("key", fetch)
        v2 = cache("key", fetch)
        assert v1 == "result-1"
        assert v2 == "result-2"
        assert call_count == 2
    finally:
        config.nvidia_smi_cache_ttl = original_ttl


def test_nvidia_smi_cache_returns_cached_value_within_ttl():
    original_ttl = config.nvidia_smi_cache_ttl
    config.nvidia_smi_cache_ttl = 0.2
    try:
        cache = _NvidiaSmiCache()
        call_count = 0

        def fetch():
            nonlocal call_count
            call_count += 1
            return f"result-{call_count}"

        v1 = cache("key", fetch)
        v2 = cache("key", fetch)
        assert v1 == v2 == "result-1"
        assert call_count == 1

        time.sleep(0.25)
        v3 = cache("key", fetch)
        assert v3 == "result-2"
        assert call_count == 2
    finally:
        config.nvidia_smi_cache_ttl = original_ttl


def test_nvidia_smi_cache_lru_eviction():
    original_ttl = config.nvidia_smi_cache_ttl
    original_maxsize = config.nvidia_smi_cache_maxsize
    config.nvidia_smi_cache_ttl = 2.0
    config.nvidia_smi_cache_maxsize = 2
    try:
        cache = _NvidiaSmiCache()
        cache("a", lambda: 1)
        cache("b", lambda: 2)
        cache("a", lambda: 1)  # refresh a
        cache("c", lambda: 3)  # evicts b
        assert "b" not in cache._cache
        assert "a" in cache._cache
        assert "c" in cache._cache
    finally:
        config.nvidia_smi_cache_ttl = original_ttl
        config.nvidia_smi_cache_maxsize = original_maxsize


def test_run_nvidia_smi_uses_cache(monkeypatch):
    original_ttl = config.nvidia_smi_cache_ttl
    config.nvidia_smi_cache_ttl = 0.5
    try:
        call_count = 0

        def fake_run(args, line_start=None, seperator=None):
            nonlocal call_count
            call_count += 1
            return ["line"] if seperator else "str"

        monkeypatch.setattr("device_smi.nvidia._run", fake_run)

        from device_smi import nvidia as nvidia_module

        old_cache = nvidia_module._nvidia_smi_cache
        nvidia_module._nvidia_smi_cache = _NvidiaSmiCache()
        try:
            r1 = _run_nvidia_smi(["nvidia-smi", "--query-gpu=name"], seperator="\n")
            r2 = _run_nvidia_smi(["nvidia-smi", "--query-gpu=name"], seperator="\n")
            assert r1 == r2 == ["line"]
            assert call_count == 1
        finally:
            nvidia_module._nvidia_smi_cache = old_cache
    finally:
        config.nvidia_smi_cache_ttl = original_ttl


def test_nvidia_smi_cache_is_thread_safe():
    original_ttl = config.nvidia_smi_cache_ttl
    config.nvidia_smi_cache_ttl = 2.0
    try:
        cache = _NvidiaSmiCache()
        call_count = 0
        results = []
        lock = threading.Lock()

        def fetch():
            nonlocal call_count
            call_count += 1
            time.sleep(0.001)
            return call_count

        def worker():
            value = cache("key", fetch)
            with lock:
                results.append(value)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads should observe the same cached value.
        assert len(set(results)) == 1
    finally:
        config.nvidia_smi_cache_ttl = original_ttl


def test_nvml_singleton_does_not_crash_without_gpu():
    assert _nvml._initialized is True
    assert isinstance(_nvml.available, bool)
