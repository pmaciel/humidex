"""Tests for configuration module."""

import os
from unittest.mock import patch

import pytest

from humidex.config import Config


class TestConfig:
    """Tests for Config dataclass."""

    def test_defaults(self) -> None:
        config = Config()
        assert config.user_agent == "humidex/3.0.0"
        assert config.geocoder_timeout == pytest.approx(10.0)
        assert config.ecmwf_source == "aws"
        assert config.retry_max == 3
        assert config.retry_backoff == pytest.approx(1.0)

    def test_valid_sources(self) -> None:
        for source in ("ecmwf", "aws", "google", "azure"):
            config = Config(ecmwf_source=source)
            assert config.ecmwf_source == source

    def test_invalid_source(self) -> None:
        with pytest.raises(ValueError, match="Invalid ECMWF source"):
            Config(ecmwf_source="invalid")

    def test_frozen(self) -> None:
        config = Config()
        with pytest.raises(Exception):
            config.retry_max = 10


class TestConfigFromEnv:
    """Tests for environment variable configuration."""

    def test_from_env_defaults(self) -> None:
        keys = [
            "HUMIDEX_USER_AGENT",
            "HUMIDEX_GEOCODER_TIMEOUT",
            "HUMIDEX_ECMWF_SOURCE",
            "HUMIDEX_ECMWF_TIMEOUT",
            "HUMIDEX_RETRY_MAX",
            "HUMIDEX_RETRY_BACKOFF",
        ]
        with patch.dict(os.environ, {}, clear=False):
            for key in keys:
                os.environ.pop(key, None)
            config = Config.from_env()
        assert config.user_agent == "humidex/3.0.0"

    def test_from_env_overrides(self) -> None:
        with patch.dict(
            os.environ,
            {
                "HUMIDEX_USER_AGENT": "test-agent/1.0",
                "HUMIDEX_RETRY_MAX": "5",
                "HUMIDEX_ECMWF_SOURCE": "google",
            },
        ):
            config = Config.from_env()
        assert config.user_agent == "test-agent/1.0"
        assert config.retry_max == 5
        assert config.ecmwf_source == "google"
