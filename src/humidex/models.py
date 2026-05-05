"""Data models for humidex calculations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Location:
    """Represents a geographic location.

    Attributes:
        name: Human-readable place name.
        latitude: Latitude in decimal degrees (-90 to 90).
        longitude: Longitude in decimal degrees (-180 to 180).
    """

    name: str
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        """Validate coordinate ranges."""
        if not -90 <= self.latitude <= 90:
            msg = f"Latitude must be between -90 and 90, got {self.latitude}"
            raise ValueError(msg)
        if not -180 <= self.longitude <= 180:
            msg = f"Longitude must be between -180 and 180, got {self.longitude}"
            raise ValueError(msg)


@dataclass
class WeatherData:
    """Weather data at a specific location and time.

    Attributes:
        temperature_c: Air temperature at 2m in Celsius.
        dewpoint_c: Dewpoint temperature at 2m in Celsius.
        forecast_step: Forecast step in hours (0 = analysis).
        valid_time: Valid time of the forecast.
    """

    temperature_c: float
    dewpoint_c: float
    forecast_step: int
    valid_time: datetime


@dataclass
class HumidexResult:
    """Result of a humidex calculation.

    Attributes:
        location: The location for which humidex was calculated.
        humidex: Calculated humidex value.
        comfort: Human-readable comfort description.
        weather: Underlying weather data used for calculation.
    """

    location: Location
    humidex: float
    comfort: str
    weather: WeatherData

    def __str__(self) -> str:
        """Return human-readable string representation."""
        return (
            f"{self.location.name}: Humidex {self.humidex:.1f}\u00b0C - {self.comfort}"
        )
