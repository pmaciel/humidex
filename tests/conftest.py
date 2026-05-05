"""Shared test fixtures for humidex tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from humidex.config import Config
from humidex.models import HumidexResult, Location, WeatherData


@pytest.fixture
def config() -> Config:
    """Create a test configuration."""
    return Config(
        retry_max=1,
        retry_backoff=0.01,
        geocoder_timeout=5.0,
        ecmwf_timeout=10.0,
    )


@pytest.fixture
def location() -> Location:
    """Create a test location (Bangkok)."""
    return Location(name="Bangkok", latitude=13.7563, longitude=100.5018)


@pytest.fixture
def london_location() -> Location:
    """Create a test location (London)."""
    return Location(name="London", latitude=51.5074, longitude=-0.1278)


@pytest.fixture
def hot_weather() -> WeatherData:
    """Create hot and humid weather data."""
    return WeatherData(
        temperature_c=32.0,
        dewpoint_c=24.0,
        forecast_step=0,
        valid_time=datetime(2026, 5, 5, 12, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def mild_weather() -> WeatherData:
    """Create mild weather data."""
    return WeatherData(
        temperature_c=22.0,
        dewpoint_c=12.0,
        forecast_step=0,
        valid_time=datetime(2026, 5, 5, 12, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def cold_weather() -> WeatherData:
    """Create cold weather data."""
    return WeatherData(
        temperature_c=5.0,
        dewpoint_c=0.0,
        forecast_step=0,
        valid_time=datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def hot_result(location: Location, hot_weather: WeatherData) -> HumidexResult:
    """Create a humidex result for hot weather."""
    return HumidexResult(
        location=location,
        humidex=40.2,
        comfort="Great discomfort; avoid exertion",
        weather=hot_weather,
    )
