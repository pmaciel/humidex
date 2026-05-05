"""Tests for calculator module."""

from datetime import datetime

import pytest

from humidex.calculator import calculate_humidex, get_comfort_category
from humidex.models import HumidexResult, Location, WeatherData


@pytest.fixture
def location() -> Location:
    """Create a test location."""
    return Location(name="Bangkok", latitude=13.7563, longitude=100.5018)


@pytest.fixture
def hot_weather() -> WeatherData:
    """Create hot and humid weather data."""
    return WeatherData(
        temperature_c=32.0,
        dewpoint_c=24.0,
        forecast_step=0,
        valid_time=datetime(2026, 5, 5, 12, 0),
    )


@pytest.fixture
def mild_weather() -> WeatherData:
    """Create mild weather data."""
    return WeatherData(
        temperature_c=22.0,
        dewpoint_c=12.0,
        forecast_step=0,
        valid_time=datetime(2026, 5, 5, 12, 0),
    )


def test_get_comfort_category_dangerous() -> None:
    """Test dangerous humidex category."""
    assert "Dangerous" in get_comfort_category(46.0)
    assert "Dangerous" in get_comfort_category(50.0)


def test_get_comfort_category_great_discomfort() -> None:
    """Test great discomfort category."""
    assert "Great discomfort" in get_comfort_category(40.0)
    assert "Great discomfort" in get_comfort_category(45.0)


def test_get_comfort_category_some_discomfort() -> None:
    """Test some discomfort category."""
    assert "Some discomfort" in get_comfort_category(30.0)
    assert "Some discomfort" in get_comfort_category(35.0)


def test_get_comfort_category_little_discomfort() -> None:
    """Test little discomfort category."""
    assert "Little discomfort" in get_comfort_category(20.0)
    assert "Little discomfort" in get_comfort_category(25.0)


def test_get_comfort_category_comfortable() -> None:
    """Test comfortable category."""
    assert get_comfort_category(15.0) == "Comfortable"
    assert get_comfort_category(0.0) == "Comfortable"


def test_calculate_humidex_hot(location: Location, hot_weather: WeatherData) -> None:
    """Test humidex calculation for hot weather."""
    result = calculate_humidex(location, hot_weather)

    assert isinstance(result, HumidexResult)
    assert result.location == location
    assert result.humidex > hot_weather.temperature_c
    assert result.comfort in [
        "Some discomfort",
        "Great discomfort; avoid exertion",
        "Dangerous; possible heat stroke",
    ]


def test_calculate_humidex_mild(location: Location, mild_weather: WeatherData) -> None:
    """Test humidex calculation for mild weather."""
    result = calculate_humidex(location, mild_weather)

    assert isinstance(result, HumidexResult)
    assert result.humidex > 0
    assert result.weather == mild_weather
