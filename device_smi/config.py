class Config:
    """Module-level configuration for ``device-smi``."""

    def __init__(self):
        # A TTL of 0 disables the nvidia-smi cache entirely so every call
        # runs the subprocess. Set it >0 to enable caching.
        self._nvidia_smi_cache_ttl = 0.0
        self._nvidia_smi_cache_maxsize = 16

    @property
    def nvidia_smi_cache_ttl(self) -> float:
        """How long ``nvidia-smi`` results are cached, in seconds.

        ``0.0`` disables caching and every call spawns a fresh subprocess.
        """
        return self._nvidia_smi_cache_ttl

    @nvidia_smi_cache_ttl.setter
    def nvidia_smi_cache_ttl(self, value: float) -> None:
        value = float(value)
        if value < 0:
            raise ValueError("nvidia_smi_cache_ttl must be greater than or equal to 0")
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


config = Config()
