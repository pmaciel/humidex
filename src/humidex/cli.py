"""Command-line interface for humidex."""

from __future__ import annotations

import logging
import sys

import click

import humidex
from humidex.models import Location


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
@click.argument("place", required=False, default=None)
@click.option("--lat", type=float, default=None, help="Latitude in decimal degrees.")
@click.option("--lon", type=float, default=None, help="Longitude in decimal degrees.")
@click.option(
    "--name", type=str, default=None,
    help="Location name (used with --lat/--lon).",
)
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
def main(
    place: str | None,
    lat: float | None,
    lon: float | None,
    name: str | None,
    step: int,
    as_json: bool,
    verbose: bool,
) -> None:
    """Get the humidex for a location using ECMWF open data.

    Provide either PLACE (a human-readable location name) or both
    --lat and --lon (decimal degrees).

    Examples:
        humidex "Bangkok"
        humidex --lat 13.75 --lon 100.50 --name "Bangkok"
        humidex "London" --step 12
        humidex "Singapore" --json
    """
    if place is None and (lat is None or lon is None):
        click.echo("Error: Provide either PLACE or both --lat and --lon", err=True)
        sys.exit(1)

    _setup_logging(verbose)

    try:
        if lat is not None and lon is not None:
            location_name = name or f"({lat:.4f}, {lon:.4f})"
            location = Location(name=location_name, latitude=lat, longitude=lon)
            result = humidex.get_humidex(location, step=step)
        else:
            assert place is not None
            result = humidex.get_humidex(place, step=step)
    except (
        humidex.PlaceNotFoundError,
        humidex.GeocodingError,
        humidex.InvalidStepError,
        humidex.DataFetchError,
        humidex.CalculationError,
    ) as e:
        _handle_error(e, place or f"({lat}, {lon})")
        sys.exit(1)

    if as_json:
        click.echo(humidex.format_json(result))
    else:
        click.echo(humidex.format_human(result, verbose=verbose))
