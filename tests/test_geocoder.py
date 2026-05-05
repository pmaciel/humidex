"""Tests for geocoder module."""

from unittest.mock import MagicMock, patch

import pytest

from humidex.geocoder import GeocoderError, PlaceNotFoundError, geocode
from humidex.models import Location


@pytest.fixture
def mock_nominatim() -> MagicMock:
    """Mock Nominatim geolocator."""
    with patch("humidex.geocoder.Nominatim") as mock:
        yield mock


def test_geocode_success(mock_nominatim: MagicMock) -> None:
    """Test successful geocoding."""
    mock_location = MagicMock()
    mock_location.address = "Bangkok, Thailand"
    mock_location.latitude = 13.7563
    mock_location.longitude = 100.5018

    mock_instance = MagicMock()
    mock_instance.geocode.return_value = mock_location
    mock_nominatim.return_value = mock_instance

    result = geocode("Bangkok")

    assert isinstance(result, Location)
    assert result.name == "Bangkok"
    assert result.latitude == 13.7563
    assert result.longitude == 100.5018


def test_geocode_not_found(mock_nominatim: MagicMock) -> None:
    """Test geocoding when place is not found."""
    mock_instance = MagicMock()
    mock_instance.geocode.return_value = None
    mock_nominatim.return_value = mock_instance

    with pytest.raises(PlaceNotFoundError, match="Place not found"):
        geocode("NonexistentPlace12345")


def test_geocode_service_unavailable(mock_nominatim: MagicMock) -> None:
    """Test geocoding when service is unavailable."""
    from geopy.exc import GeocoderUnavailable

    mock_instance = MagicMock()
    mock_instance.geocode.side_effect = GeocoderUnavailable("Service down")
    mock_nominatim.return_value = mock_instance

    with pytest.raises(GeocoderError, match="Geocoding service unavailable"):
        geocode("Bangkok")


def test_geocode_uses_first_result(mock_nominatim: MagicMock) -> None:
    """Test that geocode uses the first result from Nominatim."""
    mock_location = MagicMock()
    mock_location.address = "London, Greater London, England, United Kingdom"
    mock_location.latitude = 51.5074
    mock_location.longitude = -0.1278

    mock_instance = MagicMock()
    mock_instance.geocode.return_value = mock_location
    mock_nominatim.return_value = mock_instance

    result = geocode("London")

    assert result.name == "London"
    mock_instance.geocode.assert_called_once_with("London")
