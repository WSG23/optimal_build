"""Seed the database with deterministic fixture data."""

from __future__ import annotations

import asyncio
from datetime import datetime

from app.core.database import AsyncSessionLocal, engine
from app.models import Base
from app.models.rkp import RefDocument, RefRule, RefSource


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        source = RefSource(
            jurisdiction="SG",
            authority="BCA",
            topic="zoning",
            doc_title="Fixture Building Code",
            landing_url="https://example.test/fixture.pdf",
            fetch_kind="pdf",
            update_freq_hint="annual",
            selectors={},
        )
        session.add(source)
        await session.flush()

        document = RefDocument(
            source_id=source.id,
            version_label="v1",
            storage_path="fixtures/fixture.pdf",
            file_hash="fixturehash",
            suspected_update=False,
        )
        session.add(document)
        await session.flush()

        rule = RefRule(
            source_id=source.id,
            document_id=document.id,
            jurisdiction="SG",
            authority="BCA",
            topic="zoning",
            clause_ref="C1",
            parameter_key="buildable.floor_area_ratio",
            operator="<=",
            value="12",
            unit="",
            applicability={"occupancy": ["mixed_use"]},
            exceptions=[],
            source_provenance={"document_id": document.id, "pages": [1]},
            review_status="approved",
            reviewer="Seeder",
            reviewed_at=datetime.utcnow(),
        )
        session.add(rule)
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
