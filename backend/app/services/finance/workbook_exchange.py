"""Workbook import/export helpers for finance scenarios."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
import io
import re
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

from pydantic import ValidationError

from app.schemas.finance import FinanceFeasibilityRequest, FinanceFeasibilityResponse
from app.schemas.finance_workbook import (
    FinanceWorkbookPreviewResponse,
    FinanceWorkbookSheetSummary,
    FinanceWorkbookValidationIssue,
)

XLSX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

_XML_NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "office_rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
_WORKSHEET_REL = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
)
_HEADER_SANITIZE_RE = re.compile(r"[^a-z0-9]+")
_EXCEL_MAX_SHEET_NAME = 31


@dataclass(slots=True)
class _WorkbookSheet:
    name: str
    rows: list[list[str]]


@dataclass(slots=True)
class _WorkbookPreviewData:
    sheets: list[FinanceWorkbookSheetSummary]
    warnings: list[str]
    payload: dict[str, Any]


_SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "scenario": ("scenario", "meta", "metadata", "assumptions"),
    "cash_flow": ("cashflow", "cash_flow", "cash flow"),
    "dscr": ("dscr", "debt service", "noi"),
    "asset_mix": ("asset mix", "asset_mix", "assets"),
    "capital_stack": ("capital stack", "capital_stack", "capital"),
    "drawdown": ("drawdown", "drawdown schedule", "drawdown_schedule"),
    "loan_config": ("loan config", "construction loan", "loan settings"),
    "loan_facilities": ("loan facilities", "facilities", "construction facilities"),
    "sensitivity": ("sensitivity", "sensitivity bands", "sensitivities"),
    "summary": ("summary",),
}

_TABLE_HEADER_ALIASES: dict[str, dict[str, tuple[str, ...]]] = {
    "cash_flow": {
        "period": ("period", "label", "year", "month", "quarter"),
        "cash_flow": ("cash flow", "cash_flow", "amount", "value"),
    },
    "dscr": {
        "period": ("period", "label"),
        "net_operating_incomes": ("noi", "net operating income", "net_operating_income"),
        "debt_services": ("debt service", "debt_service", "debt services"),
    },
    "asset_mix": {
        "asset_type": ("asset", "asset type", "asset_type", "use"),
        "allocation_pct": ("allocation", "allocation pct", "allocation_pct"),
        "nia_sqm": ("nia", "nia sqm", "nia_sqm"),
        "rent_psm_month": ("rent", "rent psm month", "rent_psm_month"),
        "stabilised_vacancy_pct": (
            "vacancy",
            "stabilised vacancy pct",
            "stabilised_vacancy_pct",
        ),
        "opex_pct_of_rent": ("opex", "opex pct of rent", "opex_pct_of_rent"),
        "estimated_revenue_sgd": (
            "estimated revenue",
            "estimated_revenue_sgd",
            "revenue",
        ),
        "estimated_capex_sgd": (
            "estimated capex",
            "estimated_capex_sgd",
            "capex",
        ),
        "absorption_months": ("absorption", "absorption_months"),
        "risk_level": ("risk", "risk level", "risk_level"),
        "heritage_premium_pct": ("heritage premium", "heritage_premium_pct"),
        "notes": ("notes", "commentary"),
    },
    "capital_stack": {
        "name": ("name", "facility", "source"),
        "source_type": ("source type", "source_type", "type"),
        "amount": ("amount", "principal"),
        "rate": ("rate", "interest rate", "interest_rate"),
        "tranche_order": ("tranche", "tranche order", "tranche_order"),
    },
    "drawdown": {
        "period": ("period", "label"),
        "equity_draw": ("equity draw", "equity_draw", "equity"),
        "debt_draw": ("debt draw", "debt_draw", "debt"),
    },
    "loan_facilities": {
        "name": ("name", "facility"),
        "amount": ("amount",),
        "interest_rate": ("interest rate", "interest_rate", "rate"),
        "periods_per_year": ("periods per year", "periods_per_year"),
        "capitalise_interest": (
            "capitalise interest",
            "capitalise_interest",
            "capitalized",
        ),
        "upfront_fee_pct": ("upfront fee pct", "upfront_fee_pct"),
        "exit_fee_pct": ("exit fee pct", "exit_fee_pct"),
        "reserve_months": ("reserve months", "reserve_months"),
        "amortisation_months": ("amortisation months", "amortisation_months"),
    },
    "sensitivity": {
        "parameter": ("parameter",),
        "low": ("low", "downside"),
        "base": ("base",),
        "high": ("high", "upside"),
        "notes": ("notes",),
    },
}

_SCENARIO_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "project_id": ("project id", "project_id"),
    "project_name": ("project name", "project_name"),
    "scenario.name": ("scenario name", "scenario_name", "name"),
    "scenario.description": ("description", "scenario description"),
    "scenario.currency": ("currency",),
    "scenario.is_primary": ("is primary", "is_primary", "primary"),
    "scenario.jurisdiction_code": (
        "jurisdiction code",
        "jurisdiction_code",
        "jurisdiction",
    ),
    "scenario.cost_escalation.amount": (
        "cost amount",
        "cost_escalation amount",
        "amount",
    ),
    "scenario.cost_escalation.base_period": (
        "base period",
        "cost_escalation base_period",
        "base_period",
    ),
    "scenario.cost_escalation.series_name": (
        "series name",
        "series_name",
        "cost series",
    ),
    "scenario.cost_escalation.jurisdiction": (
        "cost jurisdiction",
        "cost_escalation jurisdiction",
    ),
    "scenario.cost_escalation.provider": (
        "provider",
        "cost provider",
        "cost_escalation provider",
    ),
    "scenario.cash_flow.discount_rate": (
        "discount rate",
        "discount_rate",
        "cashflow discount rate",
    ),
    "scenario.construction_loan.interest_rate": (
        "loan interest rate",
        "construction loan interest rate",
    ),
    "scenario.construction_loan.periods_per_year": (
        "loan periods per year",
        "construction loan periods per year",
    ),
    "scenario.construction_loan.capitalise_interest": (
        "loan capitalise interest",
        "construction loan capitalise interest",
    ),
}


def build_finance_workbook(
    summary: FinanceFeasibilityResponse,
    *,
    assumptions: Mapping[str, Any] | None,
) -> bytes:
    """Return an .xlsx workbook for a persisted finance scenario."""

    assumption_map = dict(assumptions or {})
    raw_asset_mix = assumption_map.get("asset_mix") or []
    raw_capital_stack = assumption_map.get("capital_stack") or []
    raw_drawdown = assumption_map.get("drawdown_schedule") or []
    raw_cash_flows = (assumption_map.get("cash_flow") or {}).get("cash_flows") or []
    raw_dscr = assumption_map.get("dscr") or {}
    raw_construction_loan = assumption_map.get("construction_loan") or {}
    raw_facilities = raw_construction_loan.get("facilities") or []
    raw_sensitivity = assumption_map.get("sensitivity_bands") or []

    scenario_rows = [
        ["field", "value"],
        ["project_id", _stringify(summary.project_id)],
        ["project_name", _stringify(summary.scenario_name)],
        ["scenario_name", _stringify(assumption_map.get("name") or summary.scenario_name)],
        ["description", _stringify(assumption_map.get("description"))],
        ["currency", _stringify(summary.currency)],
        ["is_primary", _stringify(summary.is_primary)],
        [
            "jurisdiction_code",
            _stringify(
                assumption_map.get("jurisdictionCode")
                or assumption_map.get("jurisdiction_code")
                or "SG"
            ),
        ],
        [
            "cost_amount",
            _stringify((assumption_map.get("cost_escalation") or {}).get("amount")),
        ],
        [
            "base_period",
            _stringify(
                (assumption_map.get("cost_escalation") or {}).get("base_period")
            ),
        ],
        [
            "series_name",
            _stringify(
                (assumption_map.get("cost_escalation") or {}).get("series_name")
            ),
        ],
        [
            "cost_jurisdiction",
            _stringify(
                (assumption_map.get("cost_escalation") or {}).get("jurisdiction")
            ),
        ],
        [
            "provider",
            _stringify((assumption_map.get("cost_escalation") or {}).get("provider")),
        ],
        [
            "discount_rate",
            _stringify((assumption_map.get("cash_flow") or {}).get("discount_rate")),
        ],
        [
            "loan_interest_rate",
            _stringify(
                (assumption_map.get("construction_loan") or {}).get("interest_rate")
            ),
        ],
        [
            "loan_periods_per_year",
            _stringify(
                (assumption_map.get("construction_loan") or {}).get("periods_per_year")
            ),
        ],
        [
            "loan_capitalise_interest",
            _stringify(
                (assumption_map.get("construction_loan") or {}).get(
                    "capitalise_interest"
                )
            ),
        ],
    ]

    sheets = [
        _WorkbookSheet(
            name="Summary",
            rows=[
                ["metric", "value", "unit"],
                ["scenario_id", _stringify(summary.scenario_id), ""],
                ["currency", _stringify(summary.currency), ""],
                ["escalated_cost", _stringify(summary.escalated_cost), "currency"],
                ["asset_count", str(len(summary.asset_breakdowns)), "count"],
                ["sensitivity_count", str(len(summary.sensitivity_results)), "count"],
                *[
                    [
                        _stringify(result.name),
                        _stringify(result.value),
                        _stringify(result.unit),
                    ]
                    for result in summary.results
                ],
            ],
        ),
        _WorkbookSheet(name="Scenario", rows=scenario_rows),
        _WorkbookSheet(
            name="Cash Flow",
            rows=[
                ["period", "cash_flow"],
                *[
                    [str(index + 1), _stringify(value)]
                    for index, value in enumerate(raw_cash_flows)
                ],
            ],
        ),
        _WorkbookSheet(
            name="DSCR",
            rows=[
                ["period", "noi", "debt_service"],
                *[
                    [
                        _stringify(label),
                        _stringify(noi),
                        _stringify(debt_service),
                    ]
                    for label, noi, debt_service in zip(
                        raw_dscr.get("period_labels") or [],
                        raw_dscr.get("net_operating_incomes") or [],
                        raw_dscr.get("debt_services") or [],
                        strict=False,
                    )
                ],
            ],
        ),
        _WorkbookSheet(
            name="Asset Mix",
            rows=[
                [
                    "asset_type",
                    "allocation_pct",
                    "nia_sqm",
                    "rent_psm_month",
                    "stabilised_vacancy_pct",
                    "opex_pct_of_rent",
                    "estimated_revenue_sgd",
                    "estimated_capex_sgd",
                    "absorption_months",
                    "risk_level",
                    "heritage_premium_pct",
                    "notes",
                ],
                *[
                    [
                        _stringify(item.get("asset_type")),
                        _stringify(item.get("allocation_pct")),
                        _stringify(item.get("nia_sqm")),
                        _stringify(item.get("rent_psm_month")),
                        _stringify(item.get("stabilised_vacancy_pct")),
                        _stringify(item.get("opex_pct_of_rent")),
                        _stringify(item.get("estimated_revenue_sgd")),
                        _stringify(item.get("estimated_capex_sgd")),
                        _stringify(item.get("absorption_months")),
                        _stringify(item.get("risk_level")),
                        _stringify(item.get("heritage_premium_pct")),
                        " | ".join(item.get("notes") or []),
                    ]
                    for item in raw_asset_mix
                ],
            ],
        ),
        _WorkbookSheet(
            name="Capital Stack",
            rows=[
                ["name", "source_type", "amount", "rate", "tranche_order"],
                *[
                    [
                        _stringify(slice_.get("name")),
                        _stringify(slice_.get("source_type")),
                        _stringify(slice_.get("amount")),
                        _stringify(slice_.get("rate")),
                        _stringify(slice_.get("tranche_order")),
                    ]
                    for slice_ in raw_capital_stack
                ],
            ],
        ),
        _WorkbookSheet(
            name="Drawdown",
            rows=[
                ["period", "equity_draw", "debt_draw"],
                *[
                    [
                        _stringify(entry.get("period")),
                        _stringify(entry.get("equity_draw")),
                        _stringify(entry.get("debt_draw")),
                    ]
                    for entry in raw_drawdown
                ],
            ],
        ),
        _WorkbookSheet(
            name="Loan Config",
            rows=[
                ["field", "value"],
                [
                    "interest_rate",
                    _stringify(raw_construction_loan.get("interest_rate")),
                ],
                [
                    "periods_per_year",
                    _stringify(raw_construction_loan.get("periods_per_year")),
                ],
                [
                    "capitalise_interest",
                    _stringify(raw_construction_loan.get("capitalise_interest")),
                ],
            ],
        ),
        _WorkbookSheet(
            name="Loan Facilities",
            rows=[
                [
                    "name",
                    "amount",
                    "interest_rate",
                    "periods_per_year",
                    "capitalise_interest",
                    "upfront_fee_pct",
                    "exit_fee_pct",
                    "reserve_months",
                    "amortisation_months",
                ],
                *[
                    [
                        _stringify(facility.get("name")),
                        _stringify(facility.get("amount")),
                        _stringify(facility.get("interest_rate")),
                        _stringify(facility.get("periods_per_year")),
                        _stringify(facility.get("capitalise_interest")),
                        _stringify(facility.get("upfront_fee_pct")),
                        _stringify(facility.get("exit_fee_pct")),
                        _stringify(facility.get("reserve_months")),
                        _stringify(facility.get("amortisation_months")),
                    ]
                    for facility in raw_facilities
                ],
            ],
        ),
        _WorkbookSheet(
            name="Sensitivity",
            rows=[
                ["parameter", "low", "base", "high", "notes"],
                *[
                    [
                        _stringify(item.get("parameter")),
                        _stringify(item.get("low")),
                        _stringify(item.get("base")),
                        _stringify(item.get("high")),
                        " | ".join(item.get("notes") or []),
                    ]
                    for item in raw_sensitivity
                ],
            ],
        ),
    ]
    return _build_xlsx_bytes(sheets)


def preview_finance_workbook(
    content: bytes,
    *,
    filename: str,
    project_id: str | int | None = None,
    project_name: str | None = None,
) -> FinanceWorkbookPreviewResponse:
    """Parse a workbook and return a validated preview response."""

    preview = _parse_workbook_preview(
        content,
        project_id=project_id,
        project_name=project_name,
    )
    validation_errors: list[FinanceWorkbookValidationIssue] = []
    is_valid = False
    try:
        validated = FinanceFeasibilityRequest.model_validate(preview.payload)
        payload = validated.model_dump(mode="json", by_alias=True)
        is_valid = True
    except ValidationError as exc:
        payload = preview.payload
        validation_errors = [
            FinanceWorkbookValidationIssue(
                field=".".join(str(part) for part in error["loc"]),
                message=error["msg"],
            )
            for error in exc.errors()
        ]

    scenario_name = _nested_get(payload, "scenario", "name")
    resolved_project_name = payload.get("project_name")
    asset_count = len((_nested_get(payload, "scenario", "asset_mix") or []))
    return FinanceWorkbookPreviewResponse(
        filename=filename,
        detected_sheets=preview.sheets,
        warnings=preview.warnings,
        is_valid=is_valid,
        validation_errors=validation_errors,
        request_payload=payload,
        scenario_name=str(scenario_name) if scenario_name else None,
        project_name=str(resolved_project_name) if resolved_project_name else None,
        asset_count=asset_count,
    )


def _parse_workbook_preview(
    content: bytes,
    *,
    project_id: str | int | None,
    project_name: str | None,
) -> _WorkbookPreviewData:
    sheets = _read_xlsx(content)
    warnings: list[str] = []
    sheet_summaries: list[FinanceWorkbookSheetSummary] = []
    sections: dict[str, _WorkbookSheet] = {}

    for sheet in sheets:
        recognised = _recognise_sheet(sheet.name)
        if recognised and recognised not in sections:
            sections[recognised] = sheet
        elif recognised:
            warnings.append(f'Duplicate sheet for "{recognised}" ignored: {sheet.name}.')
        elif sheet.rows:
            warnings.append(f'Unrecognised sheet skipped: {sheet.name}.')
        sheet_summaries.append(
            FinanceWorkbookSheetSummary(
                name=sheet.name,
                row_count=len(sheet.rows),
                column_count=max((len(row) for row in sheet.rows), default=0),
                recognised_as=recognised,
            )
        )

    payload = _build_request_payload(sections, warnings)
    if project_id not in (None, "") and not payload.get("project_id"):
        payload["project_id"] = str(project_id)
    if project_name and not payload.get("project_name"):
        payload["project_name"] = project_name

    return _WorkbookPreviewData(
        sheets=sheet_summaries,
        warnings=warnings,
        payload=payload,
    )


def _build_request_payload(
    sections: Mapping[str, _WorkbookSheet],
    warnings: list[str],
) -> dict[str, Any]:
    payload: dict[str, Any] = {"scenario": {}}
    scenario = payload["scenario"]

    scenario_sheet = sections.get("scenario")
    if scenario_sheet:
        scenario_values = _parse_key_value_sheet(scenario_sheet)
        for target, aliases in _SCENARIO_FIELD_ALIASES.items():
            value = _first_alias_value(scenario_values, aliases)
            if value is None:
                continue
            _assign_path(payload, target, value)

    cash_flow_sheet = sections.get("cash_flow")
    if cash_flow_sheet:
        cash_flow_rows = _parse_table_sheet(cash_flow_sheet, "cash_flow", warnings)
        if cash_flow_rows:
            values = [row.get("cash_flow") for row in cash_flow_rows if row.get("cash_flow")]
            if values:
                _assign_path(scenario, "cash_flow.cash_flows", values)

    dscr_sheet = sections.get("dscr")
    if dscr_sheet:
        dscr_rows = _parse_table_sheet(dscr_sheet, "dscr", warnings)
        if dscr_rows:
            _assign_path(
                scenario,
                "dscr.net_operating_incomes",
                [row["net_operating_incomes"] for row in dscr_rows if row.get("net_operating_incomes")],
            )
            _assign_path(
                scenario,
                "dscr.debt_services",
                [row["debt_services"] for row in dscr_rows if row.get("debt_services")],
            )
            period_labels = [row["period"] for row in dscr_rows if row.get("period")]
            if period_labels:
                _assign_path(scenario, "dscr.period_labels", period_labels)

    asset_sheet = sections.get("asset_mix")
    if asset_sheet:
        rows = _parse_table_sheet(asset_sheet, "asset_mix", warnings)
        if rows:
            assets = []
            for row in rows:
                asset = {
                    "asset_type": row.get("asset_type"),
                    "allocation_pct": row.get("allocation_pct"),
                    "nia_sqm": row.get("nia_sqm"),
                    "rent_psm_month": row.get("rent_psm_month"),
                    "stabilised_vacancy_pct": row.get("stabilised_vacancy_pct"),
                    "opex_pct_of_rent": row.get("opex_pct_of_rent"),
                    "estimated_revenue_sgd": row.get("estimated_revenue_sgd"),
                    "estimated_capex_sgd": row.get("estimated_capex_sgd"),
                    "absorption_months": row.get("absorption_months"),
                    "risk_level": row.get("risk_level"),
                    "heritage_premium_pct": row.get("heritage_premium_pct"),
                    "notes": _split_notes(row.get("notes")),
                }
                if asset["asset_type"]:
                    assets.append(_drop_none_values(asset))
            if assets:
                scenario["asset_mix"] = assets

    capital_sheet = sections.get("capital_stack")
    if capital_sheet:
        rows = _parse_table_sheet(capital_sheet, "capital_stack", warnings)
        capital_stack = []
        for row in rows:
            entry = {
                "name": row.get("name"),
                "source_type": row.get("source_type"),
                "amount": row.get("amount"),
                "rate": row.get("rate"),
                "tranche_order": _to_optional_int(row.get("tranche_order")),
            }
            if entry["name"] and entry["source_type"] and entry["amount"]:
                capital_stack.append(_drop_none_values(entry))
        if capital_stack:
            scenario["capital_stack"] = capital_stack

    drawdown_sheet = sections.get("drawdown")
    if drawdown_sheet:
        rows = _parse_table_sheet(drawdown_sheet, "drawdown", warnings)
        drawdown = []
        for row in rows:
            entry = {
                "period": row.get("period"),
                "equity_draw": row.get("equity_draw"),
                "debt_draw": row.get("debt_draw"),
            }
            if entry["period"] and (
                entry["equity_draw"] is not None or entry["debt_draw"] is not None
            ):
                drawdown.append(_drop_none_values(entry))
        if drawdown:
            scenario["drawdown_schedule"] = drawdown

    loan_config_sheet = sections.get("loan_config")
    if loan_config_sheet:
        config_values = _parse_key_value_sheet(loan_config_sheet)
        loan_config = {
            "interest_rate": _first_alias_value(
                config_values, ("interest rate", "interest_rate")
            ),
            "periods_per_year": _to_optional_int(
                _first_alias_value(config_values, ("periods per year", "periods_per_year"))
            ),
            "capitalise_interest": _to_optional_bool(
                _first_alias_value(
                    config_values,
                    ("capitalise interest", "capitalise_interest"),
                )
            ),
        }
        scenario["construction_loan"] = _drop_none_values(loan_config)

    loan_facilities_sheet = sections.get("loan_facilities")
    if loan_facilities_sheet:
        rows = _parse_table_sheet(loan_facilities_sheet, "loan_facilities", warnings)
        facilities = []
        for row in rows:
            facility = {
                "name": row.get("name"),
                "amount": row.get("amount"),
                "interest_rate": row.get("interest_rate"),
                "periods_per_year": _to_optional_int(row.get("periods_per_year")),
                "capitalise_interest": _to_optional_bool(
                    row.get("capitalise_interest")
                ),
                "upfront_fee_pct": row.get("upfront_fee_pct"),
                "exit_fee_pct": row.get("exit_fee_pct"),
                "reserve_months": _to_optional_int(row.get("reserve_months")),
                "amortisation_months": _to_optional_int(
                    row.get("amortisation_months")
                ),
            }
            if facility["name"]:
                facilities.append(_drop_none_values(facility))
        if facilities:
            scenario.setdefault("construction_loan", {})
            scenario["construction_loan"]["facilities"] = facilities

    sensitivity_sheet = sections.get("sensitivity")
    if sensitivity_sheet:
        rows = _parse_table_sheet(sensitivity_sheet, "sensitivity", warnings)
        sensitivities = []
        for row in rows:
            item = {
                "parameter": row.get("parameter"),
                "low": row.get("low"),
                "base": row.get("base"),
                "high": row.get("high"),
                "notes": _split_notes(row.get("notes")),
            }
            if item["parameter"]:
                sensitivities.append(_drop_none_values(item))
        if sensitivities:
            scenario["sensitivity_bands"] = sensitivities

    scenario["currency"] = scenario.get("currency") or "SGD"
    scenario["cost_escalation"] = {
        "amount": _nested_get(scenario, "cost_escalation", "amount"),
        "base_period": _nested_get(scenario, "cost_escalation", "base_period"),
        "series_name": _nested_get(scenario, "cost_escalation", "series_name"),
        "jurisdiction": _nested_get(scenario, "cost_escalation", "jurisdiction")
        or "SG",
        "provider": _nested_get(scenario, "cost_escalation", "provider"),
    }
    scenario["cash_flow"] = {
        "discount_rate": _nested_get(scenario, "cash_flow", "discount_rate"),
        "cash_flows": _nested_get(scenario, "cash_flow", "cash_flows") or [],
    }
    if not scenario.get("name"):
        warnings.append("Workbook is missing a scenario name.")
    if not payload.get("project_id"):
        warnings.append("Workbook is missing a project id; supply one in the import form.")
    return _drop_empty_sections(payload)


def _read_xlsx(content: bytes) -> list[_WorkbookSheet]:
    if not content:
        raise ValueError("Empty workbook payload.")

    with ZipFile(io.BytesIO(content), "r") as archive:
        workbook_xml = archive.read("xl/workbook.xml")
        workbook_tree = ET.fromstring(workbook_xml)
        rels_tree = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        relationships = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rels_tree.findall("rel:Relationship", _XML_NS)
            if rel.attrib.get("Type") == _WORKSHEET_REL
        }
        shared_strings = _read_shared_strings(archive)

        sheets: list[_WorkbookSheet] = []
        for sheet_node in workbook_tree.findall("main:sheets/main:sheet", _XML_NS):
            name = sheet_node.attrib.get("name", "Sheet")
            rel_id = sheet_node.attrib.get(f"{{{_XML_NS['office_rel']}}}id")
            target = relationships.get(rel_id or "")
            if not target:
                continue
            if not target.startswith("worksheets/"):
                target = f"worksheets/{target.split('/')[-1]}"
            rows = _read_sheet_rows(archive.read(f"xl/{target}"), shared_strings)
            sheets.append(_WorkbookSheet(name=name, rows=rows))
        return sheets


def _read_shared_strings(archive: ZipFile) -> list[str]:
    try:
        xml_bytes = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    tree = ET.fromstring(xml_bytes)
    values: list[str] = []
    for item in tree.findall("main:si", _XML_NS):
        text_parts = [node.text or "" for node in item.findall(".//main:t", _XML_NS)]
        values.append("".join(text_parts))
    return values


def _read_sheet_rows(xml_bytes: bytes, shared_strings: Sequence[str]) -> list[list[str]]:
    tree = ET.fromstring(xml_bytes)
    rows: list[list[str]] = []
    for row_node in tree.findall("main:sheetData/main:row", _XML_NS):
        row_values: list[str] = []
        for cell in row_node.findall("main:c", _XML_NS):
            value = _read_cell_value(cell, shared_strings)
            row_values.append(value)
        if any(value.strip() for value in row_values):
            rows.append(row_values)
    return rows


def _read_cell_value(cell: ET.Element, shared_strings: Sequence[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//main:t", _XML_NS))
    value_node = cell.find("main:v", _XML_NS)
    raw_value = value_node.text if value_node is not None else ""
    if raw_value is None:
        return ""
    if cell_type == "s":
        index = int(raw_value)
        return shared_strings[index] if 0 <= index < len(shared_strings) else ""
    if cell_type == "b":
        return "true" if raw_value == "1" else "false"
    return raw_value


def _parse_key_value_sheet(sheet: _WorkbookSheet) -> dict[str, str]:
    rows = sheet.rows
    if not rows:
        return {}
    start_index = 1 if len(rows[0]) >= 2 and _normalise_header(rows[0][0]) in {
        "field",
        "key",
    } else 0
    pairs: dict[str, str] = {}
    for row in rows[start_index:]:
        if len(row) < 2:
            continue
        key = _normalise_header(row[0])
        value = row[1].strip()
        if key and value:
            pairs[key] = value
    return pairs


def _parse_table_sheet(
    sheet: _WorkbookSheet,
    section: str,
    warnings: list[str],
) -> list[dict[str, str]]:
    if not sheet.rows:
        return []
    header_row = sheet.rows[0]
    aliases = _TABLE_HEADER_ALIASES.get(section, {})
    header_map: dict[int, str] = {}
    for index, header in enumerate(header_row):
        normalised = _normalise_header(header)
        for field, field_aliases in aliases.items():
            if normalised in {_normalise_header(alias) for alias in field_aliases}:
                header_map[index] = field
                break
    if not header_map:
        warnings.append(f'Could not map headers for sheet "{sheet.name}".')
        return []

    rows: list[dict[str, str]] = []
    for raw_row in sheet.rows[1:]:
        entry: dict[str, str] = {}
        for index, field in header_map.items():
            if index >= len(raw_row):
                continue
            value = raw_row[index].strip()
            if value:
                entry[field] = value
        if entry:
            rows.append(entry)
    return rows


def _build_xlsx_bytes(sheets: Sequence[_WorkbookSheet]) -> bytes:
    output = io.BytesIO()
    workbook_rels = []
    workbook_sheets = []
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _content_types_xml(len(sheets)))
        archive.writestr("_rels/.rels", _root_rels_xml())
        archive.writestr("xl/workbook.xml", _workbook_xml(sheets))
        for index, sheet in enumerate(sheets, start=1):
            workbook_rels.append(
                f'<Relationship Id="rId{index}" Type="{_WORKSHEET_REL}" '
                f'Target="worksheets/sheet{index}.xml"/>'
            )
            workbook_sheets.append(
                f'<sheet name="{_xml_escape(_sheet_name(sheet.name))}" '
                f'sheetId="{index}" r:id="rId{index}"/>'
            )
            archive.writestr(
                f"xl/worksheets/sheet{index}.xml",
                _worksheet_xml(sheet.rows),
            )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            _workbook_rels_xml(workbook_rels),
        )
        archive.writestr("xl/styles.xml", _styles_xml())
    return output.getvalue()


def _content_types_xml(sheet_count: int) -> str:
    overrides = "\n".join(
        [
            '<Override PartName="/xl/workbook.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
            '<Override PartName="/xl/styles.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
            *[
                f'<Override PartName="/xl/worksheets/sheet{index}.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                for index in range(1, sheet_count + 1)
            ],
        ]
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        f"{overrides}</Types>"
    )


def _root_rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        "</Relationships>"
    )


def _workbook_xml(sheets: Sequence[_WorkbookSheet]) -> str:
    sheet_nodes = "".join(
        [
            f'<sheet name="{_xml_escape(_sheet_name(sheet.name))}" sheetId="{index}" r:id="rId{index}"/>'
            for index, sheet in enumerate(sheets, start=1)
        ]
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{sheet_nodes}</sheets></workbook>"
    )


def _workbook_rels_xml(relationships: Sequence[str]) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{''.join(relationships)}</Relationships>"
    )


def _styles_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="1"><font><sz val="11"/><name val="Aptos"/></font></fonts>'
        '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
        '<borders count="1"><border/></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
        '</styleSheet>'
    )


def _worksheet_xml(rows: Sequence[Sequence[str]]) -> str:
    row_nodes = []
    for row_index, row in enumerate(rows, start=1):
        cell_nodes = []
        for column_index, value in enumerate(row, start=1):
            coordinate = f"{_column_letter(column_index)}{row_index}"
            cell_nodes.append(
                f'<c r="{coordinate}" t="inlineStr"><is><t xml:space="preserve">'
                f"{_xml_escape(value)}"
                "</t></is></c>"
            )
        row_nodes.append(f'<row r="{row_index}">{"".join(cell_nodes)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(row_nodes)}</sheetData></worksheet>"
    )


def _column_letter(index: int) -> str:
    letters = []
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters.append(chr(65 + remainder))
    return "".join(reversed(letters))


def _recognise_sheet(name: str) -> str | None:
    normalised = _normalise_header(name)
    for section, aliases in _SECTION_ALIASES.items():
        if normalised in {_normalise_header(alias) for alias in aliases}:
            return section
    return None


def _normalise_header(value: str) -> str:
    return _HEADER_SANITIZE_RE.sub(" ", value.strip().lower()).strip()


def _assign_path(target: dict[str, Any], dotted_path: str, value: Any) -> None:
    current = target
    parts = dotted_path.split(".")
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = value


def _nested_get(target: Mapping[str, Any], *path: str) -> Any:
    current: Any = target
    for part in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(part)
    return current


def _first_alias_value(values: Mapping[str, str], aliases: Iterable[str]) -> str | None:
    for alias in aliases:
        candidate = values.get(_normalise_header(alias))
        if candidate not in (None, ""):
            return candidate
    return None


def _split_notes(value: str | None) -> list[str]:
    if not value:
        return []
    parts = re.split(r"\s*\|\s*|\n+", value)
    return [part.strip() for part in parts if part.strip()]


def _drop_none_values(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: item
        for key, item in value.items()
        if item is not None and item != [] and item != {}
    }


def _drop_empty_sections(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, dict):
            nested = _drop_empty_sections(value)
            if nested:
                cleaned[key] = nested
        elif value not in (None, "", [], {}):
            cleaned[key] = value
    return cleaned


def _to_optional_int(value: str | None) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(Decimal(value))
    except Exception:
        return None


def _to_optional_bool(value: str | None) -> bool | None:
    if value in (None, ""):
        return None
    lowered = value.strip().lower()
    if lowered in {"true", "yes", "1", "y"}:
        return True
    if lowered in {"false", "no", "0", "n"}:
        return False
    return None


def _sheet_name(value: str) -> str:
    cleaned = value.strip() or "Sheet"
    return cleaned[:_EXCEL_MAX_SHEET_NAME]


def _xml_escape(value: Any) -> str:
    text = _stringify(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Decimal):
        return format(value, "f")
    return str(value)
