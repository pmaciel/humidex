"""Humidex - Retrieve humidex values for any location using ECMWF open data.

Public API:
    get_humidex: Main function to get humidex for a place name.
    HumidexResult, Location, WeatherData: Data models.
    Config: Configuration with environment variable support.
    get_config, set_config: Configuration management.
"""

from __future__ import annotations

from humidex.calculator import calculate_humidex, get_comfort_category
from humidex.config import Config, get_config, set_config
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
from humidex.models import HumidexResult, Location, WeatherData
from humidex.protocols import Geocoder, WeatherFetcher

__version__ = "2.0.0"

__all__ = [
    "CalculationError",
    "Config",
    "DataFetchError",
    "DataParseError",
    "Geocoder",
    "GeocodingError",
    "GeocodingServiceError",
    "HumidexError",
    "HumidexResult",
    "InvalidStepError",
    "Location",
    "PlaceNotFoundError",
    "WeatherData",
    "WeatherFetcher",
    "format_human",
    "format_json",
    "get_comfort_category",
    "get_config",
    "get_humidex",
    "set_config",
]


def get_humidex(
    place_name: str,
    step: int = 0,
    config: Config | None = None,
    geocoder: Geocoder | None = None,
    fetcher: WeatherFetcher | None = None,
) -> HumidexResult:
    """Get humidex for a place name.

    This is the main public API function. It:
    1. Geocodes the place name to coordinates
    2. Fetches weather data from ECMWF open data
    3. Calculates the humidex value

    Args:
        place_name: Human-readable place name (e.g., "Bangkok", "London, UK").
        step: Forecast step in hours (0 = analysis, default).
        config: Optional configuration override.
        geocoder: Optional custom geocoder (implements Geocoder protocol).
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
    """
    if geocoder is not None:
        location = geocoder.geocode(place_name)
    else:
        location = geocode(place_name, config=config)

    if fetcher is not None:
        weather = fetcher.fetch(location, step=step)
    else:
        weather = fetch_weather_data(location, step=step, config=config)

    return calculate_humidex(location, weather, config=config)
