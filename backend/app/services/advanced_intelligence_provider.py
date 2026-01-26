"""Provider client for advanced intelligence analytics."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class AdvancedIntelligenceProviderError(RuntimeError):
    """Raised when the advanced intelligence provider cannot be reached."""


class AdvancedIntelligenceProvider:
    """HTTP client for the configured analytics provider."""

    def __init__(self, base_url: str, api_key: str | None, timeout_seconds: float):
        if not base_url:
            raise AdvancedIntelligenceProviderError(
                "Advanced intelligence provider is not configured."
            )
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or None
        self.timeout = timeout_seconds

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=self._headers(),
                )
        except httpx.RequestError as exc:
            logger.error(
                "advanced_intelligence.request_failed", error=str(exc), url=url
            )
            raise AdvancedIntelligenceProviderError(
                "Advanced intelligence provider is unreachable."
            ) from exc

        if response.status_code == 404:
            return {"status": "empty"}
        if response.status_code >= 400:
            logger.error(
                "advanced_intelligence.provider_error",
                status_code=response.status_code,
                body=response.text[:200],
            )
            raise AdvancedIntelligenceProviderError(
                f"Advanced intelligence provider error ({response.status_code})."
            )

        try:
            return response.json()
        except ValueError as exc:
            logger.error("advanced_intelligence.invalid_json", url=url)
            raise AdvancedIntelligenceProviderError(
                "Advanced intelligence provider returned invalid JSON."
            ) from exc

    async def fetch_graph(self, workspace_id: str) -> dict[str, Any]:
        return await self._get("graph", {"workspaceId": workspace_id})

    async def fetch_predictive(
        self, workspace_id: str, query: str | None = None
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"workspaceId": workspace_id}
        if query:
            params["query"] = query
        return await self._get("predictive", params)

    async def fetch_correlation(self, workspace_id: str) -> dict[str, Any]:
        return await self._get("cross-correlation", {"workspaceId": workspace_id})


def get_advanced_intelligence_provider() -> AdvancedIntelligenceProvider:
    """Construct provider client from settings."""

    return AdvancedIntelligenceProvider(
        base_url=settings.ADV_INTELLIGENCE_BASE_URL,
        api_key=settings.ADV_INTELLIGENCE_API_KEY,
        timeout_seconds=settings.ADV_INTELLIGENCE_TIMEOUT_SECONDS,
    )
