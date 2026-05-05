"""Tests for calculator module."""

from datetime import datetime, timezone

import pytest

from humidex.calculator import calculate_humidex, get_comfort_category
from humidex.errors import CalculationError
from humidex.models import HumidexResult, Location, WeatherData


class TestGetComfortCategory:
    """Tests for comfort category classification."""

    @pytest.mark.parametrize(
        ("humidex", "expected"),
        [
            (46.0, "Dangerous; possible heat stroke"),
            (50.0, "Dangerous; possible heat stroke"),
            (100.0, "Dangerous; possible heat stroke"),
            (45.0, "Great discomfort; avoid exertion"),
            (40.0, "Great discomfort; avoid exertion"),
            (39.0, "Some discomfort"),
            (30.0, "Some discomfort"),
            (29.0, "Little discomfort"),
            (20.0, "Little discomfort"),
            (19.0, "Comfortable"),
            (0.0, "Comfortable"),
            (-10.0, "Comfortable"),
        ],
    )
    def test_boundaries(self, humidex: float, expected: str) -> None:
        assert get_comfort_category(humidex) == expected


class TestCalculateHumidex:
    """Tests for humidex calculation."""

    def test_hot_weather(self, location: Location, hot_weather: WeatherData) -> None:
        result = calculate_humidex(location, hot_weather)

        assert isinstance(result, HumidexResult)
        assert result.location == location
        assert result.weather == hot_weather
        assert result.humidex > hot_weather.temperature_c

    def test_mild_weather(self, location: Location, mild_weather: WeatherData) -> None:
        result = calculate_humidex(location, mild_weather)

        assert isinstance(result, HumidexResult)
        assert result.humidex > 0

    def test_cold_weather(self, location: Location, cold_weather: WeatherData) -> None:
        result = calculate_humidex(location, cold_weather)

        assert isinstance(result, HumidexResult)
        assert result.comfort == "Comfortable"

    def test_result_has_comfort(
        self, location: Location, hot_weather: WeatherData
    ) -> None:
        result = calculate_humidex(location, hot_weather)
        assert result.comfort in (
            "Some discomfort",
            "Great discomfort; avoid exertion",
            "Dangerous; possible heat stroke",
        )

    def test_calculation_error_extreme(self, location: Location) -> None:
        """Test that extreme but valid temperatures still calculate."""

        extreme_weather = WeatherData(
            temperature_c=-89.0,
            dewpoint_c=-90.0,
            forecast_step=0,
            valid_time=datetime.now(tz=timezone.utc),
        )
        result = calculate_humidex(location, extreme_weather)
        assert isinstance(result, HumidexResult)

    def test_calculation_error_type_error(self, location: Location) -> None:
        """Test that TypeError from thermofeel is caught and wrapped."""
        weather = WeatherData(
            temperature_c=25.0,
            dewpoint_c=15.0,
            forecast_step=0,
            valid_time=datetime.now(tz=timezone.utc),
        )
        with pytest.MonkeyPatch.context() as mp:
            import humidex.calculator

            mp.setattr(
                humidex.calculator.thermofeel,
                "celsius_to_kelvin",
                lambda _: "not a number",
            )
            with pytest.raises(CalculationError, match="invalid input"):
                calculate_humidex(location, weather)

    def test_unexpected_exception_propagates(self, location: Location) -> None:
        """Unexpected exceptions (e.g. AttributeError) must not be wrapped."""
        weather = WeatherData(
            temperature_c=25.0,
            dewpoint_c=15.0,
            forecast_step=0,
            valid_time=datetime.now(tz=timezone.utc),
        )

        def _raise_attr_error(*_args: object, **_kwargs: object) -> float:
            raise AttributeError("boom")

        with pytest.MonkeyPatch.context() as mp:
            import humidex.calculator

            mp.setattr(
                humidex.calculator.thermofeel,
                "calculate_humidex",
                _raise_attr_error,
            )
            with pytest.raises(AttributeError, match="boom"):
                calculate_humidex(location, weather)
