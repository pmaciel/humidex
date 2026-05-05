"""Data fetcher module to retrieve weather data from ECMWF open data."""

from __future__ import annotations

import logging
import os
import tempfile
from datetime import datetime

import numpy as np
import xarray as xr

from humidex.models import Location, WeatherData

logger = logging.getLogger(__name__)

ECMWF_PARAMS = ["2t", "2d"]
VALID_STEPS = list(range(0, 145, 3)) + list(range(144, 241, 6))


class DataFetchError(Exception):
    """Raised when data cannot be fetched from ECMWF."""


def fetch_weather_data(
    location: Location,
    step: int = 0,
) -> WeatherData:
    """Fetch weather data from ECMWF open data for a location.

    Downloads 2m temperature and 2m dewpoint temperature from ECMWF
    open data and extracts values at the nearest grid point.

    Args:
        location: Location to fetch data for.
        step: Forecast step in hours (0 = analysis, 3-144 by 3, 144-240 by 6).

    Returns:
        WeatherData with temperature and dewpoint in Celsius.

    Raises:
        DataFetchError: If data cannot be fetched or parsed.
    """
    if step not in VALID_STEPS:
        msg = (
            f"Invalid forecast step: {step}. "
            f"Valid steps: 0-144 by 3, 144-240 by 6"
        )
        raise DataFetchError(msg)

    logger.info(
        "Fetching ECMWF data for (%.4f, %.4f) at step %d",
        location.latitude,
        location.longitude,
        step,
    )

    try:
        return _fetch_from_ecmwf(location, step)
    except Exception as e:
        msg = f"Failed to fetch weather data: {e}"
        logger.error(msg)
        raise DataFetchError(msg) from e


def _fetch_from_ecmwf(location: Location, step: int) -> WeatherData:
    """Internal function to fetch data from ECMWF.

    Args:
        location: Location to fetch data for.
        step: Forecast step in hours.

    Returns:
        WeatherData with temperature and dewpoint.
    """
    from ecmwf.opendata import Client

    client = Client(source="aws")

    with tempfile.NamedTemporaryFile(suffix=".grib2", delete=False) as tmp:
        target = tmp.name

    try:
        result = client.retrieve(
            step=step,
            type="fc",
            param=ECMWF_PARAMS,
            target=target,
        )

        valid_time = result.datetime

        logger.debug("Downloaded GRIB file to %s", target)

        weather_data = _read_grib_at_location(target, location, valid_time, step)
        return weather_data
    finally:
        if os.path.exists(target):
            os.unlink(target)


def _read_grib_at_location(
    grib_path: str,
    location: Location,
    valid_time: datetime,
    step: int,
) -> WeatherData:
    """Read GRIB file and extract values at nearest grid point.

    Args:
        grib_path: Path to GRIB2 file.
        location: Target location.
        valid_time: Valid time of the forecast.
        step: Forecast step.

    Returns:
        WeatherData with extracted values.
    """
    ds = xr.open_dataset(grib_path, engine="cfgrib")

    lat = ds["latitude"].values
    lon = ds["longitude"].values

    lat_idx = _find_nearest(lat, location.latitude)
    lon_idx = _find_nearest(lon, location.longitude)

    temp_k = float(ds["t2m"].values[lat_idx, lon_idx])
    dew_k = float(ds["d2m"].values[lat_idx, lon_idx])

    temp_c = temp_k - 273.15
    dew_c = dew_k - 273.15

    logger.debug(
        "Extracted values: temp=%.1f°C, dew=%.1f°C",
        temp_c,
        dew_c,
    )

    return WeatherData(
        temperature_c=round(temp_c, 1),
        dewpoint_c=round(dew_c, 1),
        forecast_step=step,
        valid_time=valid_time,
    )


def _find_nearest(array: np.ndarray, value: float) -> int:
    """Find index of nearest value in array.

    Args:
        array: Array of values.
        value: Target value.

    Returns:
        Index of nearest value.
    """
    return int(np.abs(array - value).argmin())
