# Architecture — humidex 5.0

`humidex` is a small Python library and CLI that returns the
[Environment Canada humidex](https://climate.weather.gc.ca/glossary_e.html#humidex)
for any location on Earth, using ECMWF open data as the meteorological source
and OpenStreetMap Nominatim for geocoding.

The codebase is intentionally layered: data models and protocols at the
bottom, two I/O adapters (geocoder, fetcher) above them, a pure calculator
in the middle, and a thin composition root (`HumidexClient`) that wires the
adapters together. The CLI and the package-level convenience functions are
the two user-facing surfaces.

---

## 1. Module map

All modules live under `src/humidex/`.

### `__init__.py`

The public API surface. It exports the data models, the protocol types, the
exception hierarchy, the `Config` dataclass, the `HumidexClient` class, the
formatters, and three free functions (`get_humidex`, `geocode`,
`fetch_weather_data`). `__version__` is read from installed package metadata
via `importlib.metadata`, falling back to `"0.0.0+local"` when the package is
running from a source checkout. `get_humidex` is a thin wrapper that
constructs a fresh `HumidexClient` per call and delegates to it; everything
else is re-exported.

### `client.py`

Defines `HumidexClient`, the composition root. The constructor takes optional
`config`, `geocoder`, and `fetcher` arguments and substitutes sensible
defaults (`get_config()`, `NominatimGeocoder`, `ECMWFFetcher`) for any that
are omitted. `get_humidex(place_or_location, step=0)` performs the
three-step pipeline: geocode (only if a string was supplied), fetch, then
calculate. There is no shared state between calls and no module-level
singletons.

### `config.py`

Contains the immutable, frozen `Config` dataclass and a `get_config()`
helper that returns `Config.from_env()`. `Config.from_env` parses the
`HUMIDEX_*` environment variables, validates the ECMWF source against a
`ClassVar` `frozenset` of allowed values, and verifies that
`temp_min_c <= temp_max_c`. Validation raises `ValueError` from
`__post_init__`, so invalid configurations cannot be constructed.

### `models.py`

Frozen dataclasses for the domain types — `Location`, `WeatherData`,
`HumidexResult` — plus the `HumidexResultDict` `TypedDict` used by
`HumidexResult.to_dict()` for type-safe JSON serialization. Coordinate and
temperature bounds are exposed as module-level `Final` constants
(`MIN_LAT`, `MAX_LAT`, `MIN_LON`, `MAX_LON`, `MIN_TEMP_C`, `MAX_TEMP_C`)
and re-checked in each model's `__post_init__`. `WeatherData` additionally
rejects naive datetimes.

### `protocols.py`

Defines two `runtime_checkable` `Protocol`s used for dependency injection:
`Geocoder` (`geocode(place_name) -> Location`) and `WeatherFetcher`
(`fetch(location, step=0) -> WeatherData`). Concrete implementations live
elsewhere; this module imports nothing besides the data models, keeping the
dependency graph acyclic.

### `geocoder.py`

`NominatimGeocoder` is the default `Geocoder` implementation, built on
`geopy`'s Nominatim client. It owns a single `Nominatim` instance configured
with the user-agent and timeout from `Config`. Calls go through
`retry.retry_with_backoff` with a rate-limit predicate that recognises
`GeocoderRateLimited` and a `no_retry` tuple containing `PlaceNotFoundError`
(missing places must not be retried). On exhausted retries, geopy errors are
wrapped in `GeocodingServiceError`. The module also exposes a
`geocode(place_name, config=None)` convenience function.

### `fetcher.py`

`ECMWFFetcher` is the default `WeatherFetcher`. It downloads a GRIB2 file
from `ecmwf.opendata.Client` for the requested forecast step, parses it with
`xarray` + `cfgrib`, and extracts the 2 m temperature (`t2m`) and 2 m
dewpoint (`d2m`) at the grid point nearest the supplied coordinates.
Temporary files are managed by a `_grib_tempfile_path` context manager
built on `tempfile.mkstemp` so the file descriptor is closed immediately
and the file is unlinked on exit. Forecast steps are validated against
`VALID_STEPS` (0–144 by 3 hours, 144–240 by 6 hours). Parse failures
(`KeyError`, `ValueError`, `OSError`, `RuntimeError` from xarray/cfgrib;
NaN, Inf, or out-of-range temperatures) raise `DataParseError`; download
failures, after retries are exhausted, raise `DataFetchError`. A free
`fetch_weather_data(location, step, config)` is exported for convenience.

### `calculator.py`

A pure, side-effect-free module. `calculate_humidex(location, weather, config)`
delegates the actual humidex formula to ECMWF's
[`thermofeel`](https://github.com/ecmwf/thermofeel) library, converting
inputs from Celsius to Kelvin and back. It catches `TypeError` and
`ValueError` from `thermofeel` and re-raises them as `CalculationError`.
`get_comfort_category(humidex)` maps a numeric humidex value to one of five
discomfort strings drawn from Environment Canada's published thresholds.

### `formatter.py`

Two pure functions: `format_human(result, verbose=False)` produces a
two- or five-line text block, and `format_json(result)` produces a
two-space-indented JSON document via `HumidexResult.to_dict()`. The
formatters are the only place in the package that decides how a result is
presented; everything else returns structured data.

### `cli.py`

A `click`-based command exposed as the `humidex` console script. Accepts
either a positional `PLACE` argument or `--lat`/`--lon` (with optional
`--name`); these inputs are mutually exclusive and `--lat`/`--lon` must be
provided as a pair. Other options: `--step/-s`, `--json`, and `--verbose/-v`
(repeatable). Logging is configured to write to stderr at WARNING / INFO /
DEBUG depending on verbosity. Known errors are translated through an
`_ERROR_MESSAGES` table to friendly messages and the process exits with
status 1; success exits with status 0.

### `errors.py`

A small, flat exception hierarchy (see section 3). All exceptions inherit
from `HumidexError`. `GeocodingError` carries an optional `place_name`
attribute; `DataFetchError` carries an optional `location_info` attribute.

### `retry.py`

Single source of truth for retry semantics. Exposes one function,
`retry_with_backoff`, used by both `geocoder.py` and `fetcher.py`. See
section 5 for the formula and parameters.

---

## 2. Dependency-injection flow

`HumidexClient` is the composition root. Two protocols define the seams:

```
        +------------------+
        |   HumidexClient  |
        +--------+---------+
                 |
        owns     |
        ---------+----------+
        |                   |
        v                   v
 +---------------+   +-------------------+
 |   Geocoder    |   |  WeatherFetcher   |   (Protocols, in protocols.py)
 +-------+-------+   +---------+---------+
         ^                     ^
         | implements          | implements
         |                     |
 +---------------+   +-------------------+
 | NominatimGeo- |   |   ECMWFFetcher    |   (Default implementations)
 |    coder      |   |                   |
 +---------------+   +-------------------+
```

`HumidexClient.__init__` accepts `config`, `geocoder`, and `fetcher`
arguments. Any argument left as `None` is replaced by the default:
`get_config()` for the configuration, `NominatimGeocoder(config=...)` for
the geocoder, and `ECMWFFetcher(config=...)` for the fetcher. Tests and
advanced callers can swap in fakes or alternative implementations simply by
passing objects that satisfy the `Geocoder` / `WeatherFetcher` protocols
(both protocols are `@runtime_checkable`).

The package-level `get_humidex(...)` constructs a fresh `HumidexClient` on
every call and forwards its arguments. There is no global mutable state in
the package.

---

## 3. Error hierarchy

```
HumidexError
├── GeocodingError              (carries .place_name)
│   ├── PlaceNotFoundError
│   └── GeocodingServiceError
├── DataFetchError              (carries .location_info)
│   ├── InvalidStepError
│   └── DataParseError
└── CalculationError
```

Catching `HumidexError` is sufficient to handle every error the library
intentionally raises. The CLI catches the leaf classes individually so it
can pick a friendlier message per failure mode.

---

## 4. Configuration & environment variables

`Config` is a frozen dataclass. Defaults are baked into the class; any
field can be overridden by an environment variable parsed by
`Config.from_env()`. `get_config()` is a thin wrapper around
`Config.from_env()` and is called whenever a default config is needed.

| Env var | Type | Default | Field |
|---|---|---|---|
| `HUMIDEX_USER_AGENT` | str | `"humidex/5.0.0"` | `user_agent` |
| `HUMIDEX_GEOCODER_TIMEOUT` | float (seconds) | `10.0` | `geocoder_timeout` |
| `HUMIDEX_ECMWF_SOURCE` | str (`ecmwf`/`aws`/`google`/`azure`) | `"aws"` | `ecmwf_source` |
| `HUMIDEX_ECMWF_TIMEOUT` | float (seconds) | `60.0` | `ecmwf_timeout` |
| `HUMIDEX_RETRY_MAX` | int | `3` | `retry_max` |
| `HUMIDEX_RETRY_BACKOFF` | float (seconds) | `1.0` | `retry_backoff` |
| `HUMIDEX_TEMP_MIN_C` | float (°C) | `-90.0` | `temp_min_c` |
| `HUMIDEX_TEMP_MAX_C` | float (°C) | `60.0` | `temp_max_c` |

Validation:

- `ecmwf_source` must be one of the four values listed above; anything else
  raises `ValueError` from `__post_init__`.
- `temp_min_c` must be `<=` `temp_max_c`.
- Unparseable numeric environment variables raise `ValueError` with the
  offending variable name in the message.

---

## 5. Retry semantics

All retry behaviour lives in `retry.py`. Both `NominatimGeocoder` and
`ECMWFFetcher` call the same function:

```python
retry_with_backoff(
    func,
    max_retries=config.retry_max,
    base_backoff=config.retry_backoff,
    rate_limit_multiplier=2.0,
    is_rate_limited=...,    # optional predicate
    no_retry=(...),         # exception types to surface immediately
)
```

**Backoff formula.** Before the next attempt, the function sleeps for:

```
delay = base_backoff * (2 ** attempt) * multiplier
```

where `attempt` is zero-indexed and `multiplier` is `rate_limit_multiplier`
(default `2.0`) when `is_rate_limited(exc)` returns true and `1.0`
otherwise. With the defaults (`base_backoff=1.0`, `rate_limit_multiplier=2.0`,
`max_retries=3`), the delay schedule is `1s → 2s → 4s` for ordinary errors
and `2s → 4s → 8s` for rate-limited errors. After `max_retries + 1` total
attempts, the last exception is re-raised.

**`no_retry` parameter.** A tuple of exception types that must never be
retried. If the called function raises an instance of any type in this
tuple, it is re-raised immediately. The geocoder uses this for
`PlaceNotFoundError` (a missing place will not appear if you ask again).
The fetcher narrows around `InvalidStepError` and `DataParseError` at the
call site instead, but the mechanism is the same.

**Rate-limit multiplier.** Used by the geocoder, where geopy's
`GeocoderRateLimited` indicates Nominatim wants us to back off harder.
`_is_rate_limited` is a one-line predicate passed into
`retry_with_backoff`; when it matches, the multiplier doubles the
exponential delay.

---

## 6. CLI entry point

The `humidex` console script is registered in `pyproject.toml` and points at
`humidex.cli:main`.

**Synopsis**

```
humidex [PLACE] [--lat LAT --lon LON [--name NAME]]
        [-s STEP] [--json] [-v ...]
```

**Arguments and options**

| Flag | Type | Default | Purpose |
|---|---|---|---|
| `PLACE` | positional str | — | Human-readable location name. Mutually exclusive with `--lat`/`--lon`. |
| `--lat` | float | — | Latitude in decimal degrees. Must be paired with `--lon`. |
| `--lon` | float | — | Longitude in decimal degrees. Must be paired with `--lat`. |
| `--name` | str | `"(LAT, LON)"` | Display name when using `--lat`/`--lon`. |
| `--step`, `-s` | int | `0` | Forecast step in hours (`0` = analysis). |
| `--json` | flag | off | Emit JSON instead of human-readable text. |
| `--verbose`, `-v` | repeatable flag | 0 | `-v` = INFO logging, `-vv` = DEBUG; also enables verbose human output. |

**Exit codes**

| Code | Meaning |
|---|---|
| `0` | Success; result printed to stdout. |
| `1` | Argument error, or any caught `HumidexError` subclass. Error message goes to stderr prefixed with `Error:`. |
| `2` | Click's own usage error (unknown option, bad type, missing value). |

Logging is always written to stderr; only the formatted result reaches
stdout, so the CLI is safe to pipe.

---

## 7. Backward-compatibility guarantees

Three free functions are preserved at the package root so existing callers
do not need to construct a `HumidexClient`:

- `humidex.get_humidex(place_or_location, step=0, config=None, geocoder=None, fetcher=None)`
  — accepts either a place-name string or a `Location` and returns a
  `HumidexResult`. Internally builds a fresh `HumidexClient` per call.
- `humidex.geocode(place_name, config=None)` — returns a `Location`,
  delegating to `NominatimGeocoder`.
- `humidex.fetch_weather_data(location, step=0, config=None)` — returns a
  `WeatherData`, delegating to `ECMWFFetcher`.

The formatters (`format_human`, `format_json`) and `calculate_humidex` /
`get_comfort_category` are also re-exported. Together with the data
models and the exception hierarchy, this is the stable public surface;
anything not listed in `__all__` is internal.

---

## 8. Known limitations

- **Single grid-point sampling.** The fetcher reads exactly one ECMWF grid
  point — the one nearest the supplied coordinates. There is no
  interpolation between neighbouring cells. For most uses this is well
  within the resolution of the underlying forecast, but expect coarse
  results near sharp coastlines or terrain transitions.
- **No caching.** Every `get_humidex` call re-geocodes (when a string is
  passed) and downloads a fresh GRIB2 file. Repeated calls for the same
  place hit Nominatim and ECMWF every time. Callers who need caching should
  wrap their own `Geocoder` / `WeatherFetcher` implementations and inject
  them via `HumidexClient`.
- **Synchronous only.** Both adapters are blocking; there is no async
  variant. Concurrent fetches require running `HumidexClient` calls in
  threads (the client itself is stateless after construction, so this is
  safe as long as each thread uses its own client or the underlying
  adapters are thread-safe).
- **No bulk API.** There is no batch entry point for many locations or
  many forecast steps in a single GRIB request, even though the ECMWF
  client supports it. Each call downloads its own file.
