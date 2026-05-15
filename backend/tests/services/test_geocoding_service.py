"""Unit tests for the geocoding service behavior."""

from __future__ import annotations

from typing import Any

import pytest

from app.schemas.external_sources import ExternalSourceState
from app.services.geocoding import GeocodingService, OneMapAuthError


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, Any] | None) -> None:
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> dict[str, Any]:
        return self._payload


class _DummyClient:
    def __init__(self, responder):
        self._responder = responder

    def _call(self, method: str, url: str, payload: dict[str, Any]) -> _FakeResponse:
        try:
            return self._responder(method, url, payload)
        except TypeError:
            return self._responder(url, payload)

    async def get(
        self, url: str, params: dict[str, Any], **_: Any
    ):  # pragma: no cover - simple forwarder
        return self._call("GET", url, params)

    async def post(
        self, url: str, json: dict[str, Any], **_: Any
    ):  # pragma: no cover - simple forwarder
        return self._call("POST", url, json)


def _make_service_with_responder(responder) -> GeocodingService:
    service = GeocodingService()
    service.client = _DummyClient(responder)
    service.google_maps_api_key = "test-key"
    service.onemap_access_token = "test-onemap-token"
    service.onemap_email = ""
    service.onemap_password = ""
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
    calls: list[str] = []

    def responder(url: str, params: dict[str, Any]) -> _FakeResponse:
        if "common/elastic/search" in url:
            calls.append(params["searchVal"])
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

    assert calls == ["1 Nassim Road Singapore 258458"]
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
async def test_geocode_lookup_uses_onemap_for_singapore_context_without_country() -> (
    None
):
    calls: list[str] = []

    def responder(url: str, params: dict[str, Any]) -> _FakeResponse:
        if "common/elastic/search" in url:
            calls.append(params["searchVal"])
            return _FakeResponse(
                200,
                {
                    "found": 1,
                    "results": [
                        {
                            "SEARCHVAL": "10 MARINA BOULEVARD",
                            "BLK_NO": "10",
                            "ROAD_NAME": "MARINA BOULEVARD",
                            "BUILDING": "MARINA BAY FINANCIAL CENTRE",
                            "ADDRESS": "10 MARINA BOULEVARD SINGAPORE 018983",
                            "POSTAL": "018983",
                            "LATITUDE": "1.2797934",
                            "LONGITUDE": "103.8538274",
                        },
                    ],
                },
            )
        raise AssertionError("unexpected URL in test")

    service = _make_service_with_responder(responder)
    result = await service.geocode_lookup(
        "10 marina boulevard",
        jurisdiction_code="SG",
    )

    assert calls == ["10 marina boulevard"]
    assert result is not None
    assert result.formatted_address == "10 MARINA BOULEVARD SINGAPORE 018983"
    assert result.address.street_name == "MARINA BOULEVARD"
    assert result.source.provider == "onemap_address_search"


@pytest.mark.asyncio
async def test_geocode_lookup_uses_onemap_no_comma_singapore_retry() -> None:
    calls: list[str] = []

    def responder(url: str, params: dict[str, Any]) -> _FakeResponse:
        if "common/elastic/search" in url:
            search_value = params["searchVal"]
            calls.append(search_value)
            if search_value == "28 Soon Lee Road":
                return _FakeResponse(200, {"found": 0, "results": []})
            if search_value == "28 Soon Lee Road Singapore":
                return _FakeResponse(
                    200,
                    {
                        "found": 1,
                        "results": [
                            {
                                "SEARCHVAL": "28 SOON LEE ROAD",
                                "BLK_NO": "28",
                                "ROAD_NAME": "SOON LEE ROAD",
                                "BUILDING": "NIL",
                                "ADDRESS": "28 SOON LEE ROAD SINGAPORE 628083",
                                "POSTAL": "628083",
                                "LATITUDE": "1.330785973343241",
                                "LONGITUDE": "103.6982752065997",
                            },
                        ],
                    },
                )
        raise AssertionError("unexpected URL in test")

    service = _make_service_with_responder(responder)
    result = await service.geocode_lookup("28 Soon Lee Rd", jurisdiction_code="SG")

    assert calls == ["28 Soon Lee Road", "28 Soon Lee Road Singapore"]
    assert result is not None
    assert result.formatted_address == "28 SOON LEE ROAD SINGAPORE 628083"
    assert result.latitude == pytest.approx(1.330785973343241)


