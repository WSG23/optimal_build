"""Helpers for resolving client IPs behind reverse proxies."""

from __future__ import annotations

import ipaddress
from collections.abc import Callable

from fastapi import Request


def get_client_ip(request: Request, fallback: Callable[[Request], str]) -> str:
    """Return a stable client IP when running behind a reverse proxy.

    Cloud Run (and most production deployments) sit behind a proxy that sets
    ``X-Forwarded-For``. Framework helpers often return the proxy IP instead of
    the original client. This helper prefers the first valid IP in the standard
    proxy headers and falls back to the provided callable.
    """

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        candidate = forwarded_for.split(",", 1)[0].strip()
        try:
            ipaddress.ip_address(candidate)
        except ValueError:
            pass
        else:
            return str(candidate)

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        candidate = real_ip.strip()
        try:
            ipaddress.ip_address(candidate)
        except ValueError:
            pass
        else:
            return str(candidate)

    return fallback(request)
