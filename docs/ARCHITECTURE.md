# Architecture: Humidex CLI

## Overview

A Python module and CLI tool that retrieves the humidex (perceived temperature in hot, humid weather) for a given location using ECMWF open data. Users provide a place name (e.g., "Bangkok", "London") and receive a human-readable humidex value with comfort description.

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        CLI (click)                      │
│              humidex "Bangkok" [--step 0]               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   humidex package                       │
├─────────────────┬──────────────────┬────────────────────┤
│   geocoder.py   │  data_fetcher.py │  calculator.py     │
│                 │                  │                    │
│ Place name →    │ Coordinates →    │ Temp + Dewpoint →  │
│ Coordinates     │ GRIB data        │ Humidex value      │
│ (geopy/Nominatim│ (ecmwf-opendata) │ (thermofeel)       │
└─────────────────┴──────────────────┴────────────────────┘
```

## Components

### 1. Geocoder (`src/humidex/geocoder.py`)

Converts human-readable place names to latitude/longitude coordinates.

- Uses `geopy` with `Nominatim` backend (free, no API key required)
- Returns `(lat, lon)` tuple
- Handles ambiguous places by selecting first result or prompting

### 2. Data Fetcher (`src/humidex/data_fetcher.py`)

Retrieves weather data from ECMWF open data.

- Uses `ecmwf-opendata` Python client
- Fetches `2t` (2m temperature, K) and `2d` (2m dewpoint temperature, K)
- Supports forecast step selection (0 = analysis, 3-144 = forecast hours)
- Downloads GRIB2 files and reads with `xarray` + `cfgrib` engine
- Extracts values at nearest grid point to given coordinates

### 3. Calculator (`src/humidex/calculator.py`)

Computes humidex from temperature and dewpoint.

- Uses ECMWF's `thermofeel` library for calculation
- Converts Kelvin to Celsius before calculation
- Returns humidex value and comfort category:
  - `< 20`: Comfortable
  - `20-29`: Little discomfort
  - `30-39`: Some discomfort
  - `40-45`: Great discomfort; avoid exertion
  - `≥ 46`: Dangerous; possible heat stroke

### 4. CLI (`src/humidex/cli.py`)

Command-line interface using `click`.

- Accepts place name as positional argument
- Optional: `--step` for forecast hour (default: 0)
- Optional: `--json` for machine-readable output
- Outputs human-readable result by default

## Data Flow

```
User input: "Bangkok"
    │
    ▼
Geocoder: geopy.Nominatim → (13.7563, 100.5018)
    │
    ▼
Data Fetcher: ecmwf-opendata → GRIB file → xarray → temp=305.15K, dew=297.15K
    │
    ▼
Calculator: thermofeel.humidex(t=32°C, td=24°C) → 40.2
    │
    ▼
Output: "Bangkok: Humidex 40.2°C - Great discomfort; avoid exertion"
```

## Tech Stack

| Component | Package | Purpose |
|-----------|---------|---------|
| ECMWF data | `ecmwf-opendata` | Download forecast data |
| GRIB reading | `xarray`, `cfgrib`, `eccodes` | Parse GRIB2 files |
| Humidex calc | `thermofeel` | Thermal comfort index calculation |
| Geocoding | `geopy` | Place name → coordinates |
| CLI | `click` | Command-line interface |
| Testing | `pytest`, `pytest-cov` | Unit and integration tests |
| Linting | `ruff` | Code quality |
| Type checking | `mypy` | Static type analysis |

## Data Model

```python
@dataclass
class Location:
    name: str
    latitude: float
    longitude: float

@dataclass
class WeatherData:
    temperature_c: float
    dewpoint_c: float
    forecast_step: int
    valid_time: datetime

@dataclass
class HumidexResult:
    location: Location
    humidex: float
    comfort: str
    weather: WeatherData
```

## Project Structure

```
humidex/
├── src/
│   └── humidex/
│       ├── __init__.py
│       ├── cli.py
│       ├── geocoder.py
│       ├── data_fetcher.py
│       └── calculator.py
├── tests/
│   ├── __init__.py
│   ├── test_geocoder.py
│   ├── test_data_fetcher.py
│   └── test_calculator.py
├── docs/
│   ├── ARCHITECTURE.md
│   └── TEST_REPORT.md
├── pyproject.toml
├── AGENTS.md
└── README.md
```

## External Services

- **ECMWF Open Data**: Free, no API key required. Limited to 500 simultaneous connections. Rolling 2-3 day archive.
- **Nominatim (OpenStreetMap)**: Free geocoding. Requires User-Agent header. Rate limited to 1 request/second.

## Error Handling

- Geocoding failures (place not found)
- ECMWF data unavailability (network issues, no forecast)
- Invalid coordinates (out of range)
- Graceful degradation with informative error messages
