"""Shared HTTP fetchers for jurisdiction data sources.

Provides small adapters for CKAN (data.gov style) and Socrata/SODA APIs so
jurisdictions can reuse the same retry/backoff/rate-limit logic.  These are
intentionally lightweight and dependency-free beyond httpx.
"""

from __future__ import annotations

import os
import time
from collections.abc import MutableMapping
from dataclasses import dataclass
from datetime import date, datetime, time as time_module
from typing import Any

import httpx
import structlog
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.get_logger(__name__)


class FetcherError(RuntimeError):
    """Raised when a fetcher cannot retrieve or process data."""


@dataclass(slots=True)
class BaseFetchConfig:
    base_url: str
    timeout: float = 30.0
    max_retries: int = 3
    backoff_factor: float = 0.5
    rate_limit_per_minute: int | None = None
    user_agent: str = "optimal-build/fetcher"


@dataclass(slots=True)
class CKANConfig(BaseFetchConfig):
    resource_id: str | None = None
    api_key: str | None = None
    api_key_header: str = "api-key"
    page_size: int = 100
    date_field: str | None = None

    @classmethod
    def from_env(cls, prefix: str = "CKAN") -> CKANConfig:
        env = os.environ
        resource_id = env.get(f"{prefix}_RESOURCE_ID")
        if not resource_id:
            raise FetcherError(f"Missing {prefix}_RESOURCE_ID environment variable.")

        return cls(
            base_url=env.get(
                f"{prefix}_BASE_URL", "https://data.gov.sg/api/action/datastore_search"
            ),
            resource_id=resource_id,
            api_key=env.get(f"{prefix}_API_KEY"),
            api_key_header=env.get(f"{prefix}_API_KEY_HEADER", "api-key"),
            page_size=int(env.get(f"{prefix}_PAGE_SIZE", 100)),
            timeout=float(env.get(f"{prefix}_TIMEOUT", 10.0)),
            max_retries=int(env.get(f"{prefix}_MAX_RETRIES", 3)),
            backoff_factor=float(env.get(f"{prefix}_BACKOFF_FACTOR", 0.5)),
            rate_limit_per_minute=(
                int(rate)
                if (rate := env.get(f"{prefix}_RATE_LIMIT_PER_MINUTE"))
                else None
            ),
            user_agent=env.get(f"{prefix}_USER_AGENT", "optimal-build/ckan-fetcher"),
            date_field=env.get(f"{prefix}_DATE_FIELD"),
        )


@dataclass(slots=True)
class SodaConfig(BaseFetchConfig):
    dataset_id: str | None = None
    app_token: str | None = None
    page_size: int = 5000

    @classmethod
    def from_env(cls, prefix: str = "SODA") -> SodaConfig:
        env = os.environ
        dataset_id = env.get(f"{prefix}_DATASET_ID")
        if not dataset_id:
            raise FetcherError(f"Missing {prefix}_DATASET_ID environment variable.")

        return cls(
            base_url=env.get(f"{prefix}_BASE_URL", "https://data.seattle.gov/resource"),
            dataset_id=dataset_id,
            app_token=env.get(f"{prefix}_APP_TOKEN"),
            page_size=int(env.get(f"{prefix}_PAGE_SIZE", 5000)),
            timeout=float(env.get(f"{prefix}_TIMEOUT", 60.0)),
            max_retries=int(env.get(f"{prefix}_MAX_RETRIES", 3)),
            backoff_factor=float(env.get(f"{prefix}_BACKOFF_FACTOR", 0.5)),
            rate_limit_per_minute=(
                int(rate)
                if (rate := env.get(f"{prefix}_RATE_LIMIT_PER_MINUTE"))
                else None
            ),
            user_agent=env.get(f"{prefix}_USER_AGENT", "optimal-build/soda-fetcher"),
        )


class BaseFetcher:
    def __init__(
        self,
        config: BaseFetchConfig,
        *,
        transport: httpx.BaseTransport | None = None,
        logger: BoundLogger | None = None,
    ) -> None:
        self.config = config
        self._transport = transport
        self._logger = logger or LOGGER
        self._last_request: float | None = None

    def _enforce_rate_limit(self) -> None:
        if not self.config.rate_limit_per_minute:
            return
        minimum_interval = 60.0 / float(self.config.rate_limit_per_minute)
        if self._last_request is None:
            return
        elapsed = time.time() - self._last_request
        if elapsed < minimum_interval:
            time.sleep(minimum_interval - elapsed)

    def _request_with_retry(
        self,
        client: httpx.Client,
        url: str,
        params: MutableMapping[str, object],
        headers: MutableMapping[str, str] | None = None,
    ) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(1, self.config.max_retries + 1):
            try:
                self._enforce_rate_limit()
                response = client.get(url, params=params, headers=headers)
                self._last_request = time.time()
                response.raise_for_status()
                return response
            except Exception as exc:  # pragma: no cover - httpx error types vary
                last_exc = exc
                wait_time = self.config.backoff_factor * (2 ** (attempt - 1))
                self._logger.warning(
                    "fetch.retry",
                    attempt=attempt,
                    wait=wait_time,
                    error=str(exc),
                )
                if attempt == self.config.max_retries:
                    break
                if wait_time > 0:
                    time.sleep(wait_time)
        raise FetcherError(str(last_exc) if last_exc else "unknown fetch error")


