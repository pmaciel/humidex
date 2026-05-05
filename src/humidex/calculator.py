"""Calculator module for humidex computation."""

from __future__ import annotations

import logging

import thermofeel

from humidex.config import Config
from humidex.errors import CalculationError
from humidex.models import HumidexResult, Location, WeatherData

logger = logging.getLogger(__name__)

COMFORT_CATEGORIES: tuple[tuple[float, str], ...] = (
    (46.0, "Dangerous; possible heat stroke"),
    (40.0, "Great discomfort; avoid exertion"),
    (30.0, "Some discomfort"),
    (20.0, "Little discomfort"),
)

DEFAULT_COMFORT = "Comfortable"


def get_comfort_category(humidex: float) -> str:
    """Get human-readable comfort category for a humidex value.

    Categories based on Environment Canada standards:
    https://climate.weather.gc.ca/glossary_e.html#humidex

    Args:
        humidex: Calculated humidex value in Celsius.

    Returns:
        Comfort category description.
    """
    for threshold, category in COMFORT_CATEGORIES:
        if humidex >= threshold:
            return category
    return DEFAULT_COMFORT


def calculate_humidex(
    location: Location,
    weather: WeatherData,
    config: Config | None = None,
) -> HumidexResult:
    """Calculate humidex from weather data.

    Uses ECMWF's thermofeel library to compute the humidex index
    from 2m temperature and dewpoint temperature.

    Args:
        location: Location for which to calculate humidex.
        weather: Weather data with temperature and dewpoint in Celsius.
        config: Optional configuration override.

    Returns:
        HumidexResult with humidex value and comfort category.

    Raises:
        CalculationError: If calculation fails.
    """
    try:
        temp_k = thermofeel.celsius_to_kelvin(weather.temperature_c)
        dew_k = thermofeel.celsius_to_kelvin(weather.dewpoint_c)

        humidex_k = thermofeel.calculate_humidex(temp_k, dew_k)
        humidex_c = thermofeel.kelvin_to_celsius(humidex_k)
        humidex_c = round(float(humidex_c), 1)

    except (TypeError, ValueError) as e:
        msg = f"Failed to calculate humidex: invalid input — {e}"
        raise CalculationError(msg) from e
    except Exception as e:
        msg = f"Failed to calculate humidex: {e}"
        raise CalculationError(msg) from e

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
