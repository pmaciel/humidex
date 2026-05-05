"""Tests for fetcher module."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from humidex.config import Config
from humidex.errors import DataFetchError, DataParseError, InvalidStepError
from humidex.fetcher import (
    VALID_STEPS,
    ECMWFFetcher,
    _find_nearest_index,
    _grib_tempfile_path,
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

    def test_fetch_cleans_up_tempfile(self, config: Config) -> None:
        """After a successful fetch, the temp grib file must be removed."""
        captured: dict[str, Path] = {}

        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.datetime = datetime(2026, 5, 5, 12, 0, tzinfo=timezone.utc)
        mock_client.retrieve.return_value = mock_result

        location = Location(name="Bangkok", latitude=13.7563, longitude=100.5018)
        fetcher = ECMWFFetcher(config=config)

        def _capture_parse(
            grib_path: Path, _loc: Location, _vt: datetime, _step: int
        ) -> MagicMock:
            captured["path"] = Path(grib_path)
            assert captured["path"].exists()
            return MagicMock()

        with (
            patch("humidex.fetcher.Client", return_value=mock_client),
            patch.object(fetcher, "_parse_grib", side_effect=_capture_parse),
        ):
            fetcher.fetch(location, step=0)

        assert "path" in captured
        assert not captured["path"].exists()

    def test_grib_tempfile_path_cleanup(self) -> None:
        """The context manager unlinks the file on exit."""
        with _grib_tempfile_path() as path:
            assert path.exists()
            assert path.suffix == ".grib2"
            captured = path
        assert not captured.exists()

    def test_grib_tempfile_path_cleanup_on_exception(self) -> None:
        """The context manager unlinks even when the block raises."""
        captured: Path | None = None
        with pytest.raises(RuntimeError):
            with _grib_tempfile_path() as path:
                captured = path
                raise RuntimeError("boom")
        assert captured is not None
        assert not captured.exists()

    def test_fetch_retry_on_failure(self, config: Config) -> None:
        location = Location(name="Test", latitude=0.0, longitude=0.0)
        fetcher = ECMWFFetcher(config=config)

        with (
            patch.object(fetcher, "_fetch_and_parse") as mock_fetch,
            patch("humidex.retry.time.sleep") as mock_sleep,
        ):
            mock_fetch.side_effect = Exception("Network error")

            with pytest.raises(DataFetchError, match="failed after"):
                fetcher.fetch(location, step=0)

            assert mock_fetch.call_count == config.retry_max + 1
            assert mock_sleep.call_count >= 1
            for call in mock_sleep.call_args_list:
                assert call[0][0] > 0

    def test_parse_grib_missing_valid_time_raises(self, config: Config) -> None:
        """_parse_grib must fail loudly if ECMWF returned no valid_time."""
        fetcher = ECMWFFetcher(config=config)
        location = Location(name="Bangkok", latitude=13.7563, longitude=100.5018)

        t2m_var = MagicMock()
        t2m_var.isel.return_value = MagicMock(values=np.array(298.15))
        d2m_var = MagicMock()
        d2m_var.isel.return_value = MagicMock(values=np.array(293.15))

        mock_ds = MagicMock()
        mock_ds.__enter__.return_value = mock_ds
        mock_ds.__exit__.return_value = False
        mock_ds.__getitem__.side_effect = lambda key: {
            "latitude": MagicMock(values=np.array([13.0, 14.0])),
            "longitude": MagicMock(values=np.array([100.0, 101.0])),
            "t2m": t2m_var,
            "d2m": d2m_var,
        }[key]

        with patch("humidex.fetcher.xr.open_dataset", return_value=mock_ds):
            with pytest.raises(DataParseError, match="missing valid_time"):
                fetcher._parse_grib(
                    grib_path=MagicMock(),
                    location=location,
                    valid_time=None,
                    step=0,
                )

    def test_fetch_and_parse_missing_valid_time_raises(self, config: Config) -> None:
        """_fetch_and_parse propagates DataParseError when result.datetime is None."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.datetime = None
        mock_client.retrieve.return_value = mock_result

        location = Location(name="Test", latitude=0.0, longitude=0.0)
        fetcher = ECMWFFetcher(config=config)

        with (
            patch("humidex.fetcher.Client", return_value=mock_client),
            patch.object(
                fetcher,
                "_parse_grib",
                side_effect=DataParseError("ECMWF result missing valid_time"),
            ),
            pytest.raises(DataParseError, match="missing valid_time"),
        ):
            fetcher.fetch(location, step=0)


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
