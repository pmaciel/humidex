"""Custom exceptions for humidex."""

from __future__ import annotations


class HumidexError(Exception):
    """Base exception for all humidex errors."""


class GeocodingError(HumidexError):
    """Raised when geocoding fails."""

    def __init__(self, message: str, place_name: str | None = None) -> None:
        super().__init__(message)
        self.place_name = place_name


class PlaceNotFoundError(GeocodingError):
    """Raised when a place cannot be found."""


class GeocodingServiceError(GeocodingError):
    """Raised when the geocoding service is unavailable."""


class DataFetchError(HumidexError):
    """Raised when weather data cannot be fetched."""

    def __init__(self, message: str, location_info: str | None = None) -> None:
        super().__init__(message)
        self.location_info = location_info


class InvalidStepError(DataFetchError):
    """Raised when an invalid forecast step is requested."""


class DataParseError(DataFetchError):
    """Raised when weather data cannot be parsed."""


class CalculationError(HumidexError):
    """Raised when humidex calculation fails."""
