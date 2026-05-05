"""Data fetcher module to retrieve weather data from ECMWF open data."""

from __future__ import annotations

import contextlib
import logging
import math
import os
import tempfile
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

import numpy as np
import xarray as xr
from ecmwf.opendata import Client

from humidex.config import Config, get_config
from humidex.errors import DataFetchError, DataParseError, InvalidStepError
from humidex.models import Location, WeatherData
from humidex.protocols import WeatherFetcher
from humidex.retry import retry_with_backoff

logger = logging.getLogger(__name__)

ECMWF_PARAMS: tuple[str, str] = ("2t", "2d")
VALID_STEPS: frozenset[int] = frozenset(
    list(range(0, 144, 3)) + list(range(144, 241, 6))
)

ECMWF_TEMP_VAR = "t2m"
ECMWF_DEW_VAR = "d2m"


def _validate_step(step: int) -> None:
    """Validate forecast step is within valid range.

    Args:
        step: Forecast step in hours.

    Raises:
        InvalidStepError: If step is not valid.
    """
    if step not in VALID_STEPS:
        valid_examples = "0, 3, 6, ..., 141, 144, 150, ..., 240"
        msg = (
            f"Invalid forecast step: {step}. "
            f"Valid steps: 0-144 by 3, 144-240 by 6 (e.g., {valid_examples})"
        )
        raise InvalidStepError(msg)


def _find_nearest_index(array: np.ndarray, value: float) -> int:
    """Find index of the nearest value in an array.

    Args:
        array: Array of coordinate values.
        value: Target value to find nearest to.

    Returns:
        Index of the nearest value.
    """
    return int(np.abs(array - value).argmin())


@contextlib.contextmanager
def _grib_tempfile_path() -> Iterator[Path]:
    """Yield a path to a temporary GRIB2 file, cleaning up on exit.

    Closes the file descriptor returned by :func:`tempfile.mkstemp`
    immediately so it does not leak, and unlinks the file on exit.

    Yields:
        Path to a freshly created temporary ``.grib2`` file.
    """
    fd, target_path = tempfile.mkstemp(suffix=".grib2")
    os.close(fd)
    path = Path(target_path)
    try:
        yield path
    finally:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def _validate_temperature(value: float, config: Config) -> None:
    """Validate that a temperature value is within reasonable bounds.

    Args:
        value: Temperature in Celsius.
        config: Configuration with min/max bounds.

    Raises:
        DataParseError: If value is out of range or invalid.
    """
    if math.isnan(value) or math.isinf(value):
        msg = f"Invalid temperature value: {value} (NaN or Inf)"
        raise DataParseError(msg)
    if not config.temp_min_c <= value <= config.temp_max_c:
        msg = (
            f"Temperature {value}°C outside valid range "
            f"[{config.temp_min_c}, {config.temp_max_c}]"
        )
        raise DataParseError(msg)


class ECMWFFetcher(WeatherFetcher):
    """Weather fetcher using ECMWF open data.

    Downloads GRIB2 files and extracts values at the nearest grid point.
    Implements retry with exponential backoff for resilience.
    """

    def __init__(self, config: Config | None = None) -> None:
        """Initialize the fetcher.

        Args:
            config: Configuration. Uses default if not provided.
        """
        self._config = config or get_config()

    def fetch(self, location: Location, step: int = 0) -> WeatherData:
        """Fetch weather data from ECMWF open data.

        Args:
            location: Location to fetch data for.
            step: Forecast step in hours (0 = analysis).

        Returns:
            WeatherData with temperature and dewpoint in Celsius.

        Raises:
            InvalidStepError: If step is not valid.
            DataFetchError: If data cannot be fetched.
            DataParseError: If data cannot be parsed or is invalid.
        """
        _validate_step(step)

        logger.info(
            "Fetching ECMWF data for %s at step %d",
            location,
            step,
        )

        def _do_fetch() -> WeatherData:
            return self._fetch_and_parse(location, step)

        try:
            return retry_with_backoff(
                _do_fetch,
                max_retries=self._config.retry_max,
                base_backoff=self._config.retry_backoff,
            )
        except (InvalidStepError, DataParseError):
            raise
        except Exception as e:
            msg = f"Data fetch failed after {self._config.retry_max + 1} attempts"
            raise DataFetchError(msg) from e

    def _fetch_and_parse(self, location: Location, step: int) -> WeatherData:
        """Fetch GRIB data and parse at location.

        Args:
            location: Target location.
            step: Forecast step.

        Returns:
            Parsed WeatherData.
        """
        client = Client(source=self._config.ecmwf_source)

        with _grib_tempfile_path() as target_path:
            result = client.retrieve(
                step=step,
                type="fc",
                param=list(ECMWF_PARAMS),
                target=str(target_path),
            )

            logger.debug("Downloaded GRIB file: %s", target_path)

            return self._parse_grib(target_path, location, result.datetime, step)

    def _parse_grib(
        self,
        grib_path: Path,
        location: Location,
        valid_time: datetime | None,
        step: int,
    ) -> WeatherData:
        """Parse GRIB file and extract values at nearest grid point.

        Args:
            grib_path: Path to GRIB2 file.
            location: Target location.
            valid_time: Valid time of the forecast.
            step: Forecast step.

        Returns:
            WeatherData with extracted values.

        Raises:
            DataParseError: If GRIB file cannot be parsed.
        """
        try:
            with xr.open_dataset(str(grib_path), engine="cfgrib") as ds:
                lat_values = ds["latitude"].values
                lon_values = ds["longitude"].values

                lat_idx = _find_nearest_index(lat_values, location.latitude)
                lon_idx = _find_nearest_index(lon_values, location.longitude)

                temp_k = float(
                    ds[ECMWF_TEMP_VAR].isel(latitude=lat_idx, longitude=lon_idx).values
                )
                dew_k = float(
                    ds[ECMWF_DEW_VAR].isel(latitude=lat_idx, longitude=lon_idx).values
                )

        except DataParseError:
            raise
        except (KeyError, ValueError, OSError, RuntimeError) as e:
            # xarray/cfgrib raise these on malformed GRIB data
            msg = f"Failed to parse GRIB file: {e}"
            raise DataParseError(msg) from e

        temp_c = temp_k - 273.15
        dew_c = dew_k - 273.15

        _validate_temperature(temp_c, self._config)
        _validate_temperature(dew_c, self._config)

        logger.debug(
            "Extracted values: temp=%.1f°C, dew=%.1f°C",
            temp_c,
            dew_c,
        )

        if not isinstance(valid_time, datetime):
            msg = "ECMWF result missing valid_time"
            raise DataParseError(msg)

        return WeatherData(
            temperature_c=round(temp_c, 1),
            dewpoint_c=round(dew_c, 1),
            forecast_step=step,
            valid_time=valid_time,
        )


def fetch_weather_data(
    location: Location,
    step: int = 0,
    config: Config | None = None,
) -> WeatherData:
    """Convenience function to fetch weather data.

    Args:
        location: Location to fetch data for.
        step: Forecast step in hours (0 = analysis).
        config: Optional configuration override.

    Returns:
        WeatherData with temperature and dewpoint.

    Raises:
        InvalidStepError: If step is not valid.
        DataFetchError: If data cannot be fetched.
    """
    return ECMWFFetcher(config=config).fetch(location, step=step)
