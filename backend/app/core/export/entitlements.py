"""Entitlements export helpers."""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable
from datetime import datetime
from enum import Enum

from backend._compat import compat_dataclass
from backend._compat.datetime import UTC

from app.services.entitlements import EntitlementsService
from app.utils.render import render_html_to_pdf
from sqlalchemy.ext.asyncio import AsyncSession

EXPORT_PAGE_SIZE = 200


class EntitlementsExportFormat(str, Enum):
    """Supported entitlement export formats."""

    CSV = "csv"
    HTML = "html"
    PDF = "pdf"

    @property
    def media_type(self) -> str:
        return {
            EntitlementsExportFormat.CSV: "text/csv",
            EntitlementsExportFormat.HTML: "text/html",
            EntitlementsExportFormat.PDF: "application/pdf",
        }[self]


@compat_dataclass(slots=True)
class EntitlementsSnapshot:
    """Serialised snapshot used for exports."""

    project_id: int
    roadmap: list[dict[str, object]]
    studies: list[dict[str, object]]
    engagements: list[dict[str, object]]
    legal: list[dict[str, object]]
    generated_at: datetime


async def _collect_all(
    fetch_page,
    *,
    page_size: int = EXPORT_PAGE_SIZE,
) -> list:
    records: list = []
    offset = 0
    while True:
        page = await fetch_page(limit=page_size, offset=offset)
        records.extend(page.items)
        offset += page_size
        if offset >= page.total:
            break
        if not page.items:
            break
    return records


def _serialise_roadmap(records) -> list[dict[str, object]]:
    serialised: list[dict[str, object]] = []
    for item in records:
        serialised.append(
            {
                "sequence": item.sequence_order,
                "status": (
                    item.status.value
                    if hasattr(item.status, "value")
                    else str(item.status)
                ),
                "approval_type_id": item.approval_type_id,
                "target_submission": (
                    item.target_submission_date.isoformat()
                    if item.target_submission_date
                    else None
                ),
                "target_decision": (
                    item.target_decision_date.isoformat()
                    if item.target_decision_date
                    else None
                ),
                "actual_submission": (
                    item.actual_submission_date.isoformat()
                    if item.actual_submission_date
                    else None
                ),
                "actual_decision": (
                    item.actual_decision_date.isoformat()
                    if item.actual_decision_date
                    else None
                ),
                "notes": item.notes,
            }
        )
    return serialised


def _serialise_simple(
    records: Iterable, fields: tuple[str, ...]
) -> list[dict[str, object]]:
    serialised: list[dict[str, object]] = []
    for record in records:
        payload: dict[str, object] = {}
        for field in fields:
            value = getattr(record, field, None)
            if hasattr(value, "isoformat"):
                payload[field] = value.isoformat()  # type: ignore[assignment]
            elif hasattr(value, "value"):
                payload[field] = value.value  # type: ignore[assignment]
            else:
                payload[field] = value  # type: ignore[assignment]
        serialised.append(payload)
    return serialised


async def build_snapshot(
    session: AsyncSession, project_id: int
) -> EntitlementsSnapshot:
    """Collect a project snapshot for export."""

    service = EntitlementsService(session)
    roadmap = await service.all_roadmap_items(project_id)
    studies = await _collect_all(
        lambda **params: service.list_studies(project_id=project_id, **params)
    )
    engagements = await _collect_all(
        lambda **params: service.list_engagements(project_id=project_id, **params)
    )
    legal = await _collect_all(
        lambda **params: service.list_legal_instruments(project_id=project_id, **params)
    )

    snapshot = EntitlementsSnapshot(
        project_id=project_id,
        roadmap=_serialise_roadmap(roadmap),
        studies=_serialise_simple(
            studies,
            (
                "name",
                "study_type",
                "status",
                "consultant",
                "due_date",
                "completed_at",
            ),
        ),
        engagements=_serialise_simple(
            engagements,
            (
                "name",
                "organisation",
                "engagement_type",
                "status",
                "contact_email",
                "contact_phone",
            ),
        ),
        legal=_serialise_simple(
            legal,
            (
                "name",
                "instrument_type",
                "status",
                "reference_code",
                "effective_date",
                "expiry_date",
            ),
        ),
        generated_at=datetime.now(UTC),
    )
    return snapshot


def _render_csv(snapshot: EntitlementsSnapshot) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([f"Entitlements roadmap for project {snapshot.project_id}"])
    writer.writerow(
        [
            "Sequence",
            "Status",
            "Approval Type",
            "Target Submission",
            "Target Decision",
            "Actual Submission",
            "Actual Decision",
            "Notes",
        ]
    )
    for item in snapshot.roadmap:
        writer.writerow(
            [
                item.get("sequence"),
                item.get("status"),
                item.get("approval_type_id"),
                item.get("target_submission"),
                item.get("target_decision"),
                item.get("actual_submission"),
                item.get("actual_decision"),
                item.get("notes"),
            ]
        )

    writer.writerow([])
    writer.writerow(["Studies"])
    writer.writerow(["Name", "Type", "Status", "Consultant", "Due", "Completed"])
    for item in snapshot.studies:
        writer.writerow(
            [
                item.get("name"),
                item.get("study_type"),
                item.get("status"),
                item.get("consultant"),
                item.get("due_date"),
                item.get("completed_at"),
            ]
        )

    writer.writerow([])
    writer.writerow(["Stakeholder Engagements"])
    writer.writerow(
        [
            "Name",
            "Organisation",
            "Type",
            "Status",
            "Contact Email",
            "Contact Phone",
        ]
    )
    for item in snapshot.engagements:
        writer.writerow(
            [
                item.get("name"),
                item.get("organisation"),
                item.get("engagement_type"),
                item.get("status"),
                item.get("contact_email"),
                item.get("contact_phone"),
            ]
        )

    writer.writerow([])
    writer.writerow(["Legal Instruments"])
    writer.writerow(
        [
            "Name",
            "Type",
            "Status",
            "Reference",
            "Effective",
            "Expiry",
        ]
    )
    for item in snapshot.legal:
        writer.writerow(
            [
                item.get("name"),
                item.get("instrument_type"),
                item.get("status"),
                item.get("reference_code"),
                item.get("effective_date"),
                item.get("expiry_date"),
            ]
        )

    return buffer.getvalue().encode("utf-8")


