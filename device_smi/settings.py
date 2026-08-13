class Settings:
    """Module-level settings for ``device-smi``."""

    def __init__(self):
        self._nvidia_smi_cache_ttl = 1.0
        self._nvidia_smi_cache_maxsize = 16

    @property
    def nvidia_smi_cache_ttl(self) -> float:
        """How long ``nvidia-smi`` results are cached, in seconds."""
        return self._nvidia_smi_cache_ttl

    @nvidia_smi_cache_ttl.setter
    def nvidia_smi_cache_ttl(self, value: float) -> None:
        value = float(value)
        if value <= 0:
            raise ValueError("nvidia_smi_cache_ttl must be greater than 0")
        self._nvidia_smi_cache_ttl = value

    @property
    def nvidia_smi_cache_maxsize(self) -> int:
        """Maximum number of distinct ``nvidia-smi`` query results kept in the LRU cache."""
        return self._nvidia_smi_cache_maxsize

    @nvidia_smi_cache_maxsize.setter
    def nvidia_smi_cache_maxsize(self, value: int) -> None:
        value = int(value)
        if value <= 0:
            raise ValueError("nvidia_smi_cache_maxsize must be greater than 0")
        self._nvidia_smi_cache_maxsize = value


settings = Settings()
