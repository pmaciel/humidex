"""High-level client for humidex operations."""

from __future__ import annotations

from humidex.calculator import calculate_humidex
from humidex.config import Config, get_config
from humidex.fetcher import ECMWFFetcher
from humidex.geocoder import NominatimGeocoder
from humidex.models import HumidexResult, Location
from humidex.protocols import Geocoder, WeatherFetcher


class HumidexClient:
    """High-level client for humidex calculations.

    Holds configuration, geocoder, and weather fetcher as instance
    attributes, eliminating module-level global state.
    """

    def __init__(
        self,
        config: Config | None = None,
        geocoder: Geocoder | None = None,
        fetcher: WeatherFetcher | None = None,
    ) -> None:
        """Initialize the client.

        Args:
            config: Configuration. Creates default if not provided.
            geocoder: Geocoder. Creates NominatimGeocoder if not provided.
            fetcher: Weather fetcher. Creates ECMWFFetcher if not provided.
        """
        self._config = config or get_config()

        if geocoder is not None:
            self._geocoder = geocoder
        else:
            self._geocoder = NominatimGeocoder(config=self._config)

        if fetcher is not None:
            self._fetcher = fetcher
        else:
            self._fetcher = ECMWFFetcher(config=self._config)

    def get_humidex(
        self,
        place_or_location: str | Location,
        step: int = 0,
    ) -> HumidexResult:
        """Get humidex for a place name or coordinates.

        Args:
            place_or_location: Place name (str) or Location object.
            step: Forecast step in hours (0 = analysis).

        Returns:
            HumidexResult with humidex value and comfort description.
        """
        if isinstance(place_or_location, str):
            location = self._geocoder.geocode(place_or_location)
        else:
            location = place_or_location

        weather = self._fetcher.fetch(location, step=step)

        return calculate_humidex(location, weather, config=self._config)