def _render_html(snapshot: EntitlementsSnapshot) -> str:
    def _render_section(
        title: str, headers: list[str], rows: list[list[object]]
    ) -> str:
        header_html = "".join(f"<th>{header}</th>" for header in headers)
        rows_html = "".join(
            "<tr>"
            + "".join(f"<td>{(cell if cell is not None else '')}</td>" for cell in row)
            + "</tr>"
            for row in rows
        )
        return (
            f"<section><h2>{title}</h2><table>"
            f"<thead><tr>{header_html}</tr></thead><tbody>{rows_html}</tbody>"
            "</table></section>"
        )

    roadmap_rows = [
        [
            item.get("sequence"),
            item.get("status"),
            item.get("approval_type_id"),
            item.get("target_submission"),
            item.get("target_decision"),
            item.get("actual_submission"),
            item.get("actual_decision"),
            item.get("notes"),
        ]
        for item in snapshot.roadmap
    ]

    study_rows = [
        [
            item.get("name"),
            item.get("study_type"),
            item.get("status"),
            item.get("consultant"),
            item.get("due_date"),
            item.get("completed_at"),
        ]
        for item in snapshot.studies
    ]

    engagement_rows = [
        [
            item.get("name"),
            item.get("organisation"),
            item.get("engagement_type"),
            item.get("status"),
            item.get("contact_email"),
            item.get("contact_phone"),
        ]
        for item in snapshot.engagements
    ]

    legal_rows = [
        [
            item.get("name"),
            item.get("instrument_type"),
            item.get("status"),
            item.get("reference_code"),
            item.get("effective_date"),
            item.get("expiry_date"),
        ]
        for item in snapshot.legal
    ]

    sections = [
        _render_section(
            "Roadmap",
            [
                "Sequence",
                "Status",
                "Approval Type",
                "Target Submission",
                "Target Decision",
                "Actual Submission",
                "Actual Decision",
                "Notes",
            ],
            roadmap_rows,
        ),
        _render_section(
            "Studies",
            ["Name", "Type", "Status", "Consultant", "Due", "Completed"],
            study_rows,
        ),
        _render_section(
            "Stakeholder Engagements",
            [
                "Name",
                "Organisation",
                "Type",
                "Status",
                "Contact Email",
                "Contact Phone",
            ],
            engagement_rows,
        ),
        _render_section(
            "Legal Instruments",
            ["Name", "Type", "Status", "Reference", "Effective", "Expiry"],
            legal_rows,
        ),
    ]

    sections_html = "".join(sections)
    generated = snapshot.generated_at.isoformat()
    html = (
        "<html><head><meta charset='utf-8'><style>"
        "body{font-family:Arial,sans-serif;background-color:#0f172a;color:#e2e8f0;padding:24px;}"
        "h1{font-size:24px;margin-bottom:16px;}"
        "section{margin-bottom:24px;}"
        "table{width:100%;border-collapse:collapse;margin-top:8px;}"
        "th,td{border:1px solid #1e293b;padding:6px 8px;text-align:left;}"
        "th{background-color:#1e293b;}"
        "tr:nth-child(even){background-color:#111827;}"
        "</style></head><body>"
        f"<h1>Entitlements summary – Project {snapshot.project_id}</h1>"
        f"<p>Generated at {generated}</p>"
        f"{sections_html}"
        "</body></html>"
    )
    return html


def render_export_payload(
    snapshot: EntitlementsSnapshot, fmt: EntitlementsExportFormat
) -> tuple[bytes, str]:
    """Render the snapshot into the requested format."""

    if fmt is EntitlementsExportFormat.CSV:
        return _render_csv(snapshot), fmt.media_type

    html = _render_html(snapshot)
    if fmt is EntitlementsExportFormat.HTML:
        return html.encode("utf-8"), fmt.media_type

    pdf = render_html_to_pdf(html)
    if pdf is not None:
        return pdf, fmt.media_type

    # Fallback to HTML payload when PDF dependencies are unavailable.
    return html.encode("utf-8"), EntitlementsExportFormat.HTML.media_type


async def generate_entitlements_export(
    session: AsyncSession,
    *,
    project_id: int,
    fmt: EntitlementsExportFormat,
) -> tuple[bytes, str, str]:
    """Return payload, media type, and filename for the export."""

    snapshot = await build_snapshot(session, project_id)
    payload, media_type = render_export_payload(snapshot, fmt)
    extension = (
        fmt.value
        if media_type == fmt.media_type
        else EntitlementsExportFormat.HTML.value
    )
    filename = f"project-{project_id}-entitlements.{extension}"
    return payload, media_type, filename


__all__ = [
    "EntitlementsExportFormat",
    "EntitlementsSnapshot",
    "build_snapshot",
    "render_export_payload",
    "generate_entitlements_export",
]
