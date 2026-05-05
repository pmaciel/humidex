"""Calculator module for humidex computation."""

from __future__ import annotations

import logging

import thermofeel

from humidex.models import HumidexResult, Location, WeatherData

logger = logging.getLogger(__name__)


COMFORT_CATEGORIES = [
    (46.0, "Dangerous; possible heat stroke"),
    (40.0, "Great discomfort; avoid exertion"),
    (30.0, "Some discomfort"),
    (20.0, "Little discomfort"),
    (float("-inf"), "Comfortable"),
]


def get_comfort_category(humidex: float) -> str:
    """Get human-readable comfort category for a humidex value.

    Args:
        humidex: Calculated humidex value in Celsius.

    Returns:
        Comfort category description.
    """
    for threshold, category in COMFORT_CATEGORIES:
        if humidex >= threshold:
            return category
    return COMFORT_CATEGORIES[-1][1]


def calculate_humidex(
    location: Location,
    weather: WeatherData,
) -> HumidexResult:
    """Calculate humidex from weather data.

    Uses ECMWF's thermofeel library to compute the humidex index
    from 2m temperature and dewpoint temperature.

    Args:
        location: Location for which to calculate humidex.
        weather: Weather data with temperature and dewpoint in Celsius.

    Returns:
        HumidexResult with humidex value and comfort category.
    """
    temp_k = weather.temperature_c + 273.15
    dew_k = weather.dewpoint_c + 273.15

    humidex_k = thermofeel.calculate_humidex(temp_k, dew_k)
    humidex_c = humidex_k - 273.15

    humidex_c = round(humidex_c, 1)
    comfort = get_comfort_category(humidex_c)

    logger.info(
        "Calculated humidex for %s: %.1f°C (%s)",
        location.name,
        humidex_c,
        comfort,
    )

    return HumidexResult(
        location=location,
        humidex=humidex_c,
        comfort=comfort,
        weather=weather,
    )