class CKANFetcher(BaseFetcher):
    def __init__(
        self,
        config: CKANConfig,
        *,
        transport: httpx.BaseTransport | None = None,
        logger: BoundLogger | None = None,
    ) -> None:
        if not config.resource_id:
            raise FetcherError("CKANFetcher requires a resource_id.")
        super().__init__(config, transport=transport, logger=logger)
        self._config = config

    def _create_client(self) -> httpx.Client:
        headers = {"User-Agent": self._config.user_agent}
        if self._config.api_key and self._config.api_key_header:
            headers[self._config.api_key_header] = self._config.api_key
        return httpx.Client(
            base_url=self._config.base_url,
            headers=headers,
            timeout=self._config.timeout,
            transport=self._transport,
        )

    def fetch_records(
        self,
        *,
        since: date | datetime | None = None,
        since_field: str | None = None,
    ) -> list[dict[str, Any]]:
        since_dt: datetime | None = None
        if since:
            if isinstance(since, datetime):
                since_dt = since
            else:
                since_dt = datetime.combine(since, time_module.min)

        if since_dt and since_dt.tzinfo is not None:
            since_dt = since_dt.replace(tzinfo=None)

        if since_dt and not since_field:
            since_field = self._config.date_field

        records: list[dict[str, Any]] = []
        with self._create_client() as client:
            offset = 0
            while True:
                params: MutableMapping[str, object] = {
                    "resource_id": self._config.resource_id,
                    "limit": self._config.page_size,
                    "offset": offset,
                }
                response = self._request_with_retry(client, "", params, None)
                payload = response.json()
                result = payload.get("result") or {}
                page_records = result.get("records") or []
                if since_dt and since_field:
                    filtered = []
                    for row in page_records:
                        value = row.get(since_field)
                        try:
                            candidate = datetime.fromisoformat(str(value))
                        except Exception:
                            continue
                        if candidate.tzinfo is not None:
                            candidate = candidate.replace(tzinfo=None)
                        if candidate >= since_dt:
                            filtered.append(row)
                    page_records = filtered
                if not page_records:
                    break
                records.extend(page_records)
                if len(page_records) < self._config.page_size:
                    break
                offset += self._config.page_size
        self._logger.info(
            "ckan.fetch.complete",
            records=len(records),
            resource_id=self._config.resource_id,
        )
        return records


class SODAFetcher(BaseFetcher):
    def __init__(
        self,
        config: SodaConfig,
        *,
        transport: httpx.BaseTransport | None = None,
        logger: BoundLogger | None = None,
    ) -> None:
        if not config.dataset_id:
            raise FetcherError("SODAFetcher requires a dataset_id.")
        super().__init__(config, transport=transport, logger=logger)
        self._config = config

    def _create_client(self) -> httpx.Client:
        headers = {"User-Agent": self._config.user_agent}
        if self._config.app_token and self._config.app_token != "public":
            headers["X-App-Token"] = self._config.app_token
        return httpx.Client(
            base_url=self._config.base_url,
            headers=headers,
            timeout=self._config.timeout,
            transport=self._transport,
        )

    def fetch_geojson(
        self,
        *,
        where: str | None = None,
        max_features: int | None = None,
    ) -> dict[str, Any]:
        remaining = max_features
        features: list[dict[str, Any]] = []

        with self._create_client() as client:
            offset = 0
            while True:
                limit = self._config.page_size
                if remaining is not None:
                    limit = min(limit, remaining)
                params: MutableMapping[str, object] = {
                    "$format": "geojson",
                    "$limit": str(limit),
                    "$offset": str(offset),
                }
                if where:
                    params["$where"] = where

                response = self._request_with_retry(
                    client,
                    f"{self._config.dataset_id}.geojson",
                    params,
                    None,
                )
                payload = response.json()
                page_features = payload.get("features", [])
                if not page_features:
                    break

                features.extend(page_features)
                offset += limit

                if remaining is not None:
                    remaining -= len(page_features)
                    if remaining <= 0:
                        break
                if len(page_features) < limit:
                    break

        self._logger.info(
            "soda.fetch.complete",
            features=len(features),
            dataset_id=self._config.dataset_id,
        )
        return {"type": "FeatureCollection", "features": features}
