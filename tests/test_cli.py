"""Tests for CLI module."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from humidex.cli import main
from humidex.models import HumidexResult, Location, WeatherData


@pytest.fixture
def runner() -> CliRunner:
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_result() -> HumidexResult:
    """Create a mock humidex result."""
    loc = Location(name="Bangkok", latitude=13.7563, longitude=100.5018)
    weather = WeatherData(
        temperature_c=32.0,
        dewpoint_c=24.0,
        forecast_step=0,
        valid_time=datetime(2026, 5, 5, 12, 0),
    )
    return HumidexResult(
        location=loc,
        humidex=40.2,
        comfort="Great discomfort; avoid exertion",
        weather=weather,
    )


def test_cli_human_output(runner: CliRunner, mock_result: HumidexResult) -> None:
    """Test CLI human-readable output."""
    with patch("humidex.cli.get_humidex", return_value=mock_result):
        result = runner.invoke(main, ["Bangkok"])

    assert result.exit_code == 0
    assert "Bangkok" in result.output
    assert "40.2" in result.output
    assert "Great discomfort" in result.output
    assert "Temperature: 32.0" in result.output
    assert "Dewpoint: 24.0" in result.output


def test_cli_json_output(runner: CliRunner, mock_result: HumidexResult) -> None:
    """Test CLI JSON output."""
    with patch("humidex.cli.get_humidex", return_value=mock_result):
        result = runner.invoke(main, ["Bangkok", "--json"])

    assert result.exit_code == 0
    assert '"location": "Bangkok"' in result.output
    assert '"humidex": 40.2' in result.output
    assert '"comfort"' in result.output


def test_cli_verbose_output(runner: CliRunner, mock_result: HumidexResult) -> None:
    """Test CLI verbose output."""
    with patch("humidex.cli.get_humidex", return_value=mock_result):
        result = runner.invoke(main, ["Bangkok", "--verbose"])

    assert result.exit_code == 0
    assert "Coordinates:" in result.output
    assert "Forecast step:" in result.output
    assert "Valid time:" in result.output


def test_cli_with_step(runner: CliRunner, mock_result: HumidexResult) -> None:
    """Test CLI with forecast step option."""
    with patch("humidex.cli.get_humidex", return_value=mock_result) as mock_get:
        runner.invoke(main, ["Bangkok", "--step", "12"])

    mock_get.assert_called_once_with("Bangkok", step=12)


def test_cli_place_not_found(runner: CliRunner) -> None:
    """Test CLI when place is not found."""
    from humidex.geocoder import PlaceNotFoundError

    with patch("humidex.cli.get_humidex", side_effect=PlaceNotFoundError("Not found")):
        result = runner.invoke(main, ["NonexistentPlace123"])

    assert result.exit_code == 1
    assert "Place not found" in result.output


def test_cli_data_fetch_error(runner: CliRunner) -> None:
    """Test CLI when data fetch fails."""
    from humidex.data_fetcher import DataFetchError

    with patch("humidex.cli.get_humidex", side_effect=DataFetchError("Network error")):
        result = runner.invoke(main, ["Bangkok"])

    assert result.exit_code == 1
    assert "Failed to fetch weather data" in result.output


def test_cli_help(runner: CliRunner) -> None:
    """Test CLI help output."""
    result = runner.invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "humidex" in result.output.lower()
    assert "PLACE" in result.output
