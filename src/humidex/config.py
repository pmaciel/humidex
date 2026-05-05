"""Configuration for humidex with environment variable overrides."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Immutable configuration for humidex.

    Environment variables (all optional):
        HUMIDEX_USER_AGENT: User agent for geocoding requests.
        HUMIDEX_GEOCODER_TIMEOUT: Timeout in seconds for geocoding.
        HUMIDEX_ECMWF_SOURCE: ECMWF data source (ecmwf, aws, google, azure).
        HUMIDEX_ECMWF_TIMEOUT: Timeout in seconds for ECMWF data fetch.
        HUMIDEX_RETRY_MAX: Maximum number of retries for network operations.
        HUMIDEX_RETRY_BACKOFF: Base backoff in seconds for retries.
        HUMIDEX_TEMP_MIN_C: Minimum valid temperature in Celsius.
        HUMIDEX_TEMP_MAX_C: Maximum valid temperature in Celsius.
    """

    user_agent: str = "humidex/4.0.0"
    geocoder_timeout: float = 10.0
    ecmwf_source: str = "aws"
    ecmwf_timeout: float = 60.0
    retry_max: int = 3
    retry_backoff: float = 1.0
    temp_min_c: float = -90.0
    temp_max_c: float = 60.0

    _valid_sources = frozenset({"ecmwf", "aws", "google", "azure"})

    def __post_init__(self) -> None:
        if self.ecmwf_source not in self._valid_sources:
            msg = (
                f"Invalid ECMWF source: {self.ecmwf_source}. "
                f"Valid sources: {', '.join(sorted(self._valid_sources))}"
            )
            raise ValueError(msg)
        if self.temp_min_c > self.temp_max_c:
            msg = (
                f"temp_min_c ({self.temp_min_c}) must be <= "
                f"temp_max_c ({self.temp_max_c})"
            )
            raise ValueError(msg)

    @classmethod
    def from_env(cls) -> Config:
        """Create configuration from environment variables."""
        return cls(
            user_agent=os.getenv("HUMIDEX_USER_AGENT", cls.user_agent),
            geocoder_timeout=float(
                os.getenv("HUMIDEX_GEOCODER_TIMEOUT", cls.geocoder_timeout)
            ),
            ecmwf_source=os.getenv("HUMIDEX_ECMWF_SOURCE", cls.ecmwf_source),
            ecmwf_timeout=float(
                os.getenv("HUMIDEX_ECMWF_TIMEOUT", cls.ecmwf_timeout)
            ),
            retry_max=int(os.getenv("HUMIDEX_RETRY_MAX", cls.retry_max)),
            retry_backoff=float(
                os.getenv("HUMIDEX_RETRY_BACKOFF", cls.retry_backoff)
            ),
            temp_min_c=float(os.getenv("HUMIDEX_TEMP_MIN_C", cls.temp_min_c)),
            temp_max_c=float(os.getenv("HUMIDEX_TEMP_MAX_C", cls.temp_max_c)),
        )


def get_config() -> Config:
    """Get a fresh default configuration, loading from environment."""
    return Config.from_env()
