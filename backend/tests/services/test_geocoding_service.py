"""Unit tests for the geocoding service behavior."""

from __future__ import annotations

from typing import Any

import pytest

from app.schemas.external_sources import ExternalSourceState
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
    service.google_maps_api_key = "test-key"
    service.offline_mode = False
    return service


@pytest.mark.asyncio
async def test_reverse_geocode_returns_google_result() -> None:
    def responder(url: str, params: dict[str, Any]) -> _FakeResponse:
        if "maps.googleapis.com/maps/api/geocode/json" in url:
            return _FakeResponse(
                200,
                {
                    "status": "OK",
                    "results": [
                        {
                            "formatted_address": "Main Road, Singapore 238123",
                            "address_components": [
                                {"long_name": "123", "types": ["street_number"]},
                                {"long_name": "Main Road", "types": ["route"]},
                                {"long_name": "238123", "types": ["postal_code"]},
                                {"long_name": "Singapore", "types": ["country"]},
                            ],
                        },
                    ],
                },
            )
        raise AssertionError("unexpected URL in test")

    service = _make_service_with_responder(responder)
    address = await service.reverse_geocode(1.3, 103.8)

    assert address is not None
    assert address.full_address == "Main Road, Singapore 238123"
    assert address.district == "D09 - Orchard Road, River Valley"


@pytest.mark.asyncio
async def test_reverse_geocode_raises_when_client_fails() -> None:
    service = _make_service_with_responder(
        lambda *_: (_ for _ in ()).throw(Exception("boom"))
    )

    with pytest.raises(Exception, match="boom"):
        await service.reverse_geocode(1.3, 103.8)


@pytest.mark.asyncio
async def test_reverse_geocode_handles_empty_payload() -> None:
    """Ensure empty results return no address."""

    def responder(url: str, params: dict[str, Any]) -> _FakeResponse:
        if "maps.googleapis.com/maps/api/geocode/json" in url:
            return _FakeResponse(200, {"status": "ZERO_RESULTS", "results": []})
        raise AssertionError("unexpected URL in test")

    service = _make_service_with_responder(responder)
    address = await service.reverse_geocode(1.33, 103.82)

    assert address is None


@pytest.mark.asyncio
async def test_geocode_returns_google_coordinates() -> None:
    def responder(url: str, params: dict[str, Any]) -> _FakeResponse:
        if "maps.googleapis.com/maps/api/geocode/json" in url:
            return _FakeResponse(
                200,
                {
                    "status": "OK",
                    "results": [
                        {
                            "formatted_address": "Test Address",
                            "geometry": {"location": {"lat": 1.3050, "lng": 103.8310}},
                        }
                    ],
                },
            )
        raise AssertionError("unexpected URL in test")

    service = _make_service_with_responder(responder)
    coords = await service.geocode("Test Address")

    assert coords == (1.3050, 103.8310)


@pytest.mark.asyncio
async def test_geocode_lookup_prefers_onemap_for_singapore_addresses() -> None:
    def responder(url: str, params: dict[str, Any]) -> _FakeResponse:
        if "common/elastic/search" in url:
            assert params["searchVal"] == "1 Nassim Rd, Singapore 258458"
            return _FakeResponse(
                200,
                {
                    "found": 2,
                    "results": [
                        {
                            "SEARCHVAL": "10 TANGLIN ROAD",
                            "BLK_NO": "10",
                            "ROAD_NAME": "TANGLIN ROAD",
                            "BUILDING": "NIL",
                            "ADDRESS": "10 TANGLIN ROAD SINGAPORE 247908",
                            "POSTAL": "247908",
                            "LATITUDE": "1.3065566",
                            "LONGITUDE": "103.8262787",
                        },
                        {
                            "SEARCHVAL": "1 NASSIM ROAD",
                            "BLK_NO": "1",
                            "ROAD_NAME": "NASSIM ROAD",
                            "BUILDING": "NIL",
                            "ADDRESS": "1 NASSIM ROAD SINGAPORE 258458",
                            "POSTAL": "258458",
                            "LATITUDE": "1.3071",
                            "LONGITUDE": "103.8259",
                        },
                    ],
                },
            )
        raise AssertionError("unexpected URL in test")

    service = _make_service_with_responder(responder)
    result = await service.geocode_lookup("1 Nassim Rd, Singapore 258458")

    assert result is not None
    assert result.latitude == pytest.approx(1.3071)
    assert result.longitude == pytest.approx(103.8259)
    assert result.formatted_address == "1 NASSIM ROAD SINGAPORE 258458"
    assert result.address.street_name == "NASSIM ROAD"
    assert result.address.block_number == "1"
    assert result.address.postal_code == "258458"
    assert result.source.provider == "onemap_address_search"
    assert result.source.state == ExternalSourceState.LIVE


