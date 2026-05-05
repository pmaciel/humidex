"""Tests for CLI module."""

import pytest
from click.testing import CliRunner

from humidex.cli import main
from humidex.models import HumidexResult, Location


class TestCLI:
    """Tests for CLI main command."""

    def test_human_output(self, hot_result: "HumidexResult") -> None:
        runner = CliRunner()
        with pytest.MonkeyPatch.context() as mp:
            import humidex.cli

            mp.setattr(humidex.cli.humidex, "get_humidex", lambda *a, **kw: hot_result)
            result = runner.invoke(main, ["Bangkok"])

        assert result.exit_code == 0
        assert "Bangkok" in result.output
        assert "40.2" in result.output
        assert "Great discomfort" in result.output

    def test_json_output(self, hot_result: "HumidexResult") -> None:
        runner = CliRunner()
        with pytest.MonkeyPatch.context() as mp:
            import humidex.cli

            mp.setattr(humidex.cli.humidex, "get_humidex", lambda *a, **kw: hot_result)
            result = runner.invoke(main, ["Bangkok", "--json"])

        assert result.exit_code == 0
        assert '"location": "Bangkok"' in result.output
        assert '"humidex": 40.2' in result.output

    def test_verbose_output(self, hot_result: "HumidexResult") -> None:
        runner = CliRunner()
        with pytest.MonkeyPatch.context() as mp:
            import humidex.cli

            mp.setattr(humidex.cli.humidex, "get_humidex", lambda *a, **kw: hot_result)
            result = runner.invoke(main, ["Bangkok", "--verbose"])

        assert result.exit_code == 0
        assert "Coordinates:" in result.output

    def test_with_step(self, hot_result: "HumidexResult") -> None:
        runner = CliRunner()
        call_args = {}

        def mock_get_humidex(
            place: object, step: int = 0, **kw: object
        ) -> HumidexResult:
            call_args["place"] = place
            call_args["step"] = step
            return hot_result

        with pytest.MonkeyPatch.context() as mp:
            import humidex.cli

            mp.setattr(humidex.cli.humidex, "get_humidex", mock_get_humidex)
            runner.invoke(main, ["Bangkok", "--step", "12"])

        assert call_args["place"] == "Bangkok"
        assert call_args["step"] == 12

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

    def test_lat_lon_input(self, hot_result: "HumidexResult") -> None:
        runner = CliRunner()
        call_args = {}

        def mock_get_humidex(
            place: object, step: int = 0, **kw: object
        ) -> HumidexResult:
            call_args["place"] = place
            return hot_result

        with pytest.MonkeyPatch.context() as mp:
            import humidex.cli

            mp.setattr(humidex.cli.humidex, "get_humidex", mock_get_humidex)
            result = runner.invoke(main, ["--lat", "13.75", "--lon", "100.50"])

        assert result.exit_code == 0
        assert isinstance(call_args["place"], Location)

    def test_missing_both_args(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [])

        assert result.exit_code == 1
        assert "Provide either PLACE or both --lat and --lon" in result.output

    def test_lat_lon_verbose(self, hot_result: "HumidexResult") -> None:
        runner = CliRunner()
        call_args = {}

        def mock_get_humidex(
            place: object, step: int = 0, **kw: object
        ) -> HumidexResult:
            call_args["place"] = place
            return hot_result

        with pytest.MonkeyPatch.context() as mp:
            import humidex.cli

            mp.setattr(humidex.cli.humidex, "get_humidex", mock_get_humidex)
            result = runner.invoke(
                main, ["--lat", "13.75", "--lon", "100.50", "-v"]
            )

        assert result.exit_code == 0
        assert "Coordinates:" in result.output
