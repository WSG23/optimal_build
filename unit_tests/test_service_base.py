from types import SimpleNamespace

import pytest

from app.services.base import AsyncClientService


class _DummyService(AsyncClientService):
    def __init__(self):
        self.closed = False
        self.client = SimpleNamespace(aclose=self._mark_closed)

    async def _mark_closed(self):
        self.closed = True


@pytest.mark.anyio
async def test_async_client_service_close_invokes_client_aclose():
    service = _DummyService()
    await service.close()
    assert service.closed is True
