import time

import pytest

from device_smi import Device, settings
from device_smi.nvidia import _NvidiaSmiCache, _nvml, _run_nvidia_smi


def test_settings_ttl_and_maxsize():
    original_ttl = settings.nvidia_smi_cache_ttl
    original_maxsize = settings.nvidia_smi_cache_maxsize
    try:
        settings.nvidia_smi_cache_ttl = 2.0
        settings.nvidia_smi_cache_maxsize = 8
        assert settings.nvidia_smi_cache_ttl == 2.0
        assert settings.nvidia_smi_cache_maxsize == 8

        with pytest.raises(ValueError):
            settings.nvidia_smi_cache_ttl = 0
        with pytest.raises(ValueError):
            settings.nvidia_smi_cache_maxsize = 0
        with pytest.raises(ValueError):
            settings.nvidia_smi_cache_ttl = -1
    finally:
        settings.nvidia_smi_cache_ttl = original_ttl
        settings.nvidia_smi_cache_maxsize = original_maxsize


def test_device_settings_exposed():
    assert Device.settings is settings
    assert hasattr(settings, "nvidia_smi_cache_ttl")
    assert hasattr(settings, "nvidia_smi_cache_maxsize")


def test_nvidia_smi_cache_returns_cached_value_within_ttl():
    original_ttl = settings.nvidia_smi_cache_ttl
    settings.nvidia_smi_cache_ttl = 0.2
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
        settings.nvidia_smi_cache_ttl = original_ttl


def test_nvidia_smi_cache_lru_eviction():
    original_maxsize = settings.nvidia_smi_cache_maxsize
    settings.nvidia_smi_cache_maxsize = 2
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
        settings.nvidia_smi_cache_maxsize = original_maxsize


def test_run_nvidia_smi_uses_cache(monkeypatch):
    original_ttl = settings.nvidia_smi_cache_ttl
    settings.nvidia_smi_cache_ttl = 0.5
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
        settings.nvidia_smi_cache_ttl = original_ttl


def test_nvml_singleton_does_not_crash_without_gpu():
    assert _nvml._initialized is True
    assert isinstance(_nvml.available, bool)
