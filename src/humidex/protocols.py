"""Protocol definitions for dependency injection."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from humidex.models import Location, WeatherData


@runtime_checkable
class Geocoder(Protocol):
    """Protocol for geocoding services."""

    def geocode(self, place_name: str) -> Location:
        """Convert a place name to a Location.

        Args:
            place_name: Human-readable place name.

        Returns:
            Location with coordinates.

        Raises:
            GeocodingError: If geocoding fails.
        """
        ...


@runtime_checkable
class WeatherFetcher(Protocol):
    """Protocol for weather data fetchers."""

    def fetch(self, location: Location, step: int = 0) -> WeatherData:
        """Fetch weather data for a location.

        Args:
            location: Location to fetch data for.
            step: Forecast step in hours (0 = analysis).

        Returns:
            WeatherData with temperature and dewpoint.

        Raises:
            DataFetchError: If data cannot be fetched.
        """
        ...
