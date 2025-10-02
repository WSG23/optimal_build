"""Common service helpers."""

import httpx


class AsyncClientService:
    """Provides shared HTTPX client shutdown logic."""

    client: httpx.AsyncClient

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
