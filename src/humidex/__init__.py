"""Humidex - Retrieve humidex values for any location using ECMWF open data."""

from __future__ import annotations

from humidex.calculator import calculate_humidex
from humidex.data_fetcher import fetch_weather_data
from humidex.geocoder import geocode
from humidex.models import HumidexResult, Location, WeatherData

__version__ = "0.1.0"

__all__ = [
    "HumidexResult",
    "Location",
    "WeatherData",
    "get_humidex",
]


def get_humidex(
    place_name: str,
    step: int = 0,
) -> HumidexResult:
    """Get humidex for a place name.

    This is the main public API function. It:
    1. Geocodes the place name to coordinates
    2. Fetches weather data from ECMWF open data
    3. Calculates the humidex value

    Args:
        place_name: Human-readable place name (e.g., "Bangkok", "London, UK").
        step: Forecast step in hours (0 = analysis, default).

    Returns:
        HumidexResult with humidex value and comfort description.

    Example:
        >>> result = get_humidex("Bangkok")
        >>> print(result)
        Bangkok: Humidex 40.2°C - Great discomfort; avoid exertion
    """
    location = geocode(place_name)
    weather = fetch_weather_data(location, step=step)
    return calculate_humidex(location, weather)
