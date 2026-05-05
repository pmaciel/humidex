"""Tests for main public API."""

from unittest.mock import MagicMock

import pytest

from humidex import get_humidex
from humidex.config import Config
from humidex.models import Location, WeatherData


class TestGetHumidex:
    """Tests for get_humidex public API function."""

    def test_default_flow(self) -> None:
        mock_location = Location(name="Bangkok", latitude=13.75, longitude=100.50)
        mock_weather = MagicMock()
        mock_result = MagicMock()

        with pytest.MonkeyPatch.context() as mp:
            import humidex

            mp.setattr(humidex, "geocode", lambda *a, **kw: mock_location)
            mp.setattr(humidex, "fetch_weather_data", lambda *a, **kw: mock_weather)
            mp.setattr(
                humidex,
                "calculate_humidex",
                lambda *a, **kw: mock_result,
            )

            result = get_humidex("Bangkok")

        assert result == mock_result

    def test_custom_geocoder(self) -> None:
        mock_geocoder = MagicMock()
        mock_location = Location(name="Custom", latitude=10.0, longitude=20.0)
        mock_geocoder.geocode.return_value = mock_location
        mock_weather = MagicMock()
        mock_result = MagicMock()

        with pytest.MonkeyPatch.context() as mp:
            import humidex

            mp.setattr(humidex, "fetch_weather_data", lambda *a, **kw: mock_weather)
            mp.setattr(
                humidex,
                "calculate_humidex",
                lambda *a, **kw: mock_result,
            )

            result = get_humidex("Custom", geocoder=mock_geocoder)

        mock_geocoder.geocode.assert_called_once_with("Custom")
        assert result == mock_result

    def test_custom_fetcher(self) -> None:
        mock_location = Location(name="Test", latitude=10.0, longitude=20.0)
        mock_fetcher = MagicMock()
        mock_weather = WeatherData(
            temperature_c=25.0,
            dewpoint_c=15.0,
            forecast_step=12,
            valid_time=MagicMock(),
        )
        mock_fetcher.fetch.return_value = mock_weather
        mock_result = MagicMock()

        with pytest.MonkeyPatch.context() as mp:
            import humidex

            mp.setattr(humidex, "geocode", lambda *a, **kw: mock_location)
            mp.setattr(
                humidex,
                "calculate_humidex",
                lambda *a, **kw: mock_result,
            )

            result = get_humidex("Test", fetcher=mock_fetcher)

        mock_fetcher.fetch.assert_called_once()
        assert result == mock_result

    def test_with_config(self) -> None:
        config = Config(retry_max=1)
        mock_location = Location(name="Test", latitude=10.0, longitude=20.0)
        mock_weather = MagicMock()
        mock_result = MagicMock()

        with pytest.MonkeyPatch.context() as mp:
            import humidex

            mp.setattr(humidex, "geocode", lambda *a, **kw: mock_location)
            mp.setattr(humidex, "fetch_weather_data", lambda *a, **kw: mock_weather)
            mp.setattr(
                humidex,
                "calculate_humidex",
                lambda *a, **kw: mock_result,
            )

            result = get_humidex("Test", config=config)

        assert result == mock_result
