# Architecture - v3.0

## v2.0 Assessment

v2.0 is solid: clean module separation, dependency injection via Protocols, retry logic, frozen models, centralized config/errors. The following improvements are identified for v3.0.

## v3.0 Improvements

### 1. Extract Shared Retry Logic

**Problem:** `_retry_with_backoff` and `T = TypeVar("T")` are duplicated in `geocoder.py` and `fetcher.py`.

**Solution:** Create `src/humidex/retry.py` with a single, well-tested retry implementation. Both modules import from it.

### 2. Eliminate Global Mutable Singletons

**Problem:** `_DEFAULT_CONFIG`, `_default_geocoder`, `_default_fetcher` with `get_*`/`set_*`/`reset_*` functions create hidden mutable state that makes testing harder and is not thread-safe.

**Solution:** Replace with a `HumidexClient` class that holds config, geocoder, and fetcher as instance attributes. The convenience functions remain for backwards compatibility but delegate to a lazily-created client. This removes all module-level globals except one lazy-initialized client.

### 3. Fix Late Import in `fetcher.py`

**Problem:** `from datetime import datetime` is inside `_parse_grib` (line 225).

**Solution:** Move to top-level imports.

### 4. Add `TypedDict` for Serialization

**Problem:** `HumidexResult.to_dict()` returns `dict[str, float | str | int]` — no structure enforced.

**Solution:** Define `HumidexResultDict` TypedDict for type-safe serialization.

### 5. Support Coordinate Input

**Problem:** Only place names are accepted as input. Users with known coordinates must go through geocoding unnecessarily.

**Solution:** Add `get_humidex_by_coords(lat, lon, name, ...)` or accept `Location | str` as the first argument.

### 6. Export Missing `reset_config` from `__init__.py`

**Problem:** `reset_config` and `reset_geocoder`/`reset_fetcher` exist but aren't in `__all__`.

**Solution:** Add `reset_config` to `__all__` for testing consistency.

### 7. Improve Temp File Handling in `fetcher.py`

**Problem:** `NamedTemporaryFile(suffix=".grib2", delete=False)` then manual cleanup in `finally` is error-prone.

**Solution:** Use a proper context manager or `tempfile.mkstemp` pattern.

### 8. Narrow Exception Handling

**Problem:** `calculator.py:72` and `fetcher.py:238` catch bare `Exception`.

**Solution:** Catch specific exceptions from `thermofeel` and `xarray`/`cfgrib` where possible, falling back to a documented `Exception` catch with a comment explaining why.

### 9. Version Bump to 3.0.0

Update all version strings to `3.0.0`.

## v3.0 Directory Structure

```
src/humidex/
├── __init__.py          # Public API, version 3.0.0
├── models.py            # Data models + TypedDict
├── errors.py            # Custom exceptions (no change)
├── config.py            # Config (remove global state)
├── retry.py             # Shared retry logic (NEW)
├── protocols.py         # Dependency injection protocols
├── geocoder.py          # Nominatim geocoder (use shared retry)
├── fetcher.py           # ECMWF fetcher (use shared retry, fix imports)
├── calculator.py        # Humidex calculation (narrow exceptions)
├── formatter.py         # Output formatting (no change)
├── client.py            # HumidexClient class (NEW)
└── cli.py               # CLI (no change)
```

## Backwards Compatibility

All existing public API functions (`get_humidex`, `geocode`, `fetch_weather_data`, `calculate_humidex`, `format_human`, `format_json`) remain unchanged. The new `HumidexClient` class is an additional entry point for users who want explicit dependency management.
