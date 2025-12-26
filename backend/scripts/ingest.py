"""Ingestion helpers for the Regstack store.

The root of this repository also contains a `scripts/ingest.py` CLI module.
During tests, `tests/conftest.py` places `backend/` ahead of the project root on
`sys.path`, meaning `import scripts.ingest` resolves to `backend/scripts/ingest`.

The SG BCA jurisdiction tests import `scripts.ingest.upsert_regulations`, so we
provide the minimal implementation here to keep test imports stable.
"""

from __future__ import annotations

import hashlib
import logging
from collections import defaultdict
from collections.abc import Iterable

from sqlalchemy import select

from core import canonical_models

logger = logging.getLogger(__name__)


def upsert_regulations(
    session,
    regulations: Iterable[canonical_models.CanonicalReg],
    provenance_records: list[canonical_models.ProvenanceRecord],
) -> None:
    """Upsert regulations and provenance into the database."""

    provenance_by_ext: dict[str, list[canonical_models.ProvenanceRecord]] = defaultdict(
        list
    )
    for record in provenance_records:
        provenance_by_ext[record.regulation_external_id].append(record)

    for reg in regulations:
        stmt = select(canonical_models.RegulationORM).where(
            canonical_models.RegulationORM.jurisdiction_code == reg.jurisdiction_code,
            canonical_models.RegulationORM.external_id == reg.external_id,
        )
        existing = session.execute(stmt).scalar_one_or_none()
        if existing:
            existing.title = reg.title
            existing.text = reg.text
            existing.issued_on = reg.issued_on
            existing.effective_on = reg.effective_on
            existing.version = reg.version
            existing.metadata_ = reg.metadata
            existing.global_tags = reg.global_tags
        else:
            existing = canonical_models.RegulationORM(
                jurisdiction_code=reg.jurisdiction_code,
                external_id=reg.external_id,
                title=reg.title,
                text=reg.text,
                issued_on=reg.issued_on,
                effective_on=reg.effective_on,
                version=reg.version,
                metadata_=reg.metadata,
                global_tags=reg.global_tags,
            )
            session.add(existing)
            session.flush()

        for provenance in provenance_by_ext.get(reg.external_id, []):
            content_checksum = hashlib.sha256(
                provenance.raw_content.encode("utf-8")
            ).hexdigest()
            matched_provenance = session.execute(
                select(canonical_models.ProvenanceORM).where(
                    canonical_models.ProvenanceORM.regulation_id == existing.id,
                    canonical_models.ProvenanceORM.source_uri == provenance.source_uri,
                    canonical_models.ProvenanceORM.content_checksum == content_checksum,
                )
            ).scalar_one_or_none()

            if matched_provenance:
                if matched_provenance.fetched_at != provenance.fetched_at:
                    matched_provenance.fetched_at = provenance.fetched_at
                if matched_provenance.fetch_parameters != provenance.fetch_parameters:
                    matched_provenance.fetch_parameters = provenance.fetch_parameters
                if matched_provenance.raw_content != provenance.raw_content:
                    matched_provenance.raw_content = provenance.raw_content
                continue

            latest_provenance = (
                session.execute(
                    select(canonical_models.ProvenanceORM)
                    .where(
                        canonical_models.ProvenanceORM.regulation_id == existing.id,
                        canonical_models.ProvenanceORM.source_uri
                        == provenance.source_uri,
                    )
                    .order_by(canonical_models.ProvenanceORM.fetched_at.desc())
                )
                .scalars()
                .first()
            )

            previous_checksum = (
                latest_provenance.content_checksum
                if latest_provenance is not None
                else None
            )
            if previous_checksum == content_checksum:
                continue

            session.add(
                canonical_models.ProvenanceORM(
                    regulation_id=existing.id,
                    source_uri=provenance.source_uri,
                    fetched_at=provenance.fetched_at,
                    fetch_parameters=provenance.fetch_parameters,
                    raw_content=provenance.raw_content,
                    content_checksum=content_checksum,
                )
            )
