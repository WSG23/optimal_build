"""CLI entry point for ingesting jurisdiction regulations."""
from __future__ import annotations

import argparse
import hashlib
import logging
from datetime import date
from typing import Iterable, List

from sqlalchemy import select

from core import canonical_models
from core.mapping import load_and_apply_mappings
from core.registry import JurisdictionParser, RegistryError, load_jurisdiction
from core.util import create_session_factory, get_engine, session_scope


logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Regstack ingestion CLI")
    parser.add_argument(
        "--jurisdiction",
        required=True,
        help="Jurisdiction code to ingest",
    )
    parser.add_argument(
        "--since",
        required=True,
        help="ISO date threshold for fetching regulations",
    )
    parser.add_argument(
        "--store",
        required=True,
        help="Database URL compatible with SQLAlchemy",
    )
    parser.add_argument(
        "--echo-sql",
        action="store_true",
        help="Echo SQL emitted during ingestion",
    )
    return parser.parse_args()


def ensure_jurisdiction(session, parser: JurisdictionParser) -> None:
    """Ensure the jurisdiction exists in the database."""

    stmt = select(canonical_models.JurisdictionORM).where(
        canonical_models.JurisdictionORM.code == parser.code
    )
    if not session.execute(stmt).scalar_one_or_none():
        session.add(
            canonical_models.JurisdictionORM(
                code=parser.code,
                name=getattr(parser, "display_name", parser.code.upper()),
            )
        )


def upsert_regulations(
    session,
    regulations: Iterable[canonical_models.CanonicalReg],
    provenance_records: List[canonical_models.ProvenanceRecord],
) -> None:
    """Upsert regulations and provenance into the database."""

    provenance_by_ext = {
        record.regulation_external_id: record for record in provenance_records
    }

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

        provenance = provenance_by_ext.get(reg.external_id)
        if provenance:
            content_checksum = hashlib.sha256(
                provenance.raw_content.encode("utf-8")
            ).hexdigest()
            prov_stmt = select(canonical_models.ProvenanceORM).where(
                canonical_models.ProvenanceORM.regulation_id == existing.id,
                canonical_models.ProvenanceORM.source_uri == provenance.source_uri,
                canonical_models.ProvenanceORM.content_checksum == content_checksum,
            )
            existing_provenance = session.execute(prov_stmt).scalar_one_or_none()
            if existing_provenance:
                updated_fields = []
                if existing_provenance.fetched_at != provenance.fetched_at:
                    existing_provenance.fetched_at = provenance.fetched_at
                    updated_fields.append("fetched_at")
                if (
                    existing_provenance.fetch_parameters
                    != provenance.fetch_parameters
                ):
                    existing_provenance.fetch_parameters = (
                        provenance.fetch_parameters
                    )
                    updated_fields.append("fetch_parameters")
                if existing_provenance.raw_content != provenance.raw_content:
                    existing_provenance.raw_content = provenance.raw_content
                    updated_fields.append("raw_content")

                if updated_fields:
                    logger.info(
                        "Updated provenance record for %s (source=%s; fields=%s)",
                        reg.external_id,
                        provenance.source_uri,
                        ", ".join(updated_fields),
                    )
                else:
                    logger.info(
                        "Skipped provenance record for %s (source=%s); no changes detected",
                        reg.external_id,
                        provenance.source_uri,
                    )
            else:
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
                logger.info(
                    "Inserted provenance record for %s (source=%s)",
                    reg.external_id,
                    provenance.source_uri,
                )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    try:
        since = date.fromisoformat(args.since)
    except ValueError as exc:  # pragma: no cover - CLI validation
        raise SystemExit(f"Invalid --since date: {args.since}") from exc

    engine = get_engine(args.store, echo=args.echo_sql)
    session_factory = create_session_factory(engine)

    try:
        registered = load_jurisdiction(args.jurisdiction)
    except RegistryError as exc:  # pragma: no cover - CLI validation
        raise SystemExit(str(exc)) from exc

    parser = registered.parser
    provenance_records = list(parser.fetch_raw(since))
    regulations = list(parser.parse(provenance_records))
    regulations = load_and_apply_mappings(
        regulations,
        parser.map_overrides_path(),
    )

    with session_scope(session_factory) as session:
        ensure_jurisdiction(session, parser)
        upsert_regulations(session, regulations, provenance_records)

    print(  # pragma: no cover - CLI feedback
        f"Ingested {len(regulations)} regulations for jurisdiction {parser.code}"
    )


if __name__ == "__main__":  # pragma: no cover - CLI execution guard
    main()
