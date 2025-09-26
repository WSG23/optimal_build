"""HTTP fetcher for the Singapore BCA circular feed.

The Building and Construction Authority (BCA) publishes circulars through the
Singapore ``data.gov.sg`` CKAN API.  This module downloads the upstream payload,
converts it into :class:`~core.canonical_models.ProvenanceRecord` instances, and
exposes a small amount of operational configuration that can be driven via
environment variables.  See ``README.md`` in this package for deployment
guidance.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
import json
import os
import time as time_module
from typing import Iterable, List, MutableMapping, Sequence

import httpx
import structlog
from structlog.stdlib import BoundLogger

from core.canonical_models import ProvenanceRecord

LOGGER: BoundLogger = structlog.get_logger(__name__)


class FetchError(RuntimeError):
    """Raised when the SG BCA fetcher cannot retrieve data from upstream."""


@dataclass(slots=True)
class FetchConfig:
    """Configuration for the SG BCA fetcher.

    The defaults target the public ``data.gov.sg`` datastore API.  The resource
    identifier is not bundled with the source because it changes over time and
    frequently requires credentials.  Use ``from_env`` to build a configuration
    from the process environment.
    """

    base_url: str = "https://data.gov.sg/api/action/datastore_search"
    resource_id: str | None = None
    api_key: str | None = None
    api_key_header: str = "api-key"
    page_size: int = 100
    timeout: float = 10.0
    max_retries: int = 3
    backoff_factor: float = 0.5
    rate_limit_per_minute: int | None = None
    date_field: str = "circular_date"
    external_id_field: str = "circular_no"

    @classmethod
    def from_env(cls) -> "FetchConfig":
        """Instantiate configuration using well-known environment variables."""

        env = os.environ
        resource_id = env.get("SG_BCA_DATASTORE_RESOURCE_ID")
        if not resource_id:
            raise FetchError(
                "Missing SG_BCA_DATASTORE_RESOURCE_ID environment variable."
            )

        config = cls(
            base_url=env.get("SG_BCA_BASE_URL", cls.base_url),
            resource_id=resource_id,
            api_key=env.get("SG_BCA_API_KEY"),
            api_key_header=env.get("SG_BCA_API_KEY_HEADER", cls.api_key_header),
            page_size=int(env.get("SG_BCA_PAGE_SIZE", cls.page_size)),
            timeout=float(env.get("SG_BCA_TIMEOUT", cls.timeout)),
            max_retries=int(env.get("SG_BCA_MAX_RETRIES", cls.max_retries)),
            backoff_factor=float(env.get("SG_BCA_BACKOFF_FACTOR", cls.backoff_factor)),
            rate_limit_per_minute=(
                int(rate)
                if (rate := env.get("SG_BCA_RATE_LIMIT_PER_MINUTE"))
                else None
            ),
            date_field=env.get("SG_BCA_DATE_FIELD", cls.date_field),
            external_id_field=env.get(
                "SG_BCA_EXTERNAL_ID_FIELD", cls.external_id_field
            ),
        )
        return config


class Fetcher:
    """Download circular metadata from BCA and convert to provenance records."""

    def __init__(
        self,
        config: FetchConfig | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
        logger: BoundLogger | None = None,
    ) -> None:
        self.config = config or FetchConfig.from_env()
        self._transport = transport
        self._logger = logger or LOGGER
        self._last_request: float | None = None

    def fetch_raw(self, since: date) -> List[ProvenanceRecord]:
        """Fetch all records newer than ``since`` from the configured API."""

        if not self.config.resource_id:
            raise FetchError("SG BCA fetcher configured without a resource id")

        since_dt = datetime.combine(since, time.min)
        records: List[ProvenanceRecord] = []

        self._logger.info(
            "sg_bca.fetch.start", since=since.isoformat(), resource=self.config.resource_id
        )

        with self._create_client() as client:
            offset = 0
            total: int | None = None
            while True:
                params = {
                    "resource_id": self.config.resource_id,
                    "limit": self.config.page_size,
                    "offset": offset,
                }
                payload = self._request_with_retry(client, params)
                rows, page_total = self._extract_rows(payload.get("result"), offset)
                if total is None:
                    total = page_total

                if not rows:
                    break

                for row in rows:
                    record = self._normalise_row(row)
                    if not record:
                        continue
                    if record["issued_at"] and record["issued_at"] < since_dt:
                        continue
                    records.append(self._to_provenance(row, record, since))

                offset += self.config.page_size
                if total is not None and offset >= int(total):
                    break

        self._logger.info("sg_bca.fetch.complete", count=len(records))
        return records

    # ------------------------------------------------------------------
    def _create_client(self) -> httpx.Client:
        headers = {"User-Agent": "optimal-build/sg-bca-fetcher"}
        if self.config.api_key and self.config.api_key_header:
            headers[self.config.api_key_header] = self.config.api_key
        return httpx.Client(
            base_url=self.config.base_url,
            headers=headers,
            timeout=self.config.timeout,
            transport=self._transport,
        )

    def _request_with_retry(
        self, client: httpx.Client, params: MutableMapping[str, object]
    ) -> dict:
        last_exc: Exception | None = None
        for attempt in range(1, self.config.max_retries + 1):
            try:
                self._enforce_rate_limit()
                response = client.get("", params=params)
                response.raise_for_status()
                payload = response.json()
                self._logger.debug(
                    "sg_bca.fetch.page",
                    attempt=attempt,
                    offset=params["offset"],
                    received=len((payload.get("result") or {}).get("records", [])),
                )
                return payload
            except Exception as exc:  # pragma: no cover - exception branch
                last_exc = exc
                wait_time = self.config.backoff_factor * (2 ** (attempt - 1))
                self._logger.warning(
                    "sg_bca.fetch.retry",
                    attempt=attempt,
                    wait=wait_time,
                    error=str(exc),
                )
                if attempt == self.config.max_retries:
                    break
                if wait_time > 0:
                    time_module.sleep(wait_time)

        raise FetchError("Failed to fetch SG BCA data") from last_exc

    def _enforce_rate_limit(self) -> None:
        if not self.config.rate_limit_per_minute:
            return
        min_interval = 60.0 / self.config.rate_limit_per_minute
        now = time_module.monotonic()
        if self._last_request is not None:
            sleep_for = min_interval - (now - self._last_request)
            if sleep_for > 0:
                time_module.sleep(sleep_for)
        self._last_request = time_module.monotonic()

    def _extract_rows(
        self,
        result: MutableMapping[str, object] | None,
        offset: int,
    ) -> tuple[list[MutableMapping[str, object]], int | None]:
        if result is None or not isinstance(result, MutableMapping):
            raise FetchError("SG BCA payload missing 'result' object")

        raw_rows = result.get("records")
        if raw_rows in (None, []):
            return [], self._coerce_total(result.get("total"))
        if not isinstance(raw_rows, Sequence):
            raise FetchError("SG BCA payload 'records' must be a sequence")

        rows: list[MutableMapping[str, object]] = []
        for index, row in enumerate(raw_rows):
            if not isinstance(row, MutableMapping):
                raise FetchError(
                    "SG BCA payload row at offset "
                    f"{offset + index} is not a JSON object"
                )
            rows.append(row)

        return rows, self._coerce_total(result.get("total"))

    def _coerce_total(self, value: object) -> int | None:
        if value is None:
            return None
        try:
            total = int(value)
        except (TypeError, ValueError):
            self._logger.warning("sg_bca.fetch.invalid_total", raw=value)
            return None
        return max(total, 0)

    def _normalise_row(
        self, row: MutableMapping[str, object]
    ) -> dict[str, datetime | str | None]:
        issued_raw = self._coerce_str(row.get(self.config.date_field))
        issued_at = self._parse_datetime(issued_raw)
        external_id = self._coerce_str(row.get(self.config.external_id_field))
        if not external_id:
            self._logger.warning(
                "sg_bca.fetch.row_missing_external_id", row=row
            )
            return {}
        return {"issued_at": issued_at, "external_id": external_id}

    def _to_provenance(
        self,
        row: MutableMapping[str, object],
        normalised: dict[str, datetime | str | None],
        since: date,
    ) -> ProvenanceRecord:
        source_uri = self._coerce_str(row.get("weblink")) or self.config.base_url
        return ProvenanceRecord(
            regulation_external_id=str(normalised["external_id"]),
            source_uri=source_uri,
            fetched_at=datetime.now(timezone.utc),
            fetch_parameters={
                "since": since.isoformat(),
                "resource_id": self.config.resource_id,
            },
            raw_content=json.dumps(row, sort_keys=True, ensure_ascii=False),
        )

    @staticmethod
    def _coerce_str(value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return str(value)

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        normalised = value.replace("Z", "")
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(normalised, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(normalised)
        except ValueError:
            LOGGER.warning("sg_bca.fetch.unparsed_date", raw=value)
            return None


def fetch(since: date) -> Iterable[ProvenanceRecord]:
    """Module-level helper to align with the parser interface."""

    return Fetcher().fetch_raw(since)
