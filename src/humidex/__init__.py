"""Humidex - Retrieve humidex values for any location using ECMWF open data.

Public API:
    get_humidex: Main function to get humidex for a place name or Location.
    HumidexClient: High-level client for explicit dependency management.
    HumidexResult, Location, WeatherData: Data models.
    HumidexResultDict: TypedDict for result serialization.
    Config: Configuration with environment variable support.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from humidex.calculator import calculate_humidex, get_comfort_category
from humidex.client import HumidexClient
from humidex.config import Config
from humidex.errors import (
    CalculationError,
    DataFetchError,
    DataParseError,
    GeocodingError,
    GeocodingServiceError,
    HumidexError,
    InvalidStepError,
    PlaceNotFoundError,
)
from humidex.fetcher import fetch_weather_data
from humidex.formatter import format_human, format_json
from humidex.geocoder import geocode
from humidex.models import (
    MAX_LAT,
    MAX_LON,
    MAX_TEMP_C,
    MIN_LAT,
    MIN_LON,
    MIN_TEMP_C,
    HumidexResult,
    HumidexResultDict,
    Location,
    WeatherData,
)
from humidex.protocols import Geocoder, WeatherFetcher

try:
    __version__ = _pkg_version("humidex")
except PackageNotFoundError:
    __version__ = "0.0.0+local"

__all__ = [
    "MAX_LAT",
    "MAX_LON",
    "MAX_TEMP_C",
    "MIN_LAT",
    "MIN_LON",
    "MIN_TEMP_C",
    "CalculationError",
    "Config",
    "DataFetchError",
    "DataParseError",
    "Geocoder",
    "GeocodingError",
    "GeocodingServiceError",
    "HumidexClient",
    "HumidexError",
    "HumidexResult",
    "HumidexResultDict",
    "InvalidStepError",
    "Location",
    "PlaceNotFoundError",
    "WeatherData",
    "WeatherFetcher",
    "calculate_humidex",
    "fetch_weather_data",
    "format_human",
    "format_json",
    "geocode",
    "get_comfort_category",
    "get_humidex",
]


def get_humidex(
    place_or_location: str | Location,
    step: int = 0,
    config: Config | None = None,
    geocoder: Geocoder | None = None,
    fetcher: WeatherFetcher | None = None,
) -> HumidexResult:
    """Get humidex for a place name or coordinates.

    This is the main public API function. It:
    1. Geocodes the place name to coordinates (if string is provided)
    2. Fetches weather data from ECMWF open data
    3. Calculates the humidex value

    Args:
        place_or_location: Place name (str) or Location object with coordinates.
        step: Forecast step in hours (0 = analysis, default).
        config: Optional configuration override.
        geocoder: Optional custom geocoder (implements Geocoder protocol).
            Only used when place_or_location is a string.
        fetcher: Optional custom weather fetcher (implements WeatherFetcher protocol).

    Returns:
        HumidexResult with humidex value and comfort description.

    Raises:
        PlaceNotFoundError: If the place cannot be found.
        GeocodingServiceError: If the geocoding service is unavailable.
        InvalidStepError: If the forecast step is invalid.
        DataFetchError: If weather data cannot be fetched.
        DataParseError: If weather data cannot be parsed.
        CalculationError: If humidex cannot be calculated.

    Example:
        >>> result = get_humidex("Bangkok")
        >>> print(result)
        Bangkok: Humidex 43.9°C - Great discomfort; avoid exertion

        >>> loc = Location(name="Bangkok", latitude=13.75, longitude=100.50)
        >>> result = get_humidex(loc)
    """
    return HumidexClient(config=config, geocoder=geocoder, fetcher=fetcher).get_humidex(
        place_or_location, step=step
    )
