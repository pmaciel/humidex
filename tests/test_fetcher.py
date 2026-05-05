"""Tests for fetcher module."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from humidex.config import Config
from humidex.errors import DataFetchError, DataParseError, InvalidStepError
from humidex.fetcher import (
    VALID_STEPS,
    ECMWFFetcher,
    _find_nearest_index,
    _validate_step,
    _validate_temperature,
    fetch_weather_data,
)
from humidex.models import Location


class TestValidateStep:
    """Tests for forecast step validation."""

    def test_valid_steps(self) -> None:
        for step in (0, 3, 6, 141, 144, 150, 240):
            _validate_step(step)

    def test_invalid_steps(self) -> None:
        for step in (-1, 1, 2, 5, 143, 241, 300):
            with pytest.raises(InvalidStepError):
                _validate_step(step)

    def test_overlap_removed(self) -> None:
        assert 144 in VALID_STEPS
        steps_list = sorted(VALID_STEPS)
        assert steps_list == sorted(set(steps_list))


class TestFindNearestIndex:
    """Tests for _find_nearest_index utility."""

    def test_basic(self) -> None:
        arr = np.array([10.0, 20.0, 30.0, 40.0])
        assert _find_nearest_index(arr, 22.0) == 1
        assert _find_nearest_index(arr, 28.0) == 2

    def test_exact_match(self) -> None:
        arr = np.array([10.0, 20.0, 30.0])
        assert _find_nearest_index(arr, 20.0) == 1

    def test_boundary(self) -> None:
        arr = np.array([10.0, 20.0, 30.0])
        assert _find_nearest_index(arr, 5.0) == 0
        assert _find_nearest_index(arr, 35.0) == 2


class TestValidateTemperature:
    """Tests for temperature validation."""

    def test_valid(self, config: Config) -> None:
        _validate_temperature(25.0, config)
        _validate_temperature(-90.0, config)
        _validate_temperature(60.0, config)

    def test_nan(self, config: Config) -> None:
        with pytest.raises(DataParseError, match="NaN"):
            _validate_temperature(float("nan"), config)

    def test_inf(self, config: Config) -> None:
        with pytest.raises(DataParseError, match="Inf"):
            _validate_temperature(float("inf"), config)

    def test_out_of_range(self, config: Config) -> None:
        with pytest.raises(DataParseError, match="outside valid range"):
            _validate_temperature(65.0, config)


class TestECMWFFetcher:
    """Tests for ECMWFFetcher."""

    def test_fetch_invalid_step(self, config: Config) -> None:
        fetcher = ECMWFFetcher(config=config)
        location = Location(name="Test", latitude=0.0, longitude=0.0)
        with pytest.raises(InvalidStepError):
            fetcher.fetch(location, step=5)

    def test_fetch_success(self, config: Config) -> None:
        mock_client = MagicMock()
        mock_result = MagicMock()
        from datetime import datetime, timezone

        mock_result.datetime = datetime(2026, 5, 5, 12, 0, tzinfo=timezone.utc)
        mock_client.retrieve.return_value = mock_result

        location = Location(name="Bangkok", latitude=13.7563, longitude=100.5018)
        fetcher = ECMWFFetcher(config=config)

        with (
            patch("humidex.fetcher.Client", return_value=mock_client),
            patch.object(fetcher, "_parse_grib") as mock_parse,
        ):
            expected = MagicMock()
            mock_parse.return_value = expected

            result = fetcher.fetch(location, step=0)

            assert result == expected
            mock_client.retrieve.assert_called_once()
            call_kwargs = mock_client.retrieve.call_args[1]
            assert call_kwargs["param"] == ["2t", "2d"]

    def test_fetch_retry_on_failure(self, config: Config) -> None:
        location = Location(name="Test", latitude=0.0, longitude=0.0)
        fetcher = ECMWFFetcher(config=config)

        with patch.object(fetcher, "_fetch_and_parse") as mock_fetch:
            mock_fetch.side_effect = Exception("Network error")

            with pytest.raises(DataFetchError, match="failed after"):
                fetcher.fetch(location, step=0)

            assert mock_fetch.call_count == config.retry_max + 1


class TestFetchWeatherDataConvenience:
    """Tests for fetch_weather_data convenience function."""

    def test_calls_fetcher(self, config: Config) -> None:
        location = Location(name="Test", latitude=0.0, longitude=0.0)
        mock_fetcher = MagicMock()
        expected = MagicMock()
        mock_fetcher.fetch.return_value = expected

        with patch("humidex.fetcher.ECMWFFetcher", return_value=mock_fetcher):
            result = fetch_weather_data(location, step=12, config=config)

        assert result == expected
        mock_fetcher.fetch.assert_called_once_with(location, step=12)
