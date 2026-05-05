"""Tests for data fetcher module."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from humidex.data_fetcher import DataFetchError, _find_nearest, fetch_weather_data
from humidex.models import Location


@pytest.fixture
def location() -> Location:
    """Create a test location."""
    return Location(name="Bangkok", latitude=13.7563, longitude=100.5018)


def test_find_nearest() -> None:
    """Test finding nearest value in array."""
    arr = np.array([10.0, 20.0, 30.0, 40.0])
    assert _find_nearest(arr, 22.0) == 1
    assert _find_nearest(arr, 28.0) == 2
    assert _find_nearest(arr, 10.0) == 0
    assert _find_nearest(arr, 40.0) == 3


def test_fetch_invalid_step(location: Location) -> None:
    """Test that invalid forecast step raises error."""
    with pytest.raises(DataFetchError, match="Invalid forecast step"):
        fetch_weather_data(location, step=5)


def test_fetch_weather_data_mocked(location: Location) -> None:
    """Test fetching weather data with mocked ECMWF client."""
    mock_client = MagicMock()
    mock_result = MagicMock()
    mock_result.datetime = datetime(2026, 5, 5, 12, 0)
    mock_client.retrieve.return_value = mock_result

    with (
        patch("ecmwf.opendata.Client", return_value=mock_client),
        patch("humidex.data_fetcher._read_grib_at_location") as mock_read,
        patch("humidex.data_fetcher.os.path.exists", return_value=True),
        patch("humidex.data_fetcher.os.unlink"),
    ):
        expected_weather = MagicMock()
        mock_read.return_value = expected_weather

        result = fetch_weather_data(location, step=0)

        assert result == expected_weather
        mock_client.retrieve.assert_called_once()
        call_kwargs = mock_client.retrieve.call_args[1]
        assert call_kwargs["param"] == ["2t", "2d"]
        assert call_kwargs["step"] == 0


def test_fetch_data_ecmwf_error(location: Location) -> None:
    """Test handling of ECMWF fetch errors."""
    with (
        patch("ecmwf.opendata.Client") as mock_client,
        patch("humidex.data_fetcher.os.path.exists", return_value=False),
    ):
        mock_client.return_value.retrieve.side_effect = Exception("Network error")

        with pytest.raises(DataFetchError, match="Failed to fetch"):
            fetch_weather_data(location, step=0)
