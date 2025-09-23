"""Entitlement export helpers."""

from __future__ import annotations

import csv
import html
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from typing import Iterable, List, Sequence

from app.schemas.entitlements import EntitlementExportFormat
from app.services.entitlements import EntitlementsService
from app.utils.pdf import html_to_pdf


class EntitlementsExportError(RuntimeError):
    """Raised when an export cannot be generated."""


@dataclass
class EntitlementsExportPayload:
    """Generated payload returned to the API layer."""

    format: EntitlementExportFormat
    body: bytes
    media_type: str
    filename: str
    fallback: str | None = None

    def stream(self) -> Iterable[bytes]:
        """Return a streaming iterator for the payload body."""

        yield self.body


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value) -> str:
    return json.dumps(value, sort_keys=True, default=str)


def _normalise_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return _json(value)
    return str(value)


def _render_csv(snapshot) -> bytes:
    authorities, approvals, roadmap, studies, stakeholders, legal = snapshot
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["generated_at", _timestamp()])
    writer.writerow([])

    writer.writerow(["# Authorities"])
    writer.writerow(["id", "code", "name", "jurisdiction", "contact_email"])
    for authority in authorities:
        writer.writerow(
            [
                authority.id,
                authority.code,
                authority.name,
                authority.jurisdiction,
                authority.contact_email or "",
            ]
        )
    writer.writerow([])

    writer.writerow(["# Approval Types"])
    writer.writerow(["id", "authority_id", "code", "name", "lead_time_days"])
    for approval in approvals:
        writer.writerow(
            [
                approval.id,
                approval.authority_id,
                approval.code,
                approval.name,
                approval.default_lead_time_days or "",
            ]
        )
    writer.writerow([])

    writer.writerow(["# Roadmap"])
    writer.writerow(
        [
            "id",
            "project_id",
            "sequence",
            "approval_type_id",
            "status",
            "target_submission_date",
            "actual_submission_date",
            "decision_date",
            "notes",
            "attachments",
        ]
    )
    for item in roadmap:
        writer.writerow(
            [
                item.id,
                item.project_id,
                item.sequence,
                item.approval_type_id,
                item.status.value if hasattr(item.status, "value") else item.status,
                item.target_submission_date or "",
                item.actual_submission_date or "",
                item.decision_date or "",
                (item.notes or "").replace("\n", " "),
                _json(item.attachments or []),
            ]
        )
    writer.writerow([])

    writer.writerow(["# Studies"])
    writer.writerow(
        [
            "id",
            "project_id",
            "name",
            "study_type",
            "status",
            "consultant",
            "submission_date",
            "approval_date",
            "report_uri",
        ]
    )
    for study in studies:
        writer.writerow(
            [
                study.id,
                study.project_id,
                study.name,
                study.study_type.value if hasattr(study.study_type, "value") else study.study_type,
                study.status.value if hasattr(study.status, "value") else study.status,
                study.consultant or "",
                study.submission_date or "",
                study.approval_date or "",
                study.report_uri or "",
            ]
        )
    writer.writerow([])

    writer.writerow(["# Stakeholders"])
    writer.writerow(
        [
            "id",
            "project_id",
            "stakeholder_name",
            "stakeholder_type",
            "status",
            "contact_email",
            "meeting_date",
            "summary",
            "next_steps",
        ]
    )
    for engagement in stakeholders:
        writer.writerow(
            [
                engagement.id,
                engagement.project_id,
                engagement.stakeholder_name,
                engagement.stakeholder_type.value
                if hasattr(engagement.stakeholder_type, "value")
                else engagement.stakeholder_type,
                engagement.status.value if hasattr(engagement.status, "value") else engagement.status,
                engagement.contact_email or "",
                engagement.meeting_date or "",
                (engagement.summary or "").replace("\n", " "),
                "; ".join(str(step) for step in engagement.next_steps or []),
            ]
        )
    writer.writerow([])

    writer.writerow(["# Legal Instruments"])
    writer.writerow(
        [
            "id",
            "project_id",
            "title",
            "instrument_type",
            "status",
            "reference_code",
            "effective_date",
            "expiry_date",
            "storage_uri",
        ]
    )
    for instrument in legal:
        writer.writerow(
            [
                instrument.id,
                instrument.project_id,
                instrument.title,
                instrument.instrument_type.value
                if hasattr(instrument.instrument_type, "value")
                else instrument.instrument_type,
                instrument.status.value if hasattr(instrument.status, "value") else instrument.status,
                instrument.reference_code or "",
                instrument.effective_date or "",
                instrument.expiry_date or "",
                instrument.storage_uri or "",
            ]
        )

    return buffer.getvalue().encode("utf-8")


def _table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    head_html = "".join(f"<th>{html.escape(str(column))}</th>" for column in headers)
    body_html = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(value))}</td>" for value in row) + "</tr>"
        for row in rows
    )
    return f"<table><thead><tr>{head_html}</tr></thead><tbody>{body_html}</tbody></table>"


