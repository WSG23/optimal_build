#!/usr/bin/env python3
"""Verify Google Maps API setup end-to-end.

Tests each enabled API against the configured GOOGLE_MAPS_API_KEY and
reports specific failure modes (key invalid, API not enabled, billing
not active, restriction blocking) so you can fix the right thing.

Usage:
    python3 scripts/verify_google_maps_setup.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _scan_env_file(path: Path, *keys: str) -> str | None:
    if not path.exists():
        return None
    for line in path.read_text().splitlines():
        line = line.strip()
        for key in keys:
            if line.startswith(f"{key}="):
                value = line.split("=", 1)[1].strip().strip("'\"")
                return value or None
    return None


def load_api_key() -> str | None:
    """Read the Maps key from any of the typical locations.

    Order: root .env (backend), then frontend/.env (Vite), then env var.
    Vite reads VITE_GOOGLE_MAPS_API_KEY; the backend reads GOOGLE_MAPS_API_KEY.
    Either is fine for verification purposes — same key, same restrictions.
    """
    return (
        _scan_env_file(REPO_ROOT / ".env", "GOOGLE_MAPS_API_KEY")
        or _scan_env_file(
            REPO_ROOT / "frontend" / ".env",
            "VITE_GOOGLE_MAPS_API_KEY",
            "GOOGLE_MAPS_API_KEY",
        )
        or os.environ.get("GOOGLE_MAPS_API_KEY")
    )


def fetch(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"_http_error": e.code, "_body": e.read().decode("utf-8", "ignore")}
    except Exception as e:
        return {"_error": str(e)}


def diagnose(name: str, result: dict) -> tuple[bool, str]:
    """Return (passed, message) for a result dict."""
    if "_error" in result:
        return False, f"network error: {result['_error']}"
    if "_http_error" in result:
        return False, f"HTTP {result['_http_error']}: {result['_body'][:200]}"
    status = result.get("status", "")
    if status == "OK":
        return True, "OK"
    msg = result.get("error_message", "(no error_message)")
    fix_hints = {
        "REQUEST_DENIED": (
            "  → If 'API key not valid': key is wrong/typo in .env\n"
            "  → If 'API not enabled': enable the API in GCP Console\n"
            "  → If 'restricted': check Application restrictions (referrer/IP)\n"
            "  → If 'billing': link billing account to the project"
        ),
        "OVER_QUERY_LIMIT": "  → daily quota hit OR billing not active",
        "INVALID_REQUEST": "  → request was malformed (test script bug?)",
        "ZERO_RESULTS": "  → API works but query returned nothing (still a pass)",
    }
    hint = fix_hints.get(status, "")
    return status == "ZERO_RESULTS", f"{status}: {msg}\n{hint}"


def test_geocoding(key: str) -> tuple[bool, str]:
    url = "https://maps.googleapis.com/maps/api/geocode/json?" + urllib.parse.urlencode(
        {"address": "1 Marina Bay, Singapore", "key": key}
    )
    return diagnose("Geocoding API", fetch(url))


def test_places(key: str) -> tuple[bool, str]:
    """Test Places API (New) — the autocomplete:places endpoint.

    The frontend uses PlaceAutocompleteElement which hits this v1 endpoint.
    Returns OK if the response is 200 with a `suggestions` array (even an
    empty one); otherwise extracts the error for diagnosis.
    """
    url = "https://places.googleapis.com/v1/places:autocomplete"
    body = json.dumps({"input": "Marina Bay", "regionCode": "SG"}).encode()
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            if "suggestions" in data:
                return True, "OK (Places API New)"
            return False, f"unexpected response: {str(data)[:200]}"
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read())
            msg = err.get("error", {}).get("message", "(no message)")
            status = err.get("error", {}).get("status", "ERROR")
        except Exception:
            msg, status = "(no body)", str(e.code)
        hint = (
            "  → If 'API has not been used': enable 'Places API (New)' in GCP\n"
            "  → If 'API_KEY_INVALID': check key in .env\n"
            "  → If 'API restriction': add 'Places API (New)' to key restrictions\n"
            "  → If billing: link billing account"
        )
        return False, f"{status}: {msg}\n{hint}"
    except Exception as e:
        return False, f"network error: {e}"


def test_maps_js(key: str) -> tuple[bool, str]:
    """Maps JS loader doesn't return JSON; we just confirm it serves JS."""
    url = f"https://maps.googleapis.com/maps/api/js?key={key}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            body = resp.read().decode("utf-8", "ignore")
            if "InvalidKey" in body or "ApiNotActivated" in body:
                return False, (
                    "Maps JS API returned an error in the JS body. "
                    "Check API enablement and key restrictions."
                )
            if "google.maps" in body or "google.load" in body or len(body) > 1000:
                return True, "OK (JS bootstrapper served)"
            return False, f"unexpected response: {body[:200]}"
    except Exception as e:
        return False, f"network error: {e}"


def main() -> int:
    key = load_api_key()
    if not key:
        print("✗ GOOGLE_MAPS_API_KEY not set in .env or environment")
        return 2

    print(f"Testing key ending in ...{key[-6:]}\n")

    tests = [
        ("Geocoding API   ", test_geocoding),
        ("Places API      ", test_places),
        ("Maps JS API     ", test_maps_js),
    ]

    failures = 0
    for name, fn in tests:
        passed, msg = fn(key)
        status = "✓" if passed else "✗"
        print(f"{status} {name}: {msg}\n")
        if not passed:
            failures += 1

    if failures:
        print(f"\n{failures} of {len(tests)} APIs failed. Fix per hints above.")
        return 1
    print(f"\nAll {len(tests)} Maps APIs working. Setup complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
