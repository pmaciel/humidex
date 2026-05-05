"""Tests for main public API."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

from humidex import get_humidex
from humidex.config import Config
from humidex.models import Location, WeatherData


def _make_fakes(
    location: Location,
    weather: object | None = None,
) -> tuple[MagicMock, MagicMock]:
    """Build fake geocoder and fetcher returning the given location/weather."""
    fake_geocoder = MagicMock()
    fake_geocoder.geocode.return_value = location
    fake_fetcher = MagicMock()
    fake_fetcher.fetch.return_value = weather if weather is not None else MagicMock()
    return fake_geocoder, fake_fetcher


class TestGetHumidex:
    """Tests for get_humidex public API function."""

    def test_default_flow(self) -> None:
        location = Location(name="Bangkok", latitude=13.75, longitude=100.50)
        weather = WeatherData(
            temperature_c=30.0,
            dewpoint_c=24.0,
            forecast_step=0,
            valid_time=datetime.now(tz=timezone.utc),
        )
        geocoder, fetcher = _make_fakes(location, weather)

        result = get_humidex("Bangkok", geocoder=geocoder, fetcher=fetcher)

        geocoder.geocode.assert_called_once_with("Bangkok")
        fetcher.fetch.assert_called_once()
        assert result.location == location
        assert result.weather == weather

    def test_with_location_object(self) -> None:
        location = Location(name="Test", latitude=10.0, longitude=20.0)
        weather = WeatherData(
            temperature_c=25.0,
            dewpoint_c=15.0,
            forecast_step=0,
            valid_time=datetime.now(tz=timezone.utc),
        )
        geocoder, fetcher = _make_fakes(location, weather)

        result = get_humidex(location, geocoder=geocoder, fetcher=fetcher)

        # Geocoder must NOT be called when a Location is passed.
        geocoder.geocode.assert_not_called()
        fetcher.fetch.assert_called_once()
        assert result.location == location

    def test_custom_geocoder(self) -> None:
        custom_location = Location(name="Custom", latitude=10.0, longitude=20.0)
        custom_geocoder = MagicMock()
        custom_geocoder.geocode.return_value = custom_location
        weather = WeatherData(
            temperature_c=20.0,
            dewpoint_c=10.0,
            forecast_step=0,
            valid_time=datetime.now(tz=timezone.utc),
        )
        fetcher = MagicMock()
        fetcher.fetch.return_value = weather

        result = get_humidex("Custom", geocoder=custom_geocoder, fetcher=fetcher)

        custom_geocoder.geocode.assert_called_once_with("Custom")
        assert result.location == custom_location

    def test_custom_fetcher(self) -> None:
        location = Location(name="Test", latitude=10.0, longitude=20.0)
        custom_fetcher = MagicMock()
        weather = WeatherData(
            temperature_c=25.0,
            dewpoint_c=15.0,
            forecast_step=12,
            valid_time=datetime.now(tz=timezone.utc),
        )
        custom_fetcher.fetch.return_value = weather
        geocoder = MagicMock()
        geocoder.geocode.return_value = location

        result = get_humidex("Test", geocoder=geocoder, fetcher=custom_fetcher)

        custom_fetcher.fetch.assert_called_once()
        assert result.weather == weather

    def test_with_config(self) -> None:
        config = Config(retry_max=1)
        location = Location(name="Test", latitude=10.0, longitude=20.0)
        weather = WeatherData(
            temperature_c=22.0,
            dewpoint_c=12.0,
            forecast_step=0,
            valid_time=datetime.now(tz=timezone.utc),
        )
        geocoder, fetcher = _make_fakes(location, weather)

        result = get_humidex("Test", config=config, geocoder=geocoder, fetcher=fetcher)

        assert result.location == location
