"""HTTP fetcher for SG BCA regulations."""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Iterable, List
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from core.canonical_models import ProvenanceRecord

try:  # Prefer httpx when it is available in the runtime environment.
    import httpx  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - httpx shim always importable in tests
    httpx = None  # type: ignore[assignment]


@dataclass(slots=True)
class FetchConfig:
    """Configuration for the SG BCA fetcher."""

    base_url: str = "https://api.bca.gov.sg"
    username: str = "demo_user"
    password: str = "demo_pass"
    timeout: float = 10.0


class _SimpleResponse:
    def __init__(self, status_code: int, body: bytes, headers: dict[str, str] | None = None):
        self.status_code = status_code
        self._body = body
        self.headers = headers or {}

    def json(self) -> Any:
        if not self._body:
            return None
        return json.loads(self._body.decode("utf-8"))

    @property
    def text(self) -> str:
        return self._body.decode("utf-8")


class _UrllibClient:
    def __init__(self, timeout: float) -> None:
        self._timeout = timeout

    def get(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        auth: tuple[str, str] | None = None,
    ) -> _SimpleResponse:
        if params:
            query = urlencode(params)
            url = f"{url}?{query}"

        request = Request(url)
        if auth:
            token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode("utf-8")).decode("utf-8")
            request.add_header("Authorization", f"Basic {token}")

        with urlopen(request, timeout=self._timeout) as response:  # noqa: S310 - intentional
            body = response.read()
            headers = dict(response.headers.items())
            status_code = getattr(response, "status", 200)

        return _SimpleResponse(status_code=status_code, body=body, headers=headers)

    def close(self) -> None:  # pragma: no cover - nothing to clean up
        return None


class Fetcher:
    """Fetch provenance records from the SG BCA feed."""

    def __init__(
        self,
        config: FetchConfig | None = None,
        client: Any | None = None,
    ) -> None:
        self.config = config or FetchConfig()
        self._client = client

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client

        if httpx is not None and hasattr(httpx, "Client"):
            return httpx.Client(timeout=self.config.timeout)  # type: ignore[attr-defined]

        return _UrllibClient(timeout=self.config.timeout)

    def fetch_raw(self, since: date) -> List[ProvenanceRecord]:
        """Fetch raw provenance records newer than ``since``."""

        client = self._get_client()
        close_client = client is not self._client

        try:
            response = client.get(
                f"{self.config.base_url.rstrip('/')}/regulations",
                params={"updated_after": since.isoformat()},
                auth=(self.config.username, self.config.password),
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            if close_client and hasattr(client, "close"):
                client.close()
            raise RuntimeError("Failed to contact SG BCA feed") from exc

        if close_client and hasattr(client, "close"):
            client.close()

        if response.status_code == 401:
            raise PermissionError("Invalid credentials for SG BCA feed")

        if response.status_code >= 400:
            raise RuntimeError("Unexpected response from SG BCA feed")

        try:
            payload = response.json()
        except ValueError as exc:
            raise ValueError("Malformed payload received from SG BCA feed") from exc

        regulations = payload.get("regulations")
        if not isinstance(regulations, list):
            raise ValueError("Malformed payload: 'regulations' must be a list")

        records: List[ProvenanceRecord] = []
        for entry in regulations:
            if not isinstance(entry, dict):
                raise ValueError("Malformed regulation entry; expected an object")

            try:
                external_id = entry["id"]
            except KeyError as exc:
                raise ValueError("Missing regulation identifier in payload") from exc

            detail_url = entry.get("detail_url")
            if not detail_url:
                detail_url = (
                    f"{self.config.base_url.rstrip('/')}/regulations/{external_id}"
                )

            records.append(
                ProvenanceRecord(
                    regulation_external_id=external_id,
                    source_uri=detail_url,
                    fetched_at=datetime.now(timezone.utc),
                    fetch_parameters={"updated_after": since.isoformat()},
                    raw_content=json.dumps(entry, sort_keys=True),
                )
            )

        return records


def fetch(since: date) -> Iterable[ProvenanceRecord]:
    """Module-level helper to align with the parser interface."""

    return Fetcher().fetch_raw(since)
