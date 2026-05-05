"""Output formatting for humidex results."""

from __future__ import annotations

import json

from humidex.models import HumidexResult


def format_human(result: HumidexResult, verbose: bool = False) -> str:
    """Format a humidex result as human-readable text.

    Args:
        result: Humidex result to format.
        verbose: Include additional details like coordinates and forecast info.

    Returns:
        Formatted string.
    """
    lines = [
        f"{result.location.name}: Humidex {result.humidex:.1f}\u00b0C - "
        f"{result.comfort}",
        f"  Temperature: {result.weather.temperature_c:.1f}\u00b0C",
        f"  Dewpoint: {result.weather.dewpoint_c:.1f}\u00b0C",
    ]

    if verbose:
        lines.append(
            f"  Coordinates: ({result.location.latitude:.4f}, "
            f"{result.location.longitude:.4f})"
        )
        lines.append(f"  Forecast step: {result.weather.forecast_step}h")
        lines.append(f"  Valid time: {result.weather.valid_time}")

    return "\n".join(lines)


def format_json(result: HumidexResult) -> str:
    """Format a humidex result as JSON.

    Args:
        result: Humidex result to format.

    Returns:
        JSON string with 2-space indentation.
    """
    return json.dumps(result.to_dict(), indent=2)
