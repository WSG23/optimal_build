"""Regression tests for reference seed data bootstrap."""

from __future__ import annotations

import importlib

import pytest

from app.models.base import BaseModel
from app.models.property import Property, PropertyType

seed_finance_demo = importlib.import_module("backend.scripts.seed_finance_demo")
seed_properties_projects = importlib.import_module(
    "backend.scripts.seed_properties_projects"
)


def test_property_seed_uses_valid_space_needle_property_type() -> None:
    space_needle = next(
        item
        for item in seed_properties_projects._PROPERTIES
        if item["name"] == "Space Needle"
    )

    assert space_needle["property_type"] is PropertyType.SPECIAL_PURPOSE
    assert all(
        isinstance(item["property_type"], PropertyType)
        for item in seed_properties_projects._PROPERTIES
    )


@pytest.mark.asyncio
async def test_finance_seed_loads_model_registry_before_creating_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []

    class FakeConnection:
        async def __aenter__(self) -> "FakeConnection":
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        async def run_sync(self, fn: object) -> None:
            calls.append(fn)

    class FakeEngine:
        def begin(self) -> FakeConnection:
            return FakeConnection()

    monkeypatch.setattr(
        seed_finance_demo, "load_model_modules", lambda: calls.append("models-loaded")
    )
    monkeypatch.setattr(seed_finance_demo, "engine", FakeEngine())

    await seed_finance_demo.ensure_schema()

    assert calls == ["models-loaded", BaseModel.metadata.create_all]


@pytest.mark.asyncio
async def test_property_seed_loads_model_registry_before_creating_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []

    class FakeConnection:
        async def __aenter__(self) -> "FakeConnection":
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        async def run_sync(self, fn: object) -> None:
            calls.append(fn)

    class FakeEngine:
        def begin(self) -> FakeConnection:
            return FakeConnection()

    class FakeSession:
        async def __aenter__(self) -> "FakeSession":
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

    async def fake_seed_properties_and_projects(
        session: FakeSession,
        *,
        reset_existing: bool,
    ) -> seed_properties_projects.SeedSummary:
        calls.append(("seeded", session, reset_existing))
        return seed_properties_projects.SeedSummary(projects=0, properties=0)

    monkeypatch.setattr(
        seed_properties_projects,
        "load_model_modules",
        lambda: calls.append("models-loaded"),
    )
    monkeypatch.setattr(seed_properties_projects, "engine", FakeEngine())
    monkeypatch.setattr(seed_properties_projects, "AsyncSessionLocal", FakeSession)
    monkeypatch.setattr(
        seed_properties_projects,
        "seed_properties_and_projects",
        fake_seed_properties_and_projects,
    )

    summary = await seed_properties_projects._run_async(reset_existing=True)

    assert summary == seed_properties_projects.SeedSummary(projects=0, properties=0)
    assert calls[0:2] == ["models-loaded", Property.metadata.create_all]
    assert calls[2][0] == "seeded"
    assert calls[2][2] is True