@pytest.mark.asyncio
async def test_geocode_lookup_interpolates_missing_singapore_street_number() -> None:
    calls: list[str] = []

    def responder(url: str, params: dict[str, Any]) -> _FakeResponse:
        if "common/elastic/search" in url:
            search_value = params["searchVal"]
            calls.append(search_value)
            if search_value in {
                "25 Soon Lee Road",
                "25 Soon Lee Road Singapore",
                "25 Soon Lee Rd",
                "25 Soon Lee Rd Singapore",
                "24 Soon Lee Road Singapore",
            }:
                return _FakeResponse(200, {"found": 0, "results": []})
            if search_value == "26 Soon Lee Road Singapore":
                return _FakeResponse(
                    200,
                    {
                        "found": 1,
                        "results": [
                            {
                                "SEARCHVAL": "26 SOON LEE ROAD",
                                "BLK_NO": "26",
                                "ROAD_NAME": "SOON LEE ROAD",
                                "BUILDING": "NIL",
                                "ADDRESS": "26 SOON LEE ROAD SINGAPORE 628086",
                                "POSTAL": "628086",
                                "LATITUDE": "1.32953109420068",
                                "LONGITUDE": "103.6983092614985",
                            },
                        ],
                    },
                )
            if search_value in {
                "23 Soon Lee Road Singapore",
                "27 Soon Lee Road Singapore",
            }:
                return _FakeResponse(200, {"found": 0, "results": []})
            if search_value == "22 Soon Lee Road Singapore":
                return _FakeResponse(
                    200,
                    {
                        "found": 1,
                        "results": [
                            {
                                "SEARCHVAL": "22 SOON LEE ROAD",
                                "BLK_NO": "22",
                                "ROAD_NAME": "SOON LEE ROAD",
                                "BUILDING": "NIL",
                                "ADDRESS": "22 SOON LEE ROAD SINGAPORE 628082",
                                "POSTAL": "628082",
                                "LATITUDE": "1.3280",
                                "LONGITUDE": "103.6980",
                            },
                        ],
                    },
                )
        raise AssertionError("unexpected URL in test")

    service = _make_service_with_responder(responder)
    result = await service.geocode_lookup("25 Soon Lee Rd", jurisdiction_code="SG")

    assert result is not None
    assert result.source.provider == "onemap_street_interpolation"
    assert result.source.synthetic is True
    assert result.formatted_address == "25 SOON LEE ROAD SINGAPORE"
    assert result.address.block_number == "25"
    assert result.address.street_name == "SOON LEE ROAD"
    assert result.latitude == pytest.approx(1.32914832065051)
    assert "22 Soon Lee Road Singapore" in calls
    assert "26 Soon Lee Road Singapore" in calls


@pytest.mark.asyncio
async def test_geocode_lookup_does_not_interpolate_without_bracketing_points() -> None:
    calls: list[str] = []

    def responder(url: str, params: dict[str, Any]) -> _FakeResponse:
        if "common/elastic/search" in url:
            search_value = params["searchVal"]
            calls.append(search_value)
            if search_value == "26 Soon Lee Road Singapore":
                return _FakeResponse(
                    200,
                    {
                        "found": 1,
                        "results": [
                            {
                                "SEARCHVAL": "26 SOON LEE ROAD",
                                "BLK_NO": "26",
                                "ROAD_NAME": "SOON LEE ROAD",
                                "BUILDING": "NIL",
                                "ADDRESS": "26 SOON LEE ROAD SINGAPORE 628086",
                                "POSTAL": "628086",
                                "LATITUDE": "1.32953109420068",
                                "LONGITUDE": "103.6983092614985",
                            },
                        ],
                    },
                )
            return _FakeResponse(200, {"found": 0, "results": []})
        raise AssertionError("unexpected URL in test")

    service = _make_service_with_responder(responder)
    result = await service.geocode_lookup("25 Soon Lee Rd", jurisdiction_code="SG")

    assert result is None
    assert "26 Soon Lee Road Singapore" in calls
    assert "17 Soon Lee Road Singapore" in calls