@pytest.mark.asyncio
async def test_reverse_geocode_with_none_client() -> None:
    """Test reverse_geocode when client is None."""
    service = GeocodingService()
    service.client = None
    service.google_maps_api_key = "test-key"
    service.offline_mode = False

    with pytest.raises(RuntimeError):
        await service.reverse_geocode(1.3, 103.8)


@pytest.mark.asyncio
async def test_geocode_with_none_client() -> None:
    """Test geocode when client is None."""
    service = GeocodingService()
    service.client = None
    service.google_maps_api_key = "test-key"
    service.offline_mode = False

    with pytest.raises(RuntimeError):
        await service.geocode("Test Address")


@pytest.mark.asyncio
async def test_geocode_returns_fallback_when_onemap_fails() -> None:
    service = _make_service_with_responder(
        lambda *_: (_ for _ in ()).throw(Exception("boom"))
    )

    with pytest.raises(Exception, match="boom"):
        await service.geocode("Unknown Address")


@pytest.mark.asyncio
async def test_geocode_returns_fallback_when_coordinates_missing() -> None:
    """Latitude/longitude of zero should trigger a null result."""

    def responder(url: str, params: dict[str, Any]) -> _FakeResponse:
        if "maps.googleapis.com/maps/api/geocode/json" in url:
            return _FakeResponse(
                200,
                {
                    "status": "OK",
                    "results": [
                        {
                            "formatted_address": "Zero Coord Address",
                            "geometry": {"location": {"lat": 0, "lng": 0}},
                        }
                    ],
                },
            )
        raise AssertionError("unexpected URL in test")

    service = _make_service_with_responder(responder)
    coords = await service.geocode("Zero Coord Address")
    assert coords is None


@pytest.mark.asyncio
async def test_nearby_amenities_returns_mock_when_client_missing() -> None:
    service = GeocodingService()
    service.client = None
    service.offline_mode = True

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
    """If OneMap returns empty payloads, the amenity set remains empty."""

    def responder(url: str, params: dict[str, Any]) -> _FakeResponse:
        if "retrieveTheme" in url:
            return _FakeResponse(200, {"SrchResults": []})
        raise AssertionError("unexpected URL in test")

    service = _make_service_with_responder(responder)
    amenities = await service.get_nearby_amenities(1.3, 103.85, radius_m=300)

    assert all(not items for items in amenities.values())


def test_get_district_from_postal_unknown() -> None:
    service = GeocodingService()
    assert service._get_district_from_postal("000000") is None
    assert service._get_district_from_postal("") is None


def test_google_geocoding_metadata_reports_mock_without_api_key() -> None:
    service = GeocodingService()
    service.google_maps_api_key = None
    service.offline_mode = False

    metadata = service.get_google_geocoding_metadata()

    assert metadata.provider == "google_maps"
    assert metadata.state == ExternalSourceState.MOCK
    assert metadata.synthetic is True
    assert metadata.reason == "GOOGLE_MAPS_API_KEY not configured"


def test_google_geocoding_metadata_reports_live_when_client_ready() -> None:
    service = GeocodingService()
    service.google_maps_api_key = "test-key"
    service.client = _DummyClient(lambda *_: _FakeResponse(200, {}))
    service.offline_mode = False

    metadata = service.get_google_geocoding_metadata()

    assert metadata.provider == "google_maps"
    assert metadata.state == ExternalSourceState.LIVE
    assert metadata.synthetic is False


def test_onemap_amenities_metadata_reports_mock_in_offline_mode() -> None:
    service = GeocodingService()
    service.offline_mode = True
    service.client = None

    metadata = service.get_onemap_amenities_metadata()

    assert metadata.provider == "onemap"
    assert metadata.state == ExternalSourceState.MOCK
    assert metadata.synthetic is True
    assert metadata.reason == "OFFLINE_MODE enabled"


def test_onemap_amenities_metadata_reports_live_when_client_ready() -> None:
    service = GeocodingService()
    service.offline_mode = False
    service.client = _DummyClient(lambda *_: _FakeResponse(200, {}))

    metadata = service.get_onemap_amenities_metadata()

    assert metadata.provider == "onemap"
    assert metadata.state == ExternalSourceState.LIVE
    assert metadata.synthetic is False


def test_calculate_distance_returns_positive_value() -> None:
    service = GeocodingService()
    distance = service._calculate_distance(1.3, 103.8, 1.3005, 103.801)
    assert distance > 0
