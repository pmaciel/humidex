# Humidex

Retrieve humidex values for any location using ECMWF open data.

## Installation

```bash
pip install -e ".[dev]"
```

## Usage

### CLI

```bash
# Get humidex for a location
humidex "Bangkok"

# With forecast step (hours)
humidex "London" --step 12

# JSON output
humidex "Singapore" --json

# Verbose output
humidex "Bangkok" --verbose
```

### Python API

```python
from humidex import get_humidex

result = get_humidex("Bangkok")
print(result)
# Bangkok: Humidex 43.9°C - Great discomfort; avoid exertion

print(result.humidex)    # 43.9
print(result.comfort)    # "Great discomfort; avoid exertion"
```

## Humidex Scale

| Humidex | Comfort Level |
|---------|---------------|
| < 20 | Comfortable |
| 20-29 | Little discomfort |
| 30-39 | Some discomfort |
| 40-45 | Great discomfort; avoid exertion |
| ≥ 46 | Dangerous; possible heat stroke |

## Architecture

- **Geocoding**: OpenStreetMap Nominatim (free, no API key)
- **Weather Data**: ECMWF Open Data (free, CC BY 4.0)
- **Humidex Calculation**: ECMWF thermofeel library

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

## Development

```bash
# Run tests
pytest tests/ -v

# Lint
ruff check src/humidex tests

# Type check
mypy src/humidex
```

## License

MIT

## Data Attribution

Weather data from ECMWF Open Data is licensed under CC BY 4.0.
Please attribute ECMWF when using this data.
