from __future__ import annotations

from starlette.requests import Request

from app.utils.client_ip import get_client_ip


def _request_with_headers(headers: dict[str, str]) -> Request:
    encoded = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": encoded,
        "query_string": b"",
        "server": ("testserver", 80),
        "client": ("203.0.113.10", 12345),
        "scheme": "http",
    }
    return Request(scope)


def test_get_client_ip_prefers_first_forwarded_for() -> None:
    request = _request_with_headers({"X-Forwarded-For": "198.51.100.1, 203.0.113.10"})
    assert get_client_ip(request, lambda _: "127.0.0.1") == "198.51.100.1"


def test_get_client_ip_falls_back_when_forwarded_for_invalid() -> None:
    request = _request_with_headers({"X-Forwarded-For": "not-an-ip"})
    assert get_client_ip(request, lambda _: "127.0.0.1") == "127.0.0.1"


def test_get_client_ip_uses_x_real_ip_when_present() -> None:
    request = _request_with_headers({"X-Real-Ip": "203.0.113.123"})
    assert get_client_ip(request, lambda _: "127.0.0.1") == "203.0.113.123"


def test_get_client_ip_prefers_forwarded_for_over_x_real_ip() -> None:
    request = _request_with_headers(
        {"X-Forwarded-For": "198.51.100.77", "X-Real-Ip": "203.0.113.123"}
    )
    assert get_client_ip(request, lambda _: "127.0.0.1") == "198.51.100.77"


def test_get_client_ip_accepts_ipv6() -> None:
    request = _request_with_headers({"X-Forwarded-For": "2001:db8::1"})
    assert get_client_ip(request, lambda _: "127.0.0.1") == "2001:db8::1"
