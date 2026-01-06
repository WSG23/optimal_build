"""Common service helpers."""

import httpx


class AsyncClientService:
    """Provides shared HTTPX client shutdown logic."""

    client: httpx.AsyncClient | None

    async def close(self) -> None:
        """Close the HTTP client."""
        if self.client is not None:
            await self.client.aclose()
