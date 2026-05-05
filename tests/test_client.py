"""Tests for client module."""

from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest

from humidex.client import HumidexClient
from humidex.config import Config
from humidex.models import Location


@pytest.fixture
def mock_calculate(monkeypatch: pytest.MonkeyPatch) -> Iterator[MagicMock]:
    """Patch humidex.client.calculate_humidex with a mock returning a mock result."""
    mock_result = MagicMock()
    from humidex import client as client_module

    monkeypatch.setattr(
        client_module, "calculate_humidex", lambda *a, **kw: mock_result
    )
    yield mock_result


class TestHumidexClient:
    """Tests for HumidexClient."""

    def test_init_with_defaults(self) -> None:
        client = HumidexClient()
        assert isinstance(client, HumidexClient)

    def test_init_with_custom_config(self, config: Config) -> None:
        client = HumidexClient(config=config)
        assert client._config == config

    def test_init_with_custom_geocoder_and_fetcher(self) -> None:
        mock_geocoder = MagicMock()
        mock_fetcher = MagicMock()

        client = HumidexClient(geocoder=mock_geocoder, fetcher=mock_fetcher)

        assert client._geocoder is mock_geocoder
        assert client._fetcher is mock_fetcher

    def test_get_humidex_with_place_name(self, mock_calculate: MagicMock) -> None:
        mock_location = Location(name="Bangkok", latitude=13.75, longitude=100.50)
        mock_weather = MagicMock()

        mock_geocoder = MagicMock()
        mock_geocoder.geocode.return_value = mock_location

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_weather

        client = HumidexClient(geocoder=mock_geocoder, fetcher=mock_fetcher)

        result = client.get_humidex("Bangkok")

        mock_geocoder.geocode.assert_called_once_with("Bangkok")
        mock_fetcher.fetch.assert_called_once_with(mock_location, step=0)
        assert result == mock_calculate

    def test_get_humidex_with_location(self, mock_calculate: MagicMock) -> None:
        mock_location = Location(name="Test", latitude=10.0, longitude=20.0)
        mock_weather = MagicMock()

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_weather

        mock_geocoder = MagicMock()

        client = HumidexClient(geocoder=mock_geocoder, fetcher=mock_fetcher)

        result = client.get_humidex(mock_location)

        mock_geocoder.geocode.assert_not_called()
        mock_fetcher.fetch.assert_called_once_with(mock_location, step=0)
        assert result == mock_calculate

    def test_get_humidex_with_step(self, mock_calculate: MagicMock) -> None:
        mock_location = Location(name="Test", latitude=10.0, longitude=20.0)
        mock_weather = MagicMock()

        mock_geocoder = MagicMock()
        mock_geocoder.geocode.return_value = mock_location

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_weather

        client = HumidexClient(geocoder=mock_geocoder, fetcher=mock_fetcher)

        client.get_humidex("Test", step=12)

        mock_fetcher.fetch.assert_called_once_with(mock_location, step=12)
