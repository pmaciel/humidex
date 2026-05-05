"""Geocoding module to convert place names to coordinates."""

from __future__ import annotations

import logging

from geopy.exc import GeocoderRateLimited
from geopy.geocoders import Nominatim

from humidex.config import Config, get_config
from humidex.errors import GeocodingServiceError, PlaceNotFoundError
from humidex.models import Location
from humidex.protocols import Geocoder
from humidex.retry import retry_with_backoff

logger = logging.getLogger(__name__)


def _is_rate_limited(exc: Exception) -> bool:
    return isinstance(exc, GeocoderRateLimited)


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

        try:
            location = retry_with_backoff(
                _do_geocode,
                max_retries=self._config.retry_max,
                base_backoff=self._config.retry_backoff,
                rate_limit_multiplier=2.0,
                is_rate_limited=_is_rate_limited,
                no_retry=(PlaceNotFoundError,),
            )
        except PlaceNotFoundError:
            raise
        except Exception as e:
            msg = f"Geocoding failed after {self._config.retry_max + 1} attempts"
            raise GeocodingServiceError(msg, place_name=place_name) from e

        logger.info(
            "Geocoded '%s' to (%.4f, %.4f)",
            place_name,
            location.latitude,
            location.longitude,
        )
        return location


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
    return NominatimGeocoder(config=config).geocode(place_name)
