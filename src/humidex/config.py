"""Configuration for humidex with environment variable overrides."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import ClassVar, TypeVar

T = TypeVar("T")


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

    user_agent: str = "humidex/5.0.0"
    geocoder_timeout: float = 10.0
    ecmwf_source: str = "aws"
    ecmwf_timeout: float = 60.0
    retry_max: int = 3
    retry_backoff: float = 1.0
    temp_min_c: float = -90.0
    temp_max_c: float = 60.0

    _valid_sources: ClassVar[frozenset[str]] = frozenset(
        {"ecmwf", "aws", "google", "azure"}
    )

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
            geocoder_timeout=_parse_env(
                "HUMIDEX_GEOCODER_TIMEOUT", cls.geocoder_timeout, float
            ),
            ecmwf_source=os.getenv("HUMIDEX_ECMWF_SOURCE", cls.ecmwf_source),
            ecmwf_timeout=_parse_env(
                "HUMIDEX_ECMWF_TIMEOUT", cls.ecmwf_timeout, float
            ),
            retry_max=_parse_env("HUMIDEX_RETRY_MAX", cls.retry_max, int),
            retry_backoff=_parse_env(
                "HUMIDEX_RETRY_BACKOFF", cls.retry_backoff, float
            ),
            temp_min_c=_parse_env("HUMIDEX_TEMP_MIN_C", cls.temp_min_c, float),
            temp_max_c=_parse_env("HUMIDEX_TEMP_MAX_C", cls.temp_max_c, float),
        )


def _parse_env(var_name: str, default: T, parser: Callable[[str], T]) -> T:
    raw = os.getenv(var_name)
    if raw is None:
        return default
    try:
        return parser(raw)
    except ValueError as exc:
        msg = f"Invalid value for {var_name}: {raw!r}"
        raise ValueError(msg) from exc


def get_config() -> Config:
    """Get a fresh default configuration, loading from environment."""
    return Config.from_env()
