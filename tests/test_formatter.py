"""Tests for formatter module."""

import json

import pytest

from humidex.formatter import format_human, format_json
from humidex.models import HumidexResult


class TestFormatHuman:
    """Tests for human-readable formatting."""

    def test_basic(self, hot_result: "HumidexResult") -> None:
        output = format_human(hot_result)
        assert "Bangkok" in output
        assert "40.2" in output
        assert "Great discomfort" in output
        assert "Temperature: 32.0" in output
        assert "Dewpoint: 24.0" in output

    def test_verbose(self, hot_result: "HumidexResult") -> None:
        output = format_human(hot_result, verbose=True)
        assert "Coordinates:" in output
        assert "Forecast step:" in output
        assert "Valid time:" in output

    def test_not_verbose(self, hot_result: "HumidexResult") -> None:
        output = format_human(hot_result, verbose=False)
        assert "Coordinates:" not in output
        assert "Forecast step:" not in output


class TestFormatJson:
    """Tests for JSON formatting."""

    def test_valid_json(self, hot_result: "HumidexResult") -> None:
        output = format_json(hot_result)
        data = json.loads(output)
        assert data["location"] == "Bangkok"
        assert data["humidex"] == pytest.approx(40.2)
        assert data["comfort"] == "Great discomfort; avoid exertion"

    def test_all_fields(self, hot_result: "HumidexResult") -> None:
        output = format_json(hot_result)
        data = json.loads(output)
        required_fields = [
            "location",
            "latitude",
            "longitude",
            "humidex",
            "comfort",
            "temperature_c",
            "dewpoint_c",
            "forecast_step",
            "valid_time",
        ]
        for field in required_fields:
            assert field in data

    def test_indentation(self, hot_result: "HumidexResult") -> None:
        output = format_json(hot_result)
        assert "  " in output
