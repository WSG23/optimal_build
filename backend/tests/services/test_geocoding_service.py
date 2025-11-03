"""Unit tests for the geocoding service fallback logic."""

from __future__ import annotations

from typing import Any

import pytest

from app.services.geocoding import GeocodingService


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, Any] | None) -> None:
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> dict[str, Any]:
        return self._payload


class _DummyClient:
    def __init__(self, responder):
        self._responder = responder

    async def get(
        self, url: str, params: dict[str, Any]
    ):  # pragma: no cover - simple forwarder
        return self._responder(url, params)


def _make_service_with_responder(responder) -> GeocodingService:
    service = GeocodingService()
    service.client = _DummyClient(responder)
    return service


@pytest.mark.asyncio
async def test_reverse_geocode_returns_onemap_result(monkeypatch) -> None:
    def responder(url: str, params: dict[str, Any]) -> _FakeResponse:
        if "revgeocodexy" in url:
            return _FakeResponse(
                200,
                {
                    "GeocodeInfo": [
                        {
                            "ROAD": "Main Road",
                            "BUILDINGNAME": "Test Tower",
                            "BLOCK": "123",
                            "POSTALCODE": "238123",
                        }
                    ]
                },
            )
        raise AssertionError("unexpected URL in test")

    service = _make_service_with_responder(responder)
    address = await service.reverse_geocode(1.3, 103.8)

    assert address is not None
    assert address.full_address == "Main Road"
    assert address.building_name == "Test Tower"
    assert address.district == "D09 - Orchard Road, River Valley"


@pytest.mark.asyncio
async def test_reverse_geocode_falls_back_to_mock(monkeypatch) -> None:
    service = _make_service_with_responder(
        lambda *_: (_ for _ in ()).throw(Exception("boom"))
    )

    address = await service.reverse_geocode(1.3, 103.8)

    assert address is not None
    assert address.full_address.startswith("Mocked Address")


@pytest.mark.asyncio
async def test_reverse_geocode_handles_empty_payload() -> None:
    """Ensure empty OneMap results fall back to the mock address."""

    def responder(url: str, params: dict[str, Any]) -> _FakeResponse:
        if "revgeocodexy" in url:
            return _FakeResponse(200, {"GeocodeInfo": []})
        raise AssertionError("unexpected URL in test")

    service = _make_service_with_responder(responder)
    address = await service.reverse_geocode(1.33, 103.82)

    assert address is not None
    assert address.full_address.startswith("Mocked Address")


@pytest.mark.asyncio
async def test_reverse_geocode_with_google_maps_fallback(monkeypatch) -> None:
    """Test reverse_geocode attempts Google Maps fallback when OneMap fails."""

    def responder(url: str, params: dict[str, Any]) -> _FakeResponse:
        if "revgeocodexy" in url:
            return _FakeResponse(404, {})  # OneMap fails
        raise AssertionError("unexpected URL in test")

    service = _make_service_with_responder(responder)
    service.google_maps_api_key = "test-key"  # Enable Google Maps fallback

    # Mock the Google fallback to return something
    async def mock_google_reverse(*args, **kwargs):
        from app.services.geocoding import Address

        return Address(
            full_address="Google Address",
            street_name="Google Street",
            country="Singapore",
        )

    monkeypatch.setattr(service, "_google_reverse_geocode", mock_google_reverse)

    address = await service.reverse_geocode(1.3, 103.8)

    assert address is not None
    assert address.full_address == "Google Address"


@pytest.mark.asyncio
async def test_geocode_with_google_maps_fallback(monkeypatch) -> None:
    """Test geocode attempts Google Maps fallback when OneMap fails."""

    def responder(url: str, params: dict[str, Any]) -> _FakeResponse:
        if "elastic/search" in url:
            return _FakeResponse(404, {})  # OneMap fails
        raise AssertionError("unexpected URL in test")

    service = _make_service_with_responder(responder)
    service.google_maps_api_key = "test-key"  # Enable Google Maps fallback

    # Mock the Google fallback to return coordinates
    async def mock_google_geocode(*args, **kwargs):
        return (1.2345, 103.6789)

    monkeypatch.setattr(service, "_google_geocode", mock_google_geocode)

    coords = await service.geocode("Test Address")

    assert coords == (1.2345, 103.6789)


