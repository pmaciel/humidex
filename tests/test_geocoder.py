"""Tests for geocoder module."""

from unittest.mock import MagicMock, patch

import pytest

from humidex.config import Config
from humidex.errors import GeocodingServiceError, PlaceNotFoundError
from humidex.geocoder import NominatimGeocoder, geocode
from humidex.models import Location


@pytest.fixture
def geocoder(config: Config) -> NominatimGeocoder:
    """Create a geocoder with test config."""
    return NominatimGeocoder(config=config)


class TestNominatimGeocoder:
    """Tests for NominatimGeocoder."""

    def test_geocode_success(self, geocoder: NominatimGeocoder) -> None:
        mock_location = MagicMock()
        mock_location.latitude = 13.7563
        mock_location.longitude = 100.5018

        with patch.object(geocoder._geolocator, "geocode", return_value=mock_location):
            result = geocoder.geocode("Bangkok")

        assert isinstance(result, Location)
        assert result.name == "Bangkok"
        assert result.latitude == pytest.approx(13.7563)
        assert result.longitude == pytest.approx(100.5018)

    def test_place_not_found(self, geocoder: NominatimGeocoder) -> None:
        with patch.object(geocoder._geolocator, "geocode", return_value=None):
            with pytest.raises(PlaceNotFoundError, match="Place not found"):
                geocoder.geocode("NonexistentPlace12345")

    def test_service_unavailable(self, geocoder: NominatimGeocoder) -> None:
        from geopy.exc import GeocoderUnavailable

        with patch.object(
            geocoder._geolocator,
            "geocode",
            side_effect=GeocoderUnavailable("Service down"),
        ):
            with pytest.raises(GeocodingServiceError):
                geocoder.geocode("Bangkok")

    def test_uses_place_name_as_result_name(self, geocoder: NominatimGeocoder) -> None:
        mock_location = MagicMock()
        mock_location.latitude = 51.5074
        mock_location.longitude = -0.1278

        with patch.object(geocoder._geolocator, "geocode", return_value=mock_location):
            result = geocoder.geocode("London, UK")

        assert result.name == "London, UK"

    def test_rate_limited_triggers_multiplier(self, config: Config) -> None:
        """GeocoderRateLimited should retry with the rate-limit multiplier applied."""
        from geopy.exc import GeocoderRateLimited

        geocoder = NominatimGeocoder(config=config)

        mock_location = MagicMock()
        mock_location.latitude = 13.7563
        mock_location.longitude = 100.5018

        with (
            patch.object(
                geocoder._geolocator,
                "geocode",
                side_effect=[GeocoderRateLimited("slow down"), mock_location],
            ),
            patch("humidex.retry.time.sleep") as mock_sleep,
        ):
            result = geocoder.geocode("Bangkok")

        assert result.latitude == pytest.approx(13.7563)
        assert mock_sleep.call_count == 1
        delay = mock_sleep.call_args_list[0][0][0]
        # Multiplier (2.0) was applied vs the unmultiplied base delay
        # base_backoff * 2**0 = config.retry_backoff (no multiplier)
        assert delay > config.retry_backoff
        assert delay == pytest.approx(config.retry_backoff * 2.0)


class TestGeocodeConvenience:
    """Tests for geocode convenience function."""

    def test_geocode_calls_geocoder(self, config: Config) -> None:
        mock_location = MagicMock()
        mock_location.latitude = 13.7563
        mock_location.longitude = 100.5018

        mock_geocoder = MagicMock()
        mock_geocoder.geocode.return_value = mock_location

        with patch("humidex.geocoder.NominatimGeocoder", return_value=mock_geocoder):
            result = geocode("Bangkok", config=config)

        assert result.latitude == pytest.approx(13.7563)
        mock_geocoder.geocode.assert_called_once_with("Bangkok")
