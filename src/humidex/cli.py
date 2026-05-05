"""Command-line interface for humidex."""

from __future__ import annotations

import logging
import sys

import click

import humidex


def _setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity.

    Args:
        verbose: If True, set log level to DEBUG.
    """
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )


def _handle_error(error: Exception, place: str) -> None:
    """Handle known errors and exit with appropriate message.

    Args:
        error: The exception to handle.
        place: The place name that caused the error.
    """
    match error:
        case humidex.PlaceNotFoundError():
            msg = f"Place not found: {place}"
        case humidex.GeocodingError():
            msg = f"Geocoding failed: {error}"
        case humidex.InvalidStepError():
            msg = f"Invalid forecast step: {error}"
        case humidex.DataFetchError():
            msg = f"Failed to fetch weather data: {error}"
        case humidex.CalculationError():
            msg = f"Failed to calculate humidex: {error}"
        case _:
            msg = f"Unexpected error: {error}"

    click.echo(f"Error: {msg}", err=True)


@click.command()
@click.argument("place")
@click.option(
    "--step",
    "-s",
    type=int,
    default=0,
    help="Forecast step in hours (0 = analysis, default).",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Output as JSON.",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
def main(place: str, step: int, as_json: bool, verbose: bool) -> None:
    """Get the humidex for a location using ECMWF open data.

    PLACE is a human-readable location name (e.g., "Bangkok", "London, UK").

    Examples:
        humidex "Bangkok"
        humidex "London" --step 12
        humidex "Singapore" --json
    """
    _setup_logging(verbose)

    try:
        result = humidex.get_humidex(place, step=step)
    except (
        humidex.PlaceNotFoundError,
        humidex.GeocodingError,
        humidex.InvalidStepError,
        humidex.DataFetchError,
        humidex.CalculationError,
    ) as e:
        _handle_error(e, place)
        sys.exit(1)

    if as_json:
        click.echo(humidex.format_json(result))
    else:
        click.echo(humidex.format_human(result, verbose=verbose))