@pytest.mark.asyncio
async def test_reverse_geocode_with_none_client() -> None:
    """Test reverse_geocode when client is None."""
    service = GeocodingService()
    service.client = None

    address = await service.reverse_geocode(1.3, 103.8)

    assert address is not None
    assert address.full_address.startswith("Mocked Address")


@pytest.mark.asyncio
async def test_geocode_with_none_client() -> None:
    """Test geocode when client is None."""
    service = GeocodingService()
    service.client = None

    coords = await service.geocode("Test Address")

    assert coords == (1.3000, 103.8500)


@pytest.mark.asyncio
async def test_geocode_returns_onemap_coordinates(monkeypatch) -> None:
    def responder(url: str, params: dict[str, Any]) -> _FakeResponse:
        if "elastic/search" in url:
            return _FakeResponse(
                200,
                {
                    "results": [
                        {
                            "LATITUDE": "1.3050",
                            "LONGITUDE": "103.8310",
                        }
                    ]
                },
            )
        raise AssertionError("unexpected URL in test")

    service = _make_service_with_responder(responder)
    coords = await service.geocode("Test Address")

    assert coords == (1.3050, 103.8310)


@pytest.mark.asyncio
async def test_geocode_returns_fallback_when_onemap_fails() -> None:
    service = _make_service_with_responder(
        lambda *_: (_ for _ in ()).throw(Exception("boom"))
    )

    coords = await service.geocode("Unknown Address")
    assert coords == (1.3000, 103.8500)


@pytest.mark.asyncio
async def test_geocode_returns_fallback_when_coordinates_missing() -> None:
    """Latitude/longitude of zero should trigger the default CBD fallback."""

    def responder(url: str, params: dict[str, Any]) -> _FakeResponse:
        if "elastic/search" in url:
            return _FakeResponse(
                200, {"results": [{"LATITUDE": "0.0", "LONGITUDE": "0"}]}
            )
        raise AssertionError("unexpected URL in test")

    service = _make_service_with_responder(responder)
    coords = await service.geocode("Zero Coord Address")
    assert coords == (1.3000, 103.8500)


@pytest.mark.asyncio
async def test_nearby_amenities_returns_mock_when_client_missing() -> None:
    service = GeocodingService()
    service.client = None

    amenities = await service.get_nearby_amenities(1.3, 103.8)
    assert amenities["mrt_stations"][0]["name"] == "Mock MRT"


@pytest.mark.asyncio
async def test_nearby_amenities_returns_results_within_radius() -> None:
    """Amenity results within the radius should be preserved."""

    def responder(url: str, params: dict[str, Any]) -> _FakeResponse:
        if "retrieveTheme" in url:
            theme = params["queryName"]
            payload = {
                "SrchResults": [
                    {"FeatCount": 2},
                    {
                        "NAME": f"{theme}-near",
                        "LatLng": "1.3005,103.8495",
                    },
                    {
                        "NAME": f"{theme}-far",
                        "LatLng": "1.3500,103.9000",
                    },
                ]
            }
            return _FakeResponse(200, payload)
        raise AssertionError("unexpected URL in test")

    service = _make_service_with_responder(responder)

    amenities = await service.get_nearby_amenities(1.3, 103.85, radius_m=800)

    for result_list in amenities.values():
        names = {entry["name"] for entry in result_list}
        assert any(name.endswith("near") for name in names)
        assert all("far" not in name for name in names)


@pytest.mark.asyncio
async def test_nearby_amenities_fallback_when_no_results() -> None:
    """If OneMap returns empty payloads, the mock amenity set is used."""

    def responder(url: str, params: dict[str, Any]) -> _FakeResponse:
        if "retrieveTheme" in url:
            return _FakeResponse(200, {"SrchResults": []})
        raise AssertionError("unexpected URL in test")

    service = _make_service_with_responder(responder)
    amenities = await service.get_nearby_amenities(1.3, 103.85, radius_m=300)

    assert amenities["parks"][0]["name"] == "Mock Park"


def test_get_district_from_postal_unknown() -> None:
    service = GeocodingService()
    assert service._get_district_from_postal("000000") is None
    assert service._get_district_from_postal("") is None


def test_calculate_distance_returns_positive_value() -> None:
    service = GeocodingService()
    distance = service._calculate_distance(1.3, 103.8, 1.3005, 103.801)
    assert distance > 0
