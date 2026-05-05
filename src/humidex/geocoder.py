"""Geocoding module to convert place names to coordinates."""

from __future__ import annotations

import logging

from geopy.exc import GeocoderUnavailable
from geopy.geocoders import Nominatim

from humidex.models import Location

logger = logging.getLogger(__name__)

_USER_AGENT = "humidex-cli/0.1.0"


class GeocoderError(Exception):
    """Base exception for geocoding errors."""


class PlaceNotFoundError(GeocoderError):
    """Raised when a place cannot be found."""


def geocode(place_name: str, timeout: int = 10) -> Location:
    """Convert a place name to a Location with coordinates.

    Uses OpenStreetMap's Nominatim service (free, no API key required).

    Args:
        place_name: Human-readable place name (e.g., "Bangkok", "London, UK").
        timeout: Request timeout in seconds.

    Returns:
        Location with name, latitude, and longitude.

    Raises:
        PlaceNotFoundError: If the place cannot be found.
        GeocoderError: If the geocoding service is unavailable.
    """
    logger.debug("Geocoding place: %s", place_name)

    geolocator = Nominatim(user_agent=_USER_AGENT, timeout=timeout)

    try:
        location = geolocator.geocode(place_name)
    except GeocoderUnavailable as e:
        msg = f"Geocoding service unavailable: {e}"
        logger.error(msg)
        raise GeocoderError(msg) from e

    if location is None:
        msg = f"Place not found: {place_name}"
        logger.warning(msg)
        raise PlaceNotFoundError(msg)

    result = Location(
        name=place_name,
        latitude=location.latitude,
        longitude=location.longitude,
    )

    logger.info(
        "Geocoded '%s' to (%.4f, %.4f)",
        place_name,
        result.latitude,
        result.longitude,
    )

    return result