def _render_html(snapshot) -> str:
    authorities, approvals, roadmap, studies, stakeholders, legal = snapshot
    sections: List[str] = []

    sections.append("<h2>Authorities</h2>" + _table(
        ["Code", "Name", "Jurisdiction", "Contact"],
        [
            [
                auth.code,
                auth.name,
                auth.jurisdiction,
                auth.contact_email or "",
            ]
            for auth in authorities
        ],
    ))

    sections.append("<h2>Approval Types</h2>" + _table(
        ["Authority", "Code", "Name", "Lead time (days)"],
        [
            [
                next((a.name for a in authorities if a.id == approval.authority_id), ""),
                approval.code,
                approval.name,
                approval.default_lead_time_days or "",
            ]
            for approval in approvals
        ],
    ))

    sections.append("<h2>Roadmap</h2>" + _table(
        [
            "Sequence",
            "Status",
            "Approval",
            "Target",
            "Actual",
            "Decision",
            "Notes",
        ],
        [
            [
                item.sequence,
                item.status.value if hasattr(item.status, "value") else item.status,
                getattr(item.approval_type, "name", ""),
                item.target_submission_date or "",
                item.actual_submission_date or "",
                item.decision_date or "",
                html.escape((item.notes or "")),
            ]
            for item in roadmap
        ],
    ))

    sections.append("<h2>Studies</h2>" + _table(
        ["Name", "Type", "Status", "Consultant", "Submission", "Approval"],
        [
            [
                study.name,
                study.study_type.value if hasattr(study.study_type, "value") else study.study_type,
                study.status.value if hasattr(study.status, "value") else study.status,
                study.consultant or "",
                study.submission_date or "",
                study.approval_date or "",
            ]
            for study in studies
        ],
    ))

    sections.append("<h2>Stakeholders</h2>" + _table(
        ["Name", "Type", "Status", "Next steps"],
        [
            [
                engagement.stakeholder_name,
                engagement.stakeholder_type.value
                if hasattr(engagement.stakeholder_type, "value")
                else engagement.stakeholder_type,
                engagement.status.value if hasattr(engagement.status, "value") else engagement.status,
                "; ".join(str(step) for step in engagement.next_steps or []),
            ]
            for engagement in stakeholders
        ],
    ))

    sections.append("<h2>Legal Instruments</h2>" + _table(
        ["Title", "Type", "Status", "Effective", "Expiry"],
        [
            [
                instrument.title,
                instrument.instrument_type.value
                if hasattr(instrument.instrument_type, "value")
                else instrument.instrument_type,
                instrument.status.value if hasattr(instrument.status, "value") else instrument.status,
                instrument.effective_date or "",
                instrument.expiry_date or "",
            ]
            for instrument in legal
        ],
    ))

    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<title>Entitlements Export</title>"
        "<style>body{font-family:Arial,Helvetica,sans-serif;background:#0f172a;color:#e2e8f0;padding:2rem;}"
        "h1{color:#38bdf8;}table{width:100%;border-collapse:collapse;margin-bottom:2rem;}"
        "th,td{border:1px solid #1e293b;padding:0.5rem;text-align:left;}"
        "th{background:#1e293b;color:#f8fafc;}tr:nth-child(even){background:#111827;}"
        "</style></head><body>"
        f"<h1>Entitlements export</h1><p>Generated at {_timestamp()}</p>"
        + "".join(sections)
        + "</body></html>"
    )


async def generate_entitlements_export(
    *, service: EntitlementsService, project_id: int, fmt: EntitlementExportFormat
) -> EntitlementsExportPayload:
    """Return an export payload for the requested format."""

    snapshot = await service.snapshot_project(project_id)
    fmt = EntitlementExportFormat(fmt)

    if fmt is EntitlementExportFormat.CSV:
        body = _render_csv(snapshot)
        return EntitlementsExportPayload(
            format=fmt,
            body=body,
            media_type="text/csv",
            filename=f"project-{project_id}-entitlements.csv",
        )

    html_body = _render_html(snapshot).encode("utf-8")

    if fmt is EntitlementExportFormat.HTML:
        return EntitlementsExportPayload(
            format=fmt,
            body=html_body,
            media_type="text/html",
            filename=f"project-{project_id}-entitlements.html",
        )

    if fmt is EntitlementExportFormat.PDF:
        pdf_bytes = html_to_pdf(html_body.decode("utf-8"))
        if pdf_bytes is None:
            return EntitlementsExportPayload(
                format=EntitlementExportFormat.HTML,
                body=html_body,
                media_type="text/html",
                filename=f"project-{project_id}-entitlements.html",
                fallback="html",
            )
        return EntitlementsExportPayload(
            format=fmt,
            body=pdf_bytes,
            media_type="application/pdf",
            filename=f"project-{project_id}-entitlements.pdf",
        )

    raise EntitlementsExportError(f"Unsupported export format: {fmt}")


__all__ = [
    "EntitlementsExportError",
    "EntitlementsExportPayload",
    "generate_entitlements_export",
]
