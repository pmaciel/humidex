"""Command-line interface for humidex."""

from __future__ import annotations

import json
import logging
import sys

import click

from humidex import get_humidex
from humidex.data_fetcher import DataFetchError
from humidex.geocoder import GeocoderError, PlaceNotFoundError


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity.

    Args:
        verbose: If True, set log level to DEBUG.
    """
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


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
    setup_logging(verbose)

    try:
        result = get_humidex(place, step=step)
    except PlaceNotFoundError:
        click.echo(f"Error: Place not found: {place}", err=True)
        sys.exit(1)
    except GeocoderError as e:
        click.echo(f"Error: Geocoding failed: {e}", err=True)
        sys.exit(1)
    except DataFetchError as e:
        click.echo(f"Error: Failed to fetch weather data: {e}", err=True)
        sys.exit(1)

    if as_json:
        output = {
            "location": result.location.name,
            "latitude": result.location.latitude,
            "longitude": result.location.longitude,
            "humidex": result.humidex,
            "comfort": result.comfort,
            "temperature_c": result.weather.temperature_c,
            "dewpoint_c": result.weather.dewpoint_c,
            "forecast_step": result.weather.forecast_step,
            "valid_time": result.weather.valid_time.isoformat(),
        }
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo(str(result))
        click.echo(f"  Temperature: {result.weather.temperature_c:.1f}°C")
        click.echo(f"  Dewpoint: {result.weather.dewpoint_c:.1f}°C")
        if verbose:
            click.echo(
                f"  Coordinates: ({result.location.latitude:.4f}, "
                f"{result.location.longitude:.4f})"
            )
            click.echo(f"  Forecast step: {result.weather.forecast_step}h")
            click.echo(f"  Valid time: {result.weather.valid_time}")


if __name__ == "__main__":
    main()
