"""Tests for CLI module."""

from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from humidex.cli import main
from humidex.models import HumidexResult, Location


@pytest.fixture
def mock_get_humidex(
    monkeypatch: pytest.MonkeyPatch, hot_result: HumidexResult
) -> Iterator[MagicMock]:
    """Patch humidex.get_humidex to return hot_result and yield the mock."""
    import humidex.cli

    mock = MagicMock(return_value=hot_result)
    monkeypatch.setattr(humidex.cli.humidex, "get_humidex", mock)
    yield mock


class TestCLI:
    """Tests for CLI main command."""

    def test_human_output(self, mock_get_humidex: MagicMock) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["Bangkok"])

        assert result.exit_code == 0
        assert "Bangkok" in result.output
        assert "40.2" in result.output
        assert "Great discomfort" in result.output

    def test_json_output(self, mock_get_humidex: MagicMock) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["Bangkok", "--json"])

        assert result.exit_code == 0
        assert '"location": "Bangkok"' in result.output
        assert '"humidex": 40.2' in result.output

    def test_verbose_output(self, mock_get_humidex: MagicMock) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["Bangkok", "--verbose"])

        assert result.exit_code == 0
        assert "Coordinates:" in result.output

    def test_with_step(self, mock_get_humidex: MagicMock) -> None:
        runner = CliRunner()
        runner.invoke(main, ["Bangkok", "--step", "12"])

        mock_get_humidex.assert_called_once()
        kwargs = mock_get_humidex.call_args.kwargs
        args = mock_get_humidex.call_args.args
        # place is first positional or "place" kwarg
        place = args[0] if args else kwargs.get("place")
        assert place == "Bangkok"
        assert kwargs.get("step") == 12

    def test_place_not_found(self) -> None:
        runner = CliRunner()

        def raise_not_found(*a: object, **kw: object) -> None:
            from humidex import PlaceNotFoundError

            raise PlaceNotFoundError("Not found")

        with pytest.MonkeyPatch.context() as mp:
            import humidex.cli

            mp.setattr(humidex.cli.humidex, "get_humidex", raise_not_found)
            result = runner.invoke(main, ["NonexistentPlace123"])

        assert result.exit_code == 1
        assert "Place not found" in result.output

    def test_data_fetch_error(self) -> None:
        runner = CliRunner()

        def raise_fetch_error(*a: object, **kw: object) -> None:
            from humidex import DataFetchError

            raise DataFetchError("Network error")

        with pytest.MonkeyPatch.context() as mp:
            import humidex.cli

            mp.setattr(humidex.cli.humidex, "get_humidex", raise_fetch_error)
            result = runner.invoke(main, ["Bangkok"])

        assert result.exit_code == 1
        assert "Failed to fetch weather data" in result.output

    def test_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "humidex" in result.output.lower()
        assert "PLACE" in result.output


class TestCLICoordinates:
    """Tests for CLI coordinate input."""

    def test_lat_lon_input(self, mock_get_humidex: MagicMock) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--lat", "13.75", "--lon", "100.50"])

        assert result.exit_code == 0
        mock_get_humidex.assert_called_once()
        args = mock_get_humidex.call_args.args
        kwargs = mock_get_humidex.call_args.kwargs
        place = args[0] if args else kwargs.get("place")
        assert isinstance(place, Location)

    def test_missing_both_args(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [])

        assert result.exit_code == 1
        assert "Provide either PLACE or both --lat and --lon" in result.output

    def test_lat_without_lon(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--lat", "13.75"])

        assert result.exit_code == 1
        assert "both --lat and --lon" in result.output

    def test_lon_without_lat(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--lon", "100.50"])

        assert result.exit_code == 1
        assert "both --lat and --lon" in result.output

    def test_place_with_lat_lon_mutually_exclusive(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["Bangkok", "--lat", "13.75", "--lon", "100.50"])

        assert result.exit_code == 1
        assert "mutually exclusive" in result.output

    def test_lat_lon_verbose(self, mock_get_humidex: MagicMock) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--lat", "13.75", "--lon", "100.50", "-v"])

        assert result.exit_code == 0
        assert "Coordinates:" in result.output
