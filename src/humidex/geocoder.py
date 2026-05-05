"""Geocoding module to convert place names to coordinates."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

from geopy.exc import GeocoderQueryError, GeocoderRateLimited, GeocoderUnavailable
from geopy.geocoders import Nominatim

from humidex.config import Config, get_config
from humidex.errors import GeocodingServiceError, PlaceNotFoundError
from humidex.models import Location
from humidex.protocols import Geocoder

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _retry_with_backoff(
    func: Callable[[], T],
    max_retries: int,
    base_backoff: float,
) -> T:
    """Execute a function with exponential backoff retry.

    Args:
        func: Function to execute.
        max_retries: Maximum number of retries.
        base_backoff: Base backoff in seconds.

    Returns:
        Result of the function.

    Raises:
        Last exception if all retries fail.
    """
    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except (GeocoderUnavailable, GeocoderQueryError) as e:
            last_exception = e
            if attempt < max_retries:
                delay = base_backoff * (2**attempt)
                logger.warning(
                    "Geocoding attempt %d failed, retrying in %.1fs: %s",
                    attempt + 1,
                    delay,
                    e,
                )
                time.sleep(delay)
            continue
        except GeocoderRateLimited as e:
            last_exception = e
            if attempt < max_retries:
                delay = base_backoff * (2**attempt) * 2
                logger.warning(
                    "Rate limited, retrying in %.1fs: %s",
                    delay,
                    e,
                )
                time.sleep(delay)
            continue
        raise

    msg = f"Geocoding failed after {max_retries + 1} attempts"
    raise GeocodingServiceError(msg, place_name=None) from last_exception


class NominatimGeocoder(Geocoder):
    """Geocoder implementation using OpenStreetMap's Nominatim service.

    Uses a shared Nominatim instance to respect rate limits.
    Implements retry with exponential backoff for resilience.
    """

    def __init__(self, config: Config | None = None) -> None:
        """Initialize the geocoder.

        Args:
            config: Configuration. Uses default if not provided.
        """
        self._config = config or get_config()
        self._geolocator = Nominatim(
            user_agent=self._config.user_agent,
            timeout=self._config.geocoder_timeout,
        )

    def geocode(self, place_name: str) -> Location:
        """Convert a place name to a Location with coordinates.

        Args:
            place_name: Human-readable place name.

        Returns:
            Location with name, latitude, and longitude.

        Raises:
            PlaceNotFoundError: If the place cannot be found.
            GeocodingServiceError: If the service is unavailable.
        """
        logger.debug("Geocoding place: %s", place_name)

        def _do_geocode() -> Location:
            result = self._geolocator.geocode(place_name)
            if result is None:
                msg = f"Place not found: {place_name}"
                raise PlaceNotFoundError(msg, place_name=place_name)
            return Location(
                name=place_name,
                latitude=result.latitude,
                longitude=result.longitude,
            )

        location = _retry_with_backoff(
            _do_geocode,
            max_retries=self._config.retry_max,
            base_backoff=self._config.retry_backoff,
        )

        logger.info(
            "Geocoded '%s' to (%.4f, %.4f)",
            place_name,
            location.latitude,
            location.longitude,
        )
        return location


_default_geocoder: NominatimGeocoder | None = None


def get_geocoder(config: Config | None = None) -> NominatimGeocoder:
    """Get or create the default geocoder.

    Args:
        config: Optional configuration override.

    Returns:
        NominatimGeocoder instance.
    """
    global _default_geocoder
    if _default_geocoder is None or config is not None:
        _default_geocoder = NominatimGeocoder(config=config)
    return _default_geocoder


def reset_geocoder() -> None:
    """Reset the default geocoder. Useful for testing."""
    global _default_geocoder
    _default_geocoder = None


def geocode(place_name: str, config: Config | None = None) -> Location:
    """Convenience function to geocode a place name.

    Args:
        place_name: Human-readable place name.
        config: Optional configuration override.

    Returns:
        Location with coordinates.

    Raises:
        PlaceNotFoundError: If the place cannot be found.
        GeocodingServiceError: If the service is unavailable.
    """
    return get_geocoder(config).geocode(place_name)
