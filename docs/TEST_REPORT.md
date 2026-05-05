# Test Report

## Summary

All tests pass with 90% code coverage, exceeding the 80% target.

## Test Results

| Test File | Tests | Passed | Failed | Coverage |
|-----------|-------|--------|--------|----------|
| test_models.py | 5 | 5 | 0 | 100% |
| test_geocoder.py | 4 | 4 | 0 | 100% |
| test_data_fetcher.py | 4 | 4 | 0 | 78% |
| test_calculator.py | 7 | 7 | 0 | 95% |
| test_cli.py | 7 | 7 | 0 | 93% |
| **Total** | **27** | **27** | **0** | **90%** |

## Module Coverage

| Module | Statements | Missed | Coverage |
|--------|------------|--------|----------|
| `__init__.py` | 11 | 3 | 73% |
| `calculator.py` | 20 | 1 | 95% |
| `cli.py` | 41 | 3 | 93% |
| `data_fetcher.py` | 50 | 11 | 78% |
| `geocoder.py` | 25 | 0 | 100% |
| `models.py` | 29 | 0 | 100% |
| **Total** | **176** | **18** | **90%** |

## Quality Checks

| Check | Status |
|-------|--------|
| Linting (ruff) | ✅ Pass |
| Type checking (mypy) | ✅ Pass |
| Unit tests | ✅ 27/27 Pass |
| Integration test (real ECMWF data) | ✅ Pass |
| Coverage (80% target) | ✅ 90% |

## Integration Test Results

Successfully tested end-to-end with real ECMWF data:

- **Bangkok**: Humidex 43.9°C - Great discomfort; avoid exertion
- **London**: Humidex 12.3°C - Comfortable

## Notes

- `__init__.py` coverage is 73% due to the `get_humidex()` function which requires network calls (covered by integration test)
- `data_fetcher.py` coverage is 78% due to the `_read_grib_at_location()` function which requires actual GRIB files (covered by integration test)
- All error paths are tested with mocked exceptions
