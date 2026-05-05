"""Data models for humidex calculations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict


class HumidexResultDict(TypedDict):
    """TypedDict for humidex result JSON serialization."""

    location: str
    latitude: float
    longitude: float
    humidex: float
    comfort: str
    temperature_c: float
    dewpoint_c: float
    forecast_step: int
    valid_time: str


@dataclass(frozen=True)
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

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.name} ({self.latitude:.4f}, {self.longitude:.4f})"


@dataclass(frozen=True)
class WeatherData:
    """Weather data at a specific location and time.

    Attributes:
        temperature_c: Air temperature at 2m in Celsius.
        dewpoint_c: Dewpoint temperature at 2m in Celsius.
        forecast_step: Forecast step in hours (0 = analysis).
        valid_time: Valid time of the forecast (UTC).
    """

    temperature_c: float
    dewpoint_c: float
    forecast_step: int
    valid_time: datetime

    def __post_init__(self) -> None:
        """Validate weather data ranges."""
        if not -90 <= self.temperature_c <= 60:
            msg = (
                f"Temperature out of range: {self.temperature_c}°C "
                f"(valid: -90 to 60)"
            )
            raise ValueError(msg)
        if not -90 <= self.dewpoint_c <= 60:
            msg = (
                f"Dewpoint out of range: {self.dewpoint_c}°C "
                f"(valid: -90 to 60)"
            )
            raise ValueError(msg)
        if self.forecast_step < 0:
            msg = f"Forecast step must be non-negative, got {self.forecast_step}"
            raise ValueError(msg)


@dataclass(frozen=True)
class HumidexResult:
    """Result of a humidex calculation.

    Attributes:
        location: The location for which humidex was calculated.
        humidex: Calculated humidex value in Celsius.
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

    def to_dict(self) -> HumidexResultDict:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary with all result fields.
        """
        return {
            "location": self.location.name,
            "latitude": self.location.latitude,
            "longitude": self.location.longitude,
            "humidex": self.humidex,
            "comfort": self.comfort,
            "temperature_c": self.weather.temperature_c,
            "dewpoint_c": self.weather.dewpoint_c,
            "forecast_step": self.weather.forecast_step,
            "valid_time": self.weather.valid_time.isoformat(),
        }
