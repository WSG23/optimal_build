import asyncio

import pytest

from app.utils.cache import TTLCache


@pytest.mark.asyncio
async def test_ttl_cache_returns_independent_copies():
    cache = TTLCache(ttl_seconds=5, copy=lambda value: list(value))
    await cache.set("numbers", [1, 2])

    first = await cache.get("numbers")
    assert first == [1, 2]

    first.append(3)
    second = await cache.get("numbers")
    assert second == [1, 2]


@pytest.mark.asyncio
async def test_ttl_cache_expires_entries():
    cache = TTLCache(ttl_seconds=0.05)
    await cache.set("token", "abc")

    assert await cache.get("token") == "abc"

    await asyncio.sleep(0.06)
    assert await cache.get("token") is None
