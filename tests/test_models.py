"""Tests for data models."""

from datetime import datetime, timezone

import pytest

from humidex.models import HumidexResult, HumidexResultDict, Location, WeatherData


class TestLocation:
    """Tests for Location model."""

    def test_create_valid(self) -> None:
        loc = Location(name="Bangkok", latitude=13.7563, longitude=100.5018)
        assert loc.name == "Bangkok"
        assert loc.latitude == pytest.approx(13.7563)
        assert loc.longitude == pytest.approx(100.5018)

    def test_boundary_values(self) -> None:
        Location(name="Equator", latitude=0.0, longitude=0.0)
        Location(name="North Pole", latitude=90.0, longitude=0.0)
        Location(name="South Pole", latitude=-90.0, longitude=0.0)
        Location(name="Date Line", latitude=0.0, longitude=180.0)
        Location(name="Anti Date Line", latitude=0.0, longitude=-180.0)

    @pytest.mark.parametrize(
        ("latitude", "longitude"),
        [
            (91.0, 0.0),
            (-91.0, 0.0),
            (0.0, 181.0),
            (0.0, -181.0),
        ],
    )
    def test_invalid_coordinates(self, latitude: float, longitude: float) -> None:
        with pytest.raises(ValueError):
            Location(name="Invalid", latitude=latitude, longitude=longitude)

    def test_frozen(self) -> None:
        loc = Location(name="Test", latitude=0.0, longitude=0.0)
        with pytest.raises(Exception):
            loc.name = "Changed"

    def test_str(self) -> None:
        loc = Location(name="Bangkok", latitude=13.7563, longitude=100.5018)
        assert "Bangkok" in str(loc)
        assert "13.7563" in str(loc)
        assert "100.5018" in str(loc)


class TestWeatherData:
    """Tests for WeatherData model."""

    def test_create_valid(self) -> None:
        weather = WeatherData(
            temperature_c=32.0,
            dewpoint_c=24.0,
            forecast_step=0,
            valid_time=datetime(2026, 5, 5, 12, 0, tzinfo=timezone.utc),
        )
        assert weather.temperature_c == pytest.approx(32.0)
        assert weather.dewpoint_c == pytest.approx(24.0)

    def test_boundary_temperatures(self) -> None:
        WeatherData(
            temperature_c=-90.0,
            dewpoint_c=-90.0,
            forecast_step=0,
            valid_time=datetime.now(tz=timezone.utc),
        )
        WeatherData(
            temperature_c=60.0,
            dewpoint_c=60.0,
            forecast_step=0,
            valid_time=datetime.now(tz=timezone.utc),
        )

    @pytest.mark.parametrize(
        ("temperature_c", "dewpoint_c"),
        [
            (61.0, 20.0),
            (-91.0, 20.0),
            (20.0, 61.0),
            (20.0, -91.0),
        ],
    )
    def test_invalid_temperature(
        self, temperature_c: float, dewpoint_c: float
    ) -> None:
        with pytest.raises(ValueError, match="range"):
            WeatherData(
                temperature_c=temperature_c,
                dewpoint_c=dewpoint_c,
                forecast_step=0,
                valid_time=datetime.now(tz=timezone.utc),
            )

    def test_invalid_forecast_step(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            WeatherData(
                temperature_c=20.0,
                dewpoint_c=10.0,
                forecast_step=-1,
                valid_time=datetime.now(tz=timezone.utc),
            )

    def test_frozen(self) -> None:
        weather = WeatherData(
            temperature_c=20.0,
            dewpoint_c=10.0,
            forecast_step=0,
            valid_time=datetime.now(tz=timezone.utc),
        )
        with pytest.raises(Exception):
            weather.temperature_c = 25.0

    def test_naive_timezone_rejected(self) -> None:
        with pytest.raises(ValueError, match="timezone-aware"):
            WeatherData(
                temperature_c=20.0,
                dewpoint_c=10.0,
                forecast_step=0,
                valid_time=datetime(2026, 5, 5, 12, 0),
            )


class TestHumidexResult:
    """Tests for HumidexResult model."""

    def test_str(self, hot_result: HumidexResult) -> None:
        result_str = str(hot_result)
        assert "Bangkok" in result_str
        assert "40.2" in result_str
        assert "Great discomfort" in result_str

    def test_to_dict(self, hot_result: HumidexResult) -> None:
        d = hot_result.to_dict()
        assert d["location"] == "Bangkok"
        assert d["latitude"] == pytest.approx(13.7563)
        assert d["longitude"] == pytest.approx(100.5018)
        assert d["humidex"] == pytest.approx(40.2)
        assert "comfort" in d
        assert "temperature_c" in d
        assert "dewpoint_c" in d
        assert "forecast_step" in d
        assert "valid_time" in d

    def test_to_dict_typed(self, hot_result: HumidexResult) -> None:
        d: HumidexResultDict = hot_result.to_dict()
        assert isinstance(d, dict)
        assert isinstance(d["location"], str)
        assert isinstance(d["latitude"], float)
        assert isinstance(d["humidex"], float)
        assert isinstance(d["comfort"], str)

    def test_frozen(self, hot_result: HumidexResult) -> None:
        with pytest.raises(Exception):
            hot_result.humidex = 35.0