@pytest.mark.asyncio
async def test_geocode_lookup_retries_onemap_with_abbreviation_expansion() -> None:
    calls: list[str] = []

    def responder(url: str, params: dict[str, Any]) -> _FakeResponse:
        if "common/elastic/search" in url:
            search_value = params["searchVal"]
            calls.append(search_value)
            if search_value in {
                "1 Nassim Road",
                "1 Nassim Road Singapore",
                "1 Nassim Rd",
            }:
                return _FakeResponse(200, {"found": 0, "results": []})
            if search_value == "1 Nassim Rd Singapore":
                return _FakeResponse(
                    200,
                    {
                        "found": 1,
                        "results": [
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
    result = await service.geocode_lookup(
        "1 Nassim Rd",
        jurisdiction_code="SG",
    )

    assert calls == [
        "1 Nassim Road",
        "1 Nassim Road Singapore",
        "1 Nassim Rd",
        "1 Nassim Rd Singapore",
    ]
    assert result is not None
    assert result.address.postal_code == "258458"


@pytest.mark.asyncio
async def test_geocode_lookup_requires_onemap_token_for_singapore_context() -> None:
    service = _make_service_with_responder(
        lambda *_: (_ for _ in ()).throw(AssertionError("OneMap should not be called"))
    )
    service.onemap_access_token = ""

    with pytest.raises(RuntimeError, match="ONEMAP_ACCESS_TOKEN or ONEMAP_EMAIL"):
        await service.geocode_lookup("25 Soon Lee Rd", jurisdiction_code="SG")


@pytest.mark.asyncio
async def test_geocode_lookup_mints_onemap_token_from_server_credentials() -> None:
    calls: list[tuple[str, str]] = []

    def responder(method: str, url: str, payload: dict[str, Any]) -> _FakeResponse:
        calls.append((method, url))
        if method == "POST" and "auth/post/getToken" in url:
            assert payload == {"email": "capture@example.com", "password": "secret"}
            return _FakeResponse(
                200,
                {"access_token": "minted-token", "expires_in": 3600},
            )
        if method == "GET" and "common/elastic/search" in url:
            return _FakeResponse(
                200,
                {
                    "found": 1,
                    "results": [
                        {
                            "SEARCHVAL": "25 SOON LEE ROAD",
                            "BLK_NO": "25",
                            "ROAD_NAME": "SOON LEE ROAD",
                            "BUILDING": "NIL",
                            "ADDRESS": "25 SOON LEE ROAD SINGAPORE 628083",
                            "POSTAL": "628083",
                            "LATITUDE": "1.3282813",
                            "LONGITUDE": "103.6984406",
                        },
                    ],
                },
            )
        raise AssertionError("unexpected URL in test")

    service = _make_service_with_responder(responder)
    service.onemap_access_token = ""
    service.onemap_email = "capture@example.com"
    service.onemap_password = "secret"

    result = await service.geocode_lookup("25 Soon Lee Rd", jurisdiction_code="SG")

    assert result is not None
    assert result.address.postal_code == "628083"
    assert service._onemap_access_token_cache == "minted-token"
    assert calls[0][0] == "POST"
    assert calls[1][0] == "GET"


@pytest.mark.asyncio
async def test_geocode_lookup_propagates_onemap_token_failure() -> None:
    calls: list[tuple[str, str]] = []

    def responder(method: str, url: str, payload: dict[str, Any]) -> _FakeResponse:
        calls.append((method, url))
        if method == "POST" and "auth/post/getToken" in url:
            return _FakeResponse(400, {"error": "Invalid OneMap credentials"})
        raise AssertionError("address search should not run after auth failure")

    service = _make_service_with_responder(responder)
    service.onemap_access_token = ""
    service.onemap_email = "capture@example.com"
    service.onemap_password = "secret"

    with pytest.raises(
        OneMapAuthError,
        match=r"OneMap token request failed \(400\): Invalid OneMap credentials",
    ):
        await service.geocode_lookup("10 Marina Boulevard", jurisdiction_code="SG")

    assert calls == [("POST", "https://www.onemap.gov.sg/api/auth/post/getToken")]


@pytest.mark.asyncio
async def test_geocode_lookup_reuses_cached_onemap_token() -> None:
    post_calls = 0

    def responder(method: str, url: str, payload: dict[str, Any]) -> _FakeResponse:
        nonlocal post_calls
        if method == "POST" and "auth/post/getToken" in url:
            post_calls += 1
            return _FakeResponse(200, {"access_token": "minted-token"})
        if method == "GET" and "common/elastic/search" in url:
            return _FakeResponse(
                200,
                {
                    "found": 1,
                    "results": [
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
    service.onemap_access_token = ""
    service.onemap_email = "capture@example.com"
    service.onemap_password = "secret"

    assert await service.geocode_lookup("1 Nassim Rd", jurisdiction_code="SG")
    assert await service.geocode_lookup("1 Nassim Rd", jurisdiction_code="SG")
    assert post_calls == 1


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


def test_onemap_address_metadata_reports_unavailable_without_token_or_credentials() -> (
    None
):
    service = GeocodingService()
    service.offline_mode = False
    service.client = _DummyClient(lambda *_: _FakeResponse(200, {}))
    service.onemap_access_token = ""
    service.onemap_email = ""
    service.onemap_password = ""

    metadata = service.get_onemap_address_metadata()

    assert metadata.provider == "onemap_address_search"
    assert metadata.state == ExternalSourceState.UNAVAILABLE
    assert metadata.configured is False
    assert metadata.reason == (
        "ONEMAP_ACCESS_TOKEN or ONEMAP_EMAIL/ONEMAP_PASSWORD not configured"
    )


def test_onemap_address_metadata_reports_live_with_server_credentials() -> None:
    service = GeocodingService()
    service.offline_mode = False
    service.client = _DummyClient(lambda *_: _FakeResponse(200, {}))
    service.onemap_access_token = ""
    service.onemap_email = "capture@example.com"
    service.onemap_password = "secret"

    metadata = service.get_onemap_address_metadata()

    assert metadata.provider == "onemap_address_search"
    assert metadata.state == ExternalSourceState.LIVE
    assert metadata.configured is True
    assert metadata.synthetic is False


def test_calculate_distance_returns_positive_value() -> None:
    service = GeocodingService()
    distance = service._calculate_distance(1.3, 103.8, 1.3005, 103.801)
    assert distance > 0
