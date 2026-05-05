"""End-to-end integration tests using protocol fakes.

These tests exercise the full pipeline (geocode → fetch → calculate)
through both ``HumidexClient`` and the module-level ``get_humidex`` helper,
using hand-written fakes that implement the ``Geocoder`` and
``WeatherFetcher`` protocols (no ``MagicMock``).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from humidex import HumidexClient, get_humidex
from humidex.errors import PlaceNotFoundError
from humidex.models import HumidexResult, Location, WeatherData
from humidex.protocols import Geocoder, WeatherFetcher

# Fixed test data — Bangkok-ish hot/humid conditions.
_FIXED_LOCATION = Location(name="Testville", latitude=13.75, longitude=100.50)
_FIXED_WEATHER = WeatherData(
    temperature_c=32.0,
    dewpoint_c=24.0,
    forecast_step=0,
    valid_time=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
)


class FakeGeocoder:
    """Geocoder fake returning a fixed Location for any place name.

    Optionally raises ``PlaceNotFoundError`` to simulate lookup failure.
    """

    def __init__(
        self,
        location: Location = _FIXED_LOCATION,
        *,
        raise_not_found: bool = False,
    ) -> None:
        self._location = location
        self._raise_not_found = raise_not_found
        self.calls: list[str] = []

    def geocode(self, place_name: str) -> Location:
        self.calls.append(place_name)
        if self._raise_not_found:
            msg = f"Place not found: {place_name}"
            raise PlaceNotFoundError(msg)
        return self._location


class FakeFetcher:
    """WeatherFetcher fake returning fixed WeatherData for any input."""

    def __init__(self, weather: WeatherData = _FIXED_WEATHER) -> None:
        self._weather = weather
        self.calls: list[tuple[Location, int]] = []

    def fetch(self, location: Location, step: int = 0) -> WeatherData:
        self.calls.append((location, step))
        return self._weather


def test_protocol_conformance() -> None:
    """Fakes must satisfy the runtime-checkable protocols."""
    assert isinstance(FakeGeocoder(), Geocoder)
    assert isinstance(FakeFetcher(), WeatherFetcher)


def test_get_humidex_with_place_name_string() -> None:
    """Full pipeline with a place-name string returns a valid HumidexResult."""
    geocoder = FakeGeocoder()
    fetcher = FakeFetcher()

    result = get_humidex("Bangkok", geocoder=geocoder, fetcher=fetcher)

    assert isinstance(result, HumidexResult)
    assert geocoder.calls == ["Bangkok"]
    assert fetcher.calls == [(_FIXED_LOCATION, 0)]
    # T=32C, Td=24C → humidex ≈ 43.3°C via thermofeel.
    assert result.humidex == pytest.approx(43.3, abs=0.5)
    assert isinstance(result.humidex, float)
    assert 35.0 < result.humidex < 50.0
    assert result.location == _FIXED_LOCATION
    assert result.weather == _FIXED_WEATHER
    assert result.comfort  # non-empty category string


def test_client_with_location_object_skips_geocoder() -> None:
    """Passing a Location directly must NOT invoke the geocoder."""
    geocoder = FakeGeocoder()
    fetcher = FakeFetcher()
    client = HumidexClient(geocoder=geocoder, fetcher=fetcher)

    loc = Location(name="Direct", latitude=0.0, longitude=0.0)
    result = client.get_humidex(loc, step=6)

    assert geocoder.calls == []
    assert fetcher.calls == [(loc, 6)]
    assert isinstance(result, HumidexResult)
    assert result.location is loc
    assert result.weather.forecast_step == 0  # from fake weather


def test_place_not_found_propagates() -> None:
    """PlaceNotFoundError raised by the geocoder must propagate."""
    geocoder = FakeGeocoder(raise_not_found=True)
    fetcher = FakeFetcher()

    with pytest.raises(PlaceNotFoundError, match="Nowhere"):
        get_humidex("Nowhere", geocoder=geocoder, fetcher=fetcher)

    assert geocoder.calls == ["Nowhere"]
    assert fetcher.calls == []  # fetcher must not be called after failure
