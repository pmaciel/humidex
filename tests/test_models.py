"""Tests for data models."""

import pytest

from humidex.models import HumidexResult, Location, WeatherData


def test_location_valid() -> None:
    """Test creating a valid location."""
    loc = Location(name="Bangkok", latitude=13.7563, longitude=100.5018)
    assert loc.name == "Bangkok"
    assert loc.latitude == 13.7563
    assert loc.longitude == 100.5018


def test_location_invalid_latitude() -> None:
    """Test that invalid latitude raises ValueError."""
    with pytest.raises(ValueError, match="Latitude"):
        Location(name="Test", latitude=91.0, longitude=0.0)

    with pytest.raises(ValueError, match="Latitude"):
        Location(name="Test", latitude=-91.0, longitude=0.0)


def test_location_invalid_longitude() -> None:
    """Test that invalid longitude raises ValueError."""
    with pytest.raises(ValueError, match="Longitude"):
        Location(name="Test", latitude=0.0, longitude=181.0)

    with pytest.raises(ValueError, match="Longitude"):
        Location(name="Test", latitude=0.0, longitude=-181.0)


def test_weather_data() -> None:
    """Test creating weather data."""
    from datetime import datetime

    weather = WeatherData(
        temperature_c=32.0,
        dewpoint_c=24.0,
        forecast_step=0,
        valid_time=datetime(2026, 5, 5, 12, 0),
    )
    assert weather.temperature_c == 32.0
    assert weather.dewpoint_c == 24.0


def test_humidex_result_str() -> None:
    """Test string representation of HumidexResult."""
    from datetime import datetime

    loc = Location(name="Bangkok", latitude=13.7563, longitude=100.5018)
    weather = WeatherData(
        temperature_c=32.0,
        dewpoint_c=24.0,
        forecast_step=0,
        valid_time=datetime(2026, 5, 5, 12, 0),
    )
    result = HumidexResult(
        location=loc,
        humidex=40.2,
        comfort="Great discomfort; avoid exertion",
        weather=weather,
    )
    assert "Bangkok" in str(result)
    assert "40.2" in str(result)
    assert "Great discomfort" in str(result)
