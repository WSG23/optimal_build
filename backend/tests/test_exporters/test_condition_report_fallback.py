"""Regression tests for the condition report export fallback."""

from __future__ import annotations

import re

import pytest

from app.api.v1.developers import (
    ChecklistProgressResponse,
    ConditionAssessmentResponse,
    ConditionReportResponse,
    ConditionSystemResponse,
    _render_condition_report_html,
)
from app.utils import render as pdf_render


@pytest.mark.parametrize("scenario_name", ["mixed_use", None])
def test_condition_report_pdf_fallback_generates_plain_pdf(monkeypatch, scenario_name):
    """Ensure the fallback PDF renderer produces readable content."""

    # Force the fallback path (no WeasyPrint).
    monkeypatch.setattr(pdf_render, "_HTML_FACTORY", None)

    report = ConditionReportResponse(
        property_id="123",
        property_name="Sample Property",
        address="123 Example Street",
        generated_at="2025-01-01T00:00:00Z",
        scenario_assessments=[
            ConditionAssessmentResponse(
                property_id="123",
                scenario=scenario_name,
                overall_score=82,
                overall_rating="Good",
                risk_level="Low",
                summary="Overall building in good condition.",
                scenario_context="Redevelopment",
                systems=[
                    ConditionSystemResponse(
                        name="HVAC",
                        rating="Good",
                        score=80,
                        notes="Regular maintenance",
                        recommended_actions=["Replace filters"],
                    )
                ],
                recommended_actions=["Engage HVAC contractor"],
                recorded_at="2024-12-31T12:00:00Z",
            )
        ],
        history=[],
        checklist_summary=ChecklistProgressResponse(
            total=10,
            completed=6,
            in_progress=2,
            pending=1,
            not_applicable=1,
            completion_percentage=60,
        ),
    )

    html = _render_condition_report_html(report)
    pdf_bytes = pdf_render.render_html_to_pdf(html)

    assert pdf_bytes is not None, "Fallback renderer should return PDF bytes"
    assert pdf_bytes.startswith(b"%PDF-1.4"), "Minimal PDF header expected"

    # Extract the plain-text content from the stream section.
    match = re.search(rb"stream\n(.*?)\nendstream", pdf_bytes, flags=re.S)
    assert match, "PDF content stream should be present"
    payload = match.group(1).decode("latin-1")

    assert "Condition Summary" in payload
    assert "Total 10 - Completed 6" in payload
    assert "Overall building in good condition." in payload
    assert "font-family" not in payload, "CSS should be stripped in fallback"
