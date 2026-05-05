"""Command-line interface for humidex."""

from __future__ import annotations

import logging
import sys

import click

import humidex
from humidex.models import Location

_ERROR_MESSAGES: dict[type[Exception], str] = {
    humidex.PlaceNotFoundError: "Place not found: {place}",
    humidex.GeocodingError: "Geocoding failed: {error}",
    humidex.InvalidStepError: "Invalid forecast step: {error}",
    humidex.DataFetchError: "Failed to fetch weather data: {error}",
    humidex.CalculationError: "Failed to calculate humidex: {error}",
}


def _setup_logging(verbose: int) -> None:
    """Configure logging based on verbosity count.

    Args:
        verbose: Verbosity level. 0=WARNING, 1=INFO, 2+=DEBUG.
    """
    if verbose >= 2:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
        force=True,
    )


def _handle_error(error: Exception, place: str) -> None:
    """Handle known errors and exit with appropriate message.

    Args:
        error: The exception to handle.
        place: The place name that caused the error.
    """
    template = _ERROR_MESSAGES.get(type(error), "Unexpected error: {error}")
    msg = template.format(place=place, error=error)
    click.echo(f"Error: {msg}", err=True)


@click.command()
@click.argument("place", required=False, default=None)
@click.option("--lat", type=float, default=None, help="Latitude in decimal degrees.")
@click.option("--lon", type=float, default=None, help="Longitude in decimal degrees.")
@click.option(
    "--name",
    type=str,
    default=None,
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
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Enable verbose output (-v for INFO, -vv for DEBUG).",
)
def main(
    place: str | None,
    lat: float | None,
    lon: float | None,
    name: str | None,
    step: int,
    as_json: bool,
    verbose: int,
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
    # Mutually exclusive: PLACE vs --lat/--lon
    if place is not None and (lat is not None or lon is not None):
        click.echo(
            "Error: PLACE and --lat/--lon are mutually exclusive; "
            "provide either PLACE or both --lat and --lon",
            err=True,
        )
        sys.exit(1)

    # --lat and --lon must be provided together
    if (lat is None) != (lon is None):
        click.echo(
            "Error: --lat and --lon must be provided together; "
            "specify both --lat and --lon",
            err=True,
        )
        sys.exit(1)

    if place is None and lat is None and lon is None:
        click.echo("Error: Provide either PLACE or both --lat and --lon", err=True)
        sys.exit(1)

    _setup_logging(verbose)

    try:
        if lat is not None and lon is not None:
            location_name = name or f"({lat:.4f}, {lon:.4f})"
            location = Location(name=location_name, latitude=lat, longitude=lon)
            result = humidex.get_humidex(location, step=step)
        else:
            # Validation above guarantees `place` is set when lat/lon are not.
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
        click.echo(humidex.format_human(result, verbose=bool(verbose)))
