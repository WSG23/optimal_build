"""GPS logging and preview job API endpoints for developer workspace."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Sequence
from uuid import UUID, uuid4

import structlog
from backend._compat.datetime import utcnow
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.agents import CoordinatePair, QuickAnalysisEnvelope
from app.api.v1.developers_common import (
    DeveloperAssetOptimization,
    DeveloperBuildEnvelope,
    DeveloperCashFlowMilestone,
    DeveloperCapitalStructureScenario,
    DeveloperColorLegendEntry,
    DeveloperConstraintViolation,
    DeveloperDebtFacility,
    DeveloperEquityWaterfall,
    DeveloperEquityWaterfallTier,
    DeveloperExitAssumptions,
    DeveloperFinanceBlueprint,
    DeveloperFinancialSummary,
    DeveloperMassingLayer,
    DeveloperSensitivityBand,
    DeveloperVisualizationSummary,
    PreviewJobSchema,
    _coerce_float,
    _convert_area_to_sqm,
    _convert_rent_to_psm,
    _decimal_or_none,
    _round_optional,
    _serialise_preview_job,
    _to_mapping,
)
from app.core.config import settings
from app.core.database import get_session
from app.core.jwt_auth import TokenData, get_optional_user
from app.api.deps import RequestIdentity, require_reviewer
from app.models.property import Property
from app.models.projects import Project, ProjectPhase, ProjectType
from app.schemas.external_sources import ExternalSourceMetadata
from app.schemas.finance import FinanceAssetMixInput
from app.services.finance_project_creation import (
    create_finance_project_from_capture,
)
from app.services.agents.gps_property_logger import (
    DevelopmentScenario as CaptureScenario,
    GPSPropertyLogger,
    PropertyLogResult,
)
from app.services.developer_checklist_service import DeveloperChecklistService
from app.services.asset_mix import AssetOptimizationOutcome, build_asset_mix
from app.services import preview_generator
from app.services.geocoding import Address
from app.services.jurisdictions import get_jurisdiction_config
from app.services.preview_jobs import PreviewJobService, PreviewJobStatus
from app.utils.lazy import LazyProxy
from app.schemas._typing import copy_model

router = APIRouter(prefix="/developers", tags=["developers"])
logger = structlog.get_logger()


def _create_developer_geocoding() -> object:
    from app.services.geocoding import GeocodingService

    return GeocodingService()


def _create_developer_ura() -> object:
    from app.services.agents.ura_integration import URAIntegrationService

    return URAIntegrationService()


def _create_developer_gps_logger() -> object:
    return GPSPropertyLogger(
        _developer_geocoding.instance,
        _developer_ura.instance,
    )


_developer_geocoding = LazyProxy(_create_developer_geocoding)
_developer_ura = LazyProxy(_create_developer_ura)
developer_gps_logger = LazyProxy(_create_developer_gps_logger)


# =============================================================================
# Asset Type Colors and Formatting
# =============================================================================

_ASSET_TYPE_COLORS: dict[str, str] = {
    "office": "#1C7ED6",
    "retail": "#F76707",
    "hospitality": "#F59F00",
    "amenities": "#12B886",
    "serviced_apartments": "#845EF7",
    "residential": "#5C7CFA",
    "high-spec logistics": "#339AF0",
    "high_spec_logistics": "#339AF0",
    "production": "#FF922B",
    "support services": "#20C997",
    "support_services": "#20C997",
}


def _resolve_asset_color(asset_type: str) -> str:
    key = asset_type.lower().replace("-", "_").replace(" ", "_")
    if key in _ASSET_TYPE_COLORS:
        return _ASSET_TYPE_COLORS[key]
    if asset_type.lower() in _ASSET_TYPE_COLORS:
        return _ASSET_TYPE_COLORS[asset_type.lower()]
    return "#ADB5BD"


def _format_asset_label(value: str) -> str:
    cleaned = value.replace("_", " ").replace("-", " ").strip()
    if not cleaned:
        return value
    return cleaned.title()


# =============================================================================
# Heritage Context Extraction
# =============================================================================


def _extract_heritage_context(
    envelope: DeveloperBuildEnvelope,
    property_info: dict[str, Any] | None,
    quick_analysis: dict[str, Any] | None,
    heritage_overlay: dict[str, Any] | None,
) -> dict[str, Any]:
    constraints: list[str] = []
    notes: list[str] = []
    risk: str | None = None
    flag = False

    if envelope.zone_description and "heritage" in envelope.zone_description.lower():
        flag = True
        constraints.append(f"Zoning guidance: {envelope.zone_description}")
    for assumption in envelope.assumptions or []:
        if "heritage" in assumption.lower():
            flag = True
            constraints.append(str(assumption))

    if heritage_overlay:
        flag = True
        overlay_name = heritage_overlay.get("name")
        overlay_source = heritage_overlay.get("source")
        overlay_notes = heritage_overlay.get("notes") or []
        overlay_risk = heritage_overlay.get("risk")
        if overlay_risk:
            risk = str(overlay_risk).lower()
        if overlay_name:
            constraints.append(f"Overlay: {overlay_name}")
        if overlay_source:
            notes.append(f"Source: {overlay_source}")
        for note in overlay_notes:
            text = str(note).strip()
            if text:
                notes.append(text)
                constraints.append(text)
        premium = heritage_overlay.get("heritage_premium_pct")
        if premium:
            notes.append(f"Estimated heritage premium: {premium}% fit-out uplift")

    property_mapping = _to_mapping(property_info)
    if property_mapping:
        for key in (
            "heritage_constraints",
            "conservation_requirements",
            "heritage_notes",
        ):
            value = property_mapping.get(key)
            if isinstance(value, Sequence):
                for item in value:
                    text = str(item).strip()
                    if text:
                        constraints.append(text)
                        flag = True
        for key in (
            "heritage_status",
            "conservation_status",
            "ura_conservation_category",
        ):
            status = property_mapping.get(key)
            if status:
                flag = True
                status_text = str(status).lower()
                if any(
                    token in status_text
                    for token in ("national", "strict", "conserved")
                ):
                    risk = risk or "high"
                else:
                    risk = risk or "medium"

        if property_mapping.get("is_conservation"):
            flag = True
            risk = risk or "high"
            constraints.append("Property flagged as conservation asset.")

    qa_mapping = _to_mapping(quick_analysis)
    if qa_mapping:
        scenarios = qa_mapping.get("scenarios")
        if isinstance(scenarios, Sequence):
            for entry in scenarios:
                scenario = _to_mapping(entry)
                if not scenario:
                    continue
                scenario_name = str(scenario.get("scenario", "")).lower()
                if (
                    "heritage" not in scenario_name
                    and "conservation" not in scenario_name
                ):
                    continue
                metrics = _to_mapping(scenario.get("metrics"))
                qa_risk = None
                qa_signal = False
                if metrics:
                    qa_risk = metrics.get("heritage_risk") or metrics.get("risk_level")
                    qa_signal = bool(metrics.get("heritage_signal"))
                if qa_risk:
                    risk = str(qa_risk).lower()
                    qa_signal = qa_signal or risk in {"medium", "high"}
                if not qa_signal:
                    continue
                flag = True
                scenario_notes = scenario.get("notes")
                if isinstance(scenario_notes, Sequence):
                    for note in scenario_notes:
                        text = str(note).strip()
                        if text:
                            notes.append(text)
                            constraints.append(text)

    seen: set[str] = set()
    deduped_constraints: list[str] = []
    for item in constraints:
        text = str(item).strip()
        if not text:
            continue
        key = text.lower()
        if key not in seen:
            seen.add(key)
            deduped_constraints.append(text)

    if risk:
        risk = risk.lower()
    else:
        risk = "low"
    flag = flag or bool(deduped_constraints)

    assumption_note = None
    if flag:
        if risk == "high":
            assumption_note = "Heritage overlay detected (high sensitivity)."
        elif risk == "medium":
            assumption_note = (
                "Heritage overlay detected (monitor compliance requirements)."
            )
        else:
            assumption_note = "Heritage overlay detected; confirm authority guidance."

    return {
        "flag": flag,
        "risk": risk,
        "constraints": deduped_constraints,
        "notes": notes,
        "assumption": assumption_note,
        "overlay": heritage_overlay,
    }


def _collect_quick_metrics(
    quick_analysis: dict[str, Any] | None,
) -> dict[str, float | str]:
    if not quick_analysis:
        return {}
    mapping = _to_mapping(quick_analysis)
    if mapping is None:
        return {}
    scenarios = mapping.get("scenarios")
    if not isinstance(scenarios, Sequence):
        return {}

    metrics: dict[str, float | str] = {}

    def _coerce_float_inner(value: object) -> float | None:
        if value is None:
            return None
        if not isinstance(value, (str, bytes, bytearray, int, float)):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    for entry in scenarios:
        scenario_map = _to_mapping(entry)
        if scenario_map is None:
            continue
        scenario_name = str(scenario_map.get("scenario", "")).lower()
        raw_metrics = _to_mapping(scenario_map.get("metrics"))
        if raw_metrics is None:
            continue
        lower_metrics = {str(key).lower(): value for key, value in raw_metrics.items()}

        if scenario_name == "heritage_property":
            heritage_risk = lower_metrics.get("heritage_risk") or lower_metrics.get(
                "risk_level"
            )
            if isinstance(heritage_risk, str):
                metrics["heritage_risk"] = heritage_risk

        if scenario_name == "existing_building":
            vacancy = lower_metrics.get("vacancy_rate") or lower_metrics.get(
                "vacancy_pct"
            )
            vacancy = vacancy or lower_metrics.get("vacancy_percent")
            vacancy_value = _coerce_float_inner(vacancy)
            if vacancy_value is not None:
                if vacancy_value > 1:
                    vacancy_value /= 100.0
                metrics["existing_vacancy_rate"] = vacancy_value

            avg_rent = (
                lower_metrics.get("average_monthly_rent")
                or lower_metrics.get("average_rent_psm")
                or lower_metrics.get("avg_rent_psm")
            )
            avg_rent_value = _coerce_float_inner(avg_rent)
            if avg_rent_value is not None:
                metrics["existing_average_rent_psm"] = avg_rent_value

        if scenario_name == "underused_asset":
            mrt_count = lower_metrics.get("nearby_mrt_count")
            mrt_value = _coerce_float_inner(mrt_count)
            if mrt_value is not None:
                metrics["underused_mrt_count"] = mrt_value

    return metrics


# =============================================================================
# Build Envelope and Asset Optimization
# =============================================================================


def _mark_envelope_field_source(
    *,
    resolved_by: dict[str, str],
    unresolved_fields: list[str],
    field: str,
    source: str,
) -> None:
    if field not in resolved_by:
        resolved_by[field] = source
    while field in unresolved_fields:
        unresolved_fields.remove(field)


def _augment_rule_corpus_status_for_envelope(
    raw_status: dict[str, Any] | None,
    *,
    zone_description: object | None,
    plot_ratio: float | None,
    building_height_limit: float | None,
    site_coverage: float | None,
    setback_front: float | None,
    setback_rear: float | None,
    setback_side: float | None,
    step_backs: list[object],
    air_rights_note: str | None,
) -> dict[str, Any] | None:
    if not raw_status:
        return None

    status = dict(raw_status)
    resolved_by = dict(status.get("resolved_by") or {})
    unresolved_fields = [
        str(field)
        for field in status.get("unresolved_fields") or []
        if field is not None
    ]

    # The rule resolver reports RefRule/zoning-layer sources only. The final
    # envelope can still use captured zoning metadata, so record those fields as
    # resolved-by-capture instead of leaving them listed as unresolved.
    if zone_description:
        _mark_envelope_field_source(
            resolved_by=resolved_by,
            unresolved_fields=unresolved_fields,
            field="land_use",
            source="captured_zoning_metadata",
        )
    if plot_ratio is not None:
        _mark_envelope_field_source(
            resolved_by=resolved_by,
            unresolved_fields=unresolved_fields,
            field="plot_ratio",
            source="captured_zoning_metadata",
        )
    if building_height_limit is not None:
        _mark_envelope_field_source(
            resolved_by=resolved_by,
            unresolved_fields=unresolved_fields,
            field="building_height_limit_m",
            source="captured_zoning_metadata",
        )
    if site_coverage is not None:
        _mark_envelope_field_source(
            resolved_by=resolved_by,
            unresolved_fields=unresolved_fields,
            field="site_coverage_pct",
            source="captured_zoning_metadata",
        )
    if any(value is not None for value in (setback_front, setback_rear, setback_side)):
        _mark_envelope_field_source(
            resolved_by=resolved_by,
            unresolved_fields=unresolved_fields,
            field="setbacks",
            source="captured_development_constraints",
        )
    if step_backs:
        _mark_envelope_field_source(
            resolved_by=resolved_by,
            unresolved_fields=unresolved_fields,
            field="step_backs",
            source="captured_development_constraints",
        )
    if air_rights_note:
        _mark_envelope_field_source(
            resolved_by=resolved_by,
            unresolved_fields=unresolved_fields,
            field="air_rights_note",
            source="captured_development_constraints",
        )

    status["resolved_by"] = resolved_by
    status["unresolved_fields"] = unresolved_fields
    source_gaps = status.get("official_source_gaps")
    if isinstance(source_gaps, list):
        status["official_source_gaps"] = [
            entry
            for entry in source_gaps
            if not (isinstance(entry, dict) and str(entry.get("field")) in resolved_by)
        ]

    captured_sources_present = any(
        str(source).startswith("captured_") for source in resolved_by.values()
    )
    if unresolved_fields or captured_sources_present:
        status["coverage_state"] = "partial"
        status["confidence"] = status.get("confidence") or "medium"
    else:
        status["coverage_state"] = "approved"
        status["confidence"] = status.get("confidence") or "medium"

    return status


def _source_gap_has_configured_value(
    gap: dict[str, Any],
    *,
    zone_code: str | None,
) -> bool:
    """Return true when a source gap can be resolved from reviewed registry data."""

    if not zone_code:
        return False
    candidate_sources = gap.get("candidate_sources")
    if not isinstance(candidate_sources, list):
        return False

    zone_key = zone_code.lower()
    for source in candidate_sources:
        if not isinstance(source, dict):
            continue
        values_by_zone = source.get("configured_values_by_zone")
        if not isinstance(values_by_zone, dict):
            continue
        if any(
            str(candidate_zone).lower() == zone_key for candidate_zone in values_by_zone
        ):
            return True
    return False


async def _derive_build_envelope(
    result: PropertyLogResult,
    session: AsyncSession,
    jurisdiction: str = "SG",
) -> DeveloperBuildEnvelope:
    """Construct zoning/buildability summary from RefRule database.

    Queries the RefRule database for zoning parameters (plot ratio, height limits,
    site coverage) instead of using hardcoded mock values from URAIntegrationService.
    """
    from app.services.rules.zone_rules import get_zoning_rules_for_zone

    ura_data = result.ura_zoning or {}
    property_info = result.property_info or {}

    # Get zone code from URA service (still used for zone identification)
    raw_zone_code = ura_data.get("zone_code") or ura_data.get("zoneCode")

    # Query RefRule database for zoning parameters
    rules_result = await get_zoning_rules_for_zone(
        session=session,
        zone_code=raw_zone_code,
        jurisdiction=jurisdiction,
    )

    development_constraints = property_info.get("development_constraints")
    if not isinstance(development_constraints, dict):
        development_constraints = property_info.get("developmentConstraints")
    if not isinstance(development_constraints, dict):
        development_constraints = {}

    fallback_plot_ratio = _coerce_float(
        ura_data.get("plot_ratio") or ura_data.get("plotRatio")
    )
    fallback_zone_code = str(raw_zone_code) if raw_zone_code else None
    fallback_zone_description = ura_data.get("zone_description") or ura_data.get(
        "zoneDescription"
    )
    fallback_building_height_limit = _coerce_float(
        ura_data.get("building_height_limit") or ura_data.get("buildingHeightLimit")
    )
    fallback_site_coverage = _coerce_float(
        ura_data.get("site_coverage") or ura_data.get("siteCoverage")
    )
    fallback_setback_front = _coerce_float(
        development_constraints.get("setback_front_m")
        or development_constraints.get("front_setback_m")
        or ura_data.get("setback_front_m")
        or ura_data.get("setbackFrontM")
    )
    fallback_setback_rear = _coerce_float(
        development_constraints.get("setback_rear_m")
        or development_constraints.get("rear_setback_m")
        or ura_data.get("setback_rear_m")
        or ura_data.get("setbackRearM")
    )
    fallback_setback_side = _coerce_float(
        development_constraints.get("setback_side_m")
        or development_constraints.get("side_setback_m")
        or ura_data.get("setback_side_m")
        or ura_data.get("setbackSideM")
    )
    raw_step_backs = (
        development_constraints.get("step_backs")
        or development_constraints.get("stepBacks")
        or ura_data.get("step_backs")
        or ura_data.get("stepBacks")
    )
    fallback_step_backs = raw_step_backs if isinstance(raw_step_backs, list) else []
    fallback_air_rights_note = (
        development_constraints.get("air_rights_note")
        or development_constraints.get("airRightsNote")
        or ura_data.get("air_rights_note")
        or ura_data.get("airRightsNote")
    )
    fallback_air_rights_note = (
        str(fallback_air_rights_note) if fallback_air_rights_note else None
    )

    # Use rules data if available, otherwise fall back to URA service data
    if rules_result.has_data:
        plot_ratio = rules_result.plot_ratio or fallback_plot_ratio
        zone_code = fallback_zone_code or rules_result.zone_code
        zone_description = fallback_zone_description or rules_result.zone_description
        building_height_limit = (
            rules_result.building_height_limit_m or fallback_building_height_limit
        )
        site_coverage = rules_result.site_coverage_pct or fallback_site_coverage
        setback_front = rules_result.setback_front_m or fallback_setback_front
        setback_rear = rules_result.setback_rear_m or fallback_setback_rear
        setback_side = rules_result.setback_side_m or fallback_setback_side
        step_backs = rules_result.step_backs or fallback_step_backs
        air_rights_note = rules_result.air_rights_note or fallback_air_rights_note
        source_reference = rules_result.source_reference
    else:
        # Fallback to URA service data (mocked)
        plot_ratio = fallback_plot_ratio
        zone_code = fallback_zone_code
        zone_description = fallback_zone_description
        building_height_limit = fallback_building_height_limit
        site_coverage = fallback_site_coverage
        setback_front = fallback_setback_front
        setback_rear = fallback_setback_rear
        setback_side = fallback_setback_side
        step_backs = fallback_step_backs
        air_rights_note = fallback_air_rights_note
        source_reference = rules_result.source_reference

    site_area = _coerce_float(
        property_info.get("site_area_sqm") or property_info.get("siteAreaSqm")
    )
    current_gfa = _coerce_float(
        property_info.get("gross_floor_area_sqm")
        or property_info.get("grossFloorAreaSqm")
        or property_info.get("gfa_approved")
        or property_info.get("gfaApproved")
    )

    max_buildable: Optional[float]
    if site_area is not None and plot_ratio is not None:
        max_buildable = site_area * plot_ratio
    else:
        max_buildable = None

    additional: Optional[float] = None
    if max_buildable is not None and current_gfa is not None:
        additional = max(max_buildable - current_gfa, 0.0)

    rule_corpus_status = _augment_rule_corpus_status_for_envelope(
        rules_result.rule_corpus_status,
        zone_description=zone_description,
        plot_ratio=plot_ratio,
        building_height_limit=building_height_limit,
        site_coverage=site_coverage,
        setback_front=setback_front,
        setback_rear=setback_rear,
        setback_side=setback_side,
        step_backs=step_backs,
        air_rights_note=air_rights_note,
    )
    if rule_corpus_status:
        source_gaps = rule_corpus_status.get("official_source_gaps")
        if isinstance(source_gaps, list) and source_gaps:
            normalized_status_zone = (
                str(rule_corpus_status.get("zone_code"))
                if rule_corpus_status.get("zone_code")
                else None
            )
            source_gaps_to_ingest = [
                gap
                for gap in source_gaps
                if isinstance(gap, dict)
                and (
                    settings.CAPTURE_LIVE_SOURCE_SCAN_ENABLED
                    or _source_gap_has_configured_value(
                        gap,
                        zone_code=normalized_status_zone,
                    )
                )
            ]
            if not source_gaps_to_ingest:
                source_gaps = []
        if isinstance(source_gaps, list) and source_gaps:
            try:
                from app.services.rules.official_source_ingestion import (
                    OfficialSourceIngestionService,
                )

                ingestion_result = (
                    await OfficialSourceIngestionService().ingest_source_gaps(
                        session,
                        jurisdiction=jurisdiction,
                        zone_code=normalized_status_zone,
                        source_gaps=source_gaps_to_ingest,
                    )
                )
                rule_corpus_status["official_source_ingestion"] = (
                    ingestion_result.as_rule_corpus_payload()
                )
                if ingestion_result.resolved_count:
                    rules_result = await get_zoning_rules_for_zone(
                        session=session,
                        zone_code=raw_zone_code,
                        jurisdiction=jurisdiction,
                    )
                    if rules_result.has_data:
                        plot_ratio = rules_result.plot_ratio or fallback_plot_ratio
                        zone_code = fallback_zone_code or rules_result.zone_code
                        zone_description = (
                            fallback_zone_description or rules_result.zone_description
                        )
                        building_height_limit = (
                            rules_result.building_height_limit_m
                            or fallback_building_height_limit
                        )
                        site_coverage = (
                            rules_result.site_coverage_pct or fallback_site_coverage
                        )
                        setback_front = (
                            rules_result.setback_front_m or fallback_setback_front
                        )
                        setback_rear = (
                            rules_result.setback_rear_m or fallback_setback_rear
                        )
                        setback_side = (
                            rules_result.setback_side_m or fallback_setback_side
                        )
                        step_backs = rules_result.step_backs or fallback_step_backs
                        air_rights_note = (
                            rules_result.air_rights_note or fallback_air_rights_note
                        )
                        source_reference = rules_result.source_reference

                    if site_area is not None and plot_ratio is not None:
                        max_buildable = site_area * plot_ratio
                    else:
                        max_buildable = None
                    if max_buildable is not None and current_gfa is not None:
                        additional = max(max_buildable - current_gfa, 0.0)
                    else:
                        additional = None

                    rule_corpus_status = _augment_rule_corpus_status_for_envelope(
                        rules_result.rule_corpus_status,
                        zone_description=zone_description,
                        plot_ratio=plot_ratio,
                        building_height_limit=building_height_limit,
                        site_coverage=site_coverage,
                        setback_front=setback_front,
                        setback_rear=setback_rear,
                        setback_side=setback_side,
                        step_backs=step_backs,
                        air_rights_note=air_rights_note,
                    )
                    if rule_corpus_status is not None:
                        rule_corpus_status["official_source_ingestion"] = (
                            ingestion_result.as_rule_corpus_payload()
                        )
            except Exception as exc:
                logger.warning(
                    "Capture official source ingestion failed",
                    jurisdiction=jurisdiction,
                    error=str(exc),
                )
                if rule_corpus_status is not None:
                    rule_corpus_status["official_source_ingestion"] = {
                        "status": "failed",
                        "message": str(exc),
                    }

    assumptions: list[str] = []
    if plot_ratio is not None and site_area is not None:
        assumptions.append(
            f"Plot ratio {plot_ratio:g} applied to {site_area:,.0f} sqm site area."
        )
    if zone_description:
        assumptions.append(
            f"Envelope derived from {str(zone_description).lower()} zoning rules."
        )
    if rules_result.rules_found > 0:
        assumptions.append(f"Data from {rules_result.rules_found} RefRule entries.")
    resolved_deeper_controls = []
    if any(value is not None for value in (setback_front, setback_rear, setback_side)):
        resolved_deeper_controls.append("setbacks")
    if step_backs:
        resolved_deeper_controls.append("step-backs")
    if air_rights_note:
        resolved_deeper_controls.append("air-rights note")
    if resolved_deeper_controls:
        assumptions.append(
            "Resolved deeper controls: " + ", ".join(resolved_deeper_controls) + "."
        )
    corpus_status = rule_corpus_status or {}
    if corpus_status:
        coverage_state = corpus_status.get("coverage_state")
        confidence = corpus_status.get("confidence")
        counts = corpus_status.get("counts") or {}
        approved_count = counts.get("approved", 0)
        needs_review_count = counts.get("needs_review", 0)
        if coverage_state == "partial":
            assumptions.append(
                "Rule corpus partially approved; verify unresolved zoning controls before underwriting."
            )
        elif coverage_state == "review_pending":
            assumptions.append(
                "Rule corpus exists but is pending review; treat envelope outputs as provisional."
            )
        elif coverage_state == "missing":
            assumptions.append(
                "No configured rule values were resolved for this zone; envelope falls back to captured zoning metadata while official sources are ingested."
            )
        elif coverage_state == "approved":
            assumptions.append(
                f"Rule corpus approved with {approved_count} published entries ({confidence} confidence)."
            )
        source_gaps = corpus_status.get("official_source_gaps")
        if isinstance(source_gaps, list) and source_gaps:
            gap_fields = [
                str(entry.get("field"))
                for entry in source_gaps
                if isinstance(entry, dict) and entry.get("field")
            ]
            if gap_fields:
                assumptions.append(
                    "Official Singapore source ingestion still required for: "
                    + ", ".join(gap_fields[:4])
                    + ("." if len(gap_fields) <= 4 else ", ...")
                )
        if needs_review_count:
            assumptions.append(
                f"{needs_review_count} zoning rule entries still require review."
            )
    if not assumptions:
        assumptions.append(
            "Plot ratio or site area unavailable; envelope estimated from captured metadata."
        )

    return DeveloperBuildEnvelope(
        zone_code=str(zone_code) if zone_code else None,
        zone_description=str(zone_description) if zone_description else None,
        site_area_sqm=_round_optional(site_area),
        allowable_plot_ratio=_round_optional(plot_ratio),
        max_buildable_gfa_sqm=_round_optional(max_buildable),
        current_gfa_sqm=_round_optional(current_gfa),
        additional_potential_gfa_sqm=_round_optional(additional),
        building_height_limit_m=_round_optional(building_height_limit),
        site_coverage_pct=_round_optional(site_coverage),
        setback_front_m=_round_optional(setback_front),
        setback_rear_m=_round_optional(setback_rear),
        setback_side_m=_round_optional(setback_side),
        step_backs=[
            {
                "level": _round_optional(_coerce_float(entry.get("level"))) or 0,
                "depth_m": _round_optional(_coerce_float(entry.get("depth_m")))
                or _round_optional(_coerce_float(entry.get("depthM")))
                or 0,
            }
            for entry in step_backs
            if isinstance(entry, dict)
        ],
        air_rights_note=air_rights_note,
        assumptions=assumptions,
        source_reference=source_reference,
        rule_corpus_status=rule_corpus_status,
    )


def _build_visualization_summary(
    quick_analysis: dict[str, Any] | None,
    property_id: UUID,
    optimizations: list[DeveloperAssetOptimization],
    envelope: DeveloperBuildEnvelope,
) -> DeveloperVisualizationSummary:
    """Return messaging about 3D preview readiness."""

    scenario_count = 0
    if quick_analysis and isinstance(quick_analysis.get("scenarios"), list):
        scenario_count = len(quick_analysis["scenarios"])

    notes: list[str] = []
    if scenario_count:
        plural = "s" if scenario_count != 1 else ""
        notes.append(
            f"{scenario_count} scenario{plural} prepared for feasibility review."
        )
    notes.append(
        "Preview generation queued. High-fidelity renders will replace the stub when ready."
    )

    camera_orbit = {"theta": 48.0, "phi": 32.0, "radius": 1.6}

    massing_layers: list[DeveloperMassingLayer] = []
    legend_entries: dict[str, DeveloperColorLegendEntry] = {}
    site_area = envelope.site_area_sqm or 0.0

    for opt in optimizations:
        gfa = opt.allocated_gfa_sqm
        nia = None
        if gfa is not None and opt.nia_efficiency:
            nia = gfa * opt.nia_efficiency
        height = None
        if site_area and site_area > 0 and gfa:
            floor_height = opt.target_floor_height_m or 4.0
            height = (gfa / site_area) * floor_height
        color = _resolve_asset_color(opt.asset_type)
        massing_layers.append(
            DeveloperMassingLayer(
                asset_type=opt.asset_type,
                allocation_pct=opt.allocation_pct,
                gfa_sqm=round(gfa, 2) if gfa is not None else None,
                nia_sqm=round(nia, 2) if nia is not None else None,
                estimated_height_m=round(height, 1) if height is not None else None,
                color=color,
            )
        )
        legend_entries.setdefault(
            opt.asset_type,
            DeveloperColorLegendEntry(
                asset_type=opt.asset_type,
                label=_format_asset_label(opt.asset_type),
                color=color,
                description=(
                    f"Risk level: {opt.risk_level.title()}" if opt.risk_level else None
                ),
            ),
        )

    massing_layers.sort(key=lambda layer: layer.allocation_pct, reverse=True)
    color_legend: list[DeveloperColorLegendEntry] = []
    seen_assets: set[str] = set()
    for layer in massing_layers:
        entry = legend_entries.get(layer.asset_type)
        if entry and entry.asset_type not in seen_assets:
            color_legend.append(entry)
            seen_assets.add(entry.asset_type)

    if massing_layers:
        primary = massing_layers[0]
        label = _format_asset_label(primary.asset_type)
        if primary.estimated_height_m:
            summary_note = f"{label} stack drives the stub massing (~{primary.estimated_height_m:.0f} m)."
        else:
            summary_note = (
                f"{label} stack drives {primary.allocation_pct:.0f}% of the programme."
            )
        if summary_note not in notes:
            notes.append(summary_note)

    return DeveloperVisualizationSummary(
        status=PreviewJobStatus.QUEUED.value,
        preview_available=False,
        notes=notes,
        concept_mesh_url=None,
        preview_metadata_url=None,
        camera_orbit_hint=camera_orbit,
        preview_seed=scenario_count or 1,
        massing_layers=massing_layers,
        color_legend=color_legend,
    )


async def _build_property_preview_inputs(
    property_record: Property,
    session: AsyncSession,
    scenario: str,
) -> tuple[
    DeveloperBuildEnvelope,
    DeveloperVisualizationSummary,
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
]:
    """Derive preview-job inputs from a persisted property record."""

    existing_use = (
        property_record.property_type.value
        if hasattr(property_record.property_type, "value")
        else str(property_record.property_type or "existing_building")
    )
    property_info: dict[str, Any] = {
        "site_area_sqm": (
            float(property_record.land_area_sqm)
            if property_record.land_area_sqm is not None
            else None
        ),
        "gross_floor_area_sqm": (
            float(property_record.gross_floor_area_sqm)
            if property_record.gross_floor_area_sqm is not None
            else None
        ),
        "gfa_approved": (
            float(property_record.gross_floor_area_sqm)
            if property_record.gross_floor_area_sqm is not None
            else None
        ),
        "building_height": (
            float(property_record.building_height_m)
            if property_record.building_height_m is not None
            else None
        ),
        "floors_above_ground": property_record.floors_above_ground,
        "year_built": property_record.year_built,
        "is_conservation": bool(property_record.is_conservation),
        "conservation_status": property_record.conservation_status,
        "heritage_overlay": property_record.conservation_status,
    }
    pseudo_result = PropertyLogResult(
        property_id=property_record.id,
        address=Address(
            full_address=property_record.address,
            district=property_record.district,
        ),
        coordinates=(0.0, 0.0),
        ura_zoning={
            "zone_code": property_record.zoning_code,
            "plot_ratio": (
                float(property_record.plot_ratio)
                if property_record.plot_ratio is not None
                else None
            ),
            "building_height_limit": (
                float(property_record.building_height_m)
                if property_record.building_height_m is not None
                else None
            ),
        },
        existing_use=existing_use,
        property_info=property_info,
        nearby_amenities=None,
        quick_analysis=None,
        heritage_overlay=(
            {"name": property_record.conservation_status}
            if property_record.is_conservation or property_record.conservation_status
            else None
        ),
        jurisdiction_code=property_record.jurisdiction_code or "SG",
    )

    envelope = await _derive_build_envelope(
        pseudo_result,
        session,
        property_record.jurisdiction_code or "SG",
    )
    (
        scenario_envelope,
        scenario_land_use,
        scenario_existing_use,
        scenario_heritage_overlay,
        scenario_quick_metrics,
    ) = _apply_preview_scenario_rules(
        envelope,
        existing_use=existing_use,
        heritage_overlay=pseudo_result.heritage_overlay,
        scenario=scenario,
    )
    engineering_assumptions = _build_preview_engineering_assumptions(
        scenario=scenario,
        property_info=property_info,
        existing_use=scenario_existing_use,
        heritage_overlay=scenario_heritage_overlay,
    )
    optimizations, _, _ = _build_asset_optimizations(
        scenario_land_use,
        scenario_envelope,
        scenario_existing_use,
        property_info,
        {"scenarios": [{"scenario": scenario, "metrics": scenario_quick_metrics}]},
        scenario_heritage_overlay,
    )
    optimizations = _apply_preview_engineering_defaults(
        optimizations,
        engineering_assumptions=engineering_assumptions,
        site_area_sqm=scenario_envelope.site_area_sqm,
    )
    engineering_assumptions["asset_profiles"] = _build_preview_asset_profiles(
        optimizations,
        engineering_assumptions=engineering_assumptions,
    )
    visualization = _build_visualization_summary(
        None,
        property_record.id,
        optimizations,
        scenario_envelope,
    )
    _append_visualization_assumption_notes(visualization, engineering_assumptions)
    massing_payload = [
        layer.model_dump() if hasattr(layer, "model_dump") else layer.__dict__
        for layer in visualization.massing_layers
    ]
    legend_payload = [
        entry.model_dump() if hasattr(entry, "model_dump") else entry.__dict__
        for entry in visualization.color_legend
    ]
    return (
        scenario_envelope,
        visualization,
        massing_payload,
        legend_payload,
        engineering_assumptions,
    )


def _apply_preview_scenario_rules(
    envelope: DeveloperBuildEnvelope,
    *,
    existing_use: str,
    heritage_overlay: dict[str, Any] | None,
    scenario: str,
) -> tuple[
    DeveloperBuildEnvelope,
    str,
    str | None,
    dict[str, Any] | None,
    dict[str, Any],
]:
    """Adjust preview inputs so starter models differ meaningfully by scenario."""

    scenario_key = scenario.strip().lower()
    current_gfa = envelope.current_gfa_sqm or 0.0
    max_gfa = envelope.max_buildable_gfa_sqm or current_gfa or None
    additional_gfa = (
        envelope.additional_potential_gfa_sqm
        if envelope.additional_potential_gfa_sqm is not None
        else (
            max(max_gfa - current_gfa, 0.0)
            if max_gfa is not None and current_gfa is not None
            else None
        )
    )
    assumptions = list(envelope.assumptions)
    primary_asset = _infer_primary_asset_type(existing_use)

    if scenario_key == "raw_land":
        assumptions.append(
            "Starter model uses a ground-up envelope assumption for raw land."
        )
        return (
            copy_model(
                envelope,
                update={
                    "current_gfa_sqm": 0.0,
                    "additional_potential_gfa_sqm": _round_optional(max_gfa),
                    "assumptions": assumptions,
                },
            ),
            "mixed_use",
            None,
            None,
            {
                "user_constraints": {
                    "min": {"office": 45.0, "retail": 15.0},
                    "max": {"amenities": 12.0},
                }
            },
        )

    if scenario_key == "existing_building":
        preserved_gfa = current_gfa or max_gfa
        assumptions.append(
            "Starter model preserves existing bulk as the renovation baseline."
        )
        return (
            copy_model(
                envelope,
                update={
                    "max_buildable_gfa_sqm": _round_optional(preserved_gfa),
                    "additional_potential_gfa_sqm": 0.0,
                    "assumptions": assumptions,
                },
            ),
            existing_use,
            existing_use,
            heritage_overlay,
            {
                "user_constraints": {
                    "min": {primary_asset: 65.0},
                    "max": {"retail": 20.0, "amenities": 10.0},
                }
            },
        )

    if scenario_key == "underused_asset":
        uplift = (
            additional_gfa * 0.5
            if additional_gfa is not None
            else (max((max_gfa or 0.0) - current_gfa, 0.0) * 0.5)
        )
        target_gfa = current_gfa + uplift if current_gfa > 0 else max_gfa
        assumptions.append(
            "Starter model applies moderate uplift to existing bulk for reuse potential."
        )
        underused_constraints = {
            "min": {primary_asset: 35.0, "retail": 15.0, "amenities": 10.0},
            "max": {"office": 55.0 if primary_asset == "office" else 45.0},
        }
        return (
            copy_model(
                envelope,
                update={
                    "max_buildable_gfa_sqm": _round_optional(target_gfa),
                    "additional_potential_gfa_sqm": _round_optional(uplift),
                    "assumptions": assumptions,
                },
            ),
            "mixed_use",
            existing_use,
            heritage_overlay,
            {"user_constraints": underused_constraints},
        )

    if scenario_key == "heritage_property":
        heritage_height = (
            envelope.building_height_limit_m * 0.75
            if envelope.building_height_limit_m is not None
            else None
        )
        preserved_gfa = current_gfa or (max_gfa * 0.75 if max_gfa is not None else None)
        assumptions.append(
            "Starter model applies conservative heritage retention assumptions."
        )
        return (
            copy_model(
                envelope,
                update={
                    "max_buildable_gfa_sqm": _round_optional(preserved_gfa),
                    "additional_potential_gfa_sqm": 0.0,
                    "building_height_limit_m": _round_optional(heritage_height),
                    "assumptions": assumptions,
                },
            ),
            "mixed_use",
            existing_use,
            heritage_overlay or {"name": "Heritage overlay detected", "risk": "medium"},
            {
                "user_constraints": {
                    "min": {"retail": 20.0, "amenities": 10.0},
                    "max": {"office": 45.0, "hospitality": 30.0},
                }
            },
        )

    return envelope, existing_use, existing_use, heritage_overlay, {}


def _infer_primary_asset_type(existing_use: str | None) -> str:
    use_lower = (existing_use or "").lower()
    if any(token in use_lower for token in ("retail", "mall", "shopping")):
        return "retail"
    if any(token in use_lower for token in ("hotel", "hospitality")):
        return "hospitality"
    if any(token in use_lower for token in ("residential", "apartment", "condo")):
        return "residential"
    if any(
        token in use_lower for token in ("industrial", "logistics", "manufacturing")
    ):
        return "industrial"
    return "office"


def _build_preview_engineering_assumptions(
    *,
    scenario: str,
    property_info: dict[str, Any] | None,
    existing_use: str | None,
    heritage_overlay: dict[str, Any] | None,
) -> dict[str, Any]:
    assumption_fields = (
        "wall_thickness_mm",
        "core_ratio_pct",
        "common_area_ratio_pct",
        "floor_to_floor_m",
        "clear_ceiling_m",
        "hvac_space_ratio_pct",
        "electrical_space_ratio_pct",
        "efficiency_factor",
        "retention_strategy",
    )
    scenario_key = scenario.strip().lower()
    year_built = property_info.get("year_built") if property_info else None
    existing_floors = (
        property_info.get("floors_above_ground") if property_info else None
    )
    conservation = bool(heritage_overlay) or bool(
        property_info and property_info.get("is_conservation")
    )

    assumptions: dict[str, Any] = {
        "wall_thickness_mm": 220,
        "core_ratio_pct": 16,
        "common_area_ratio_pct": 12,
        "floor_to_floor_m": 3.9,
        "clear_ceiling_m": 2.8,
        "hvac_space_ratio_pct": 8,
        "electrical_space_ratio_pct": 4,
        "efficiency_factor": 0.98,
        "retention_strategy": "adaptive_reuse_baseline",
    }
    field_sources: dict[str, str] = {
        field_name: "rules" for field_name in assumption_fields
    }
    adjustments: list[str] = []

    if scenario_key == "raw_land":
        assumptions.update(
            {
                "wall_thickness_mm": 260,
                "core_ratio_pct": 18,
                "common_area_ratio_pct": 15,
                "floor_to_floor_m": 4.2,
                "clear_ceiling_m": 3.2,
                "hvac_space_ratio_pct": 6,
                "electrical_space_ratio_pct": 3,
                "efficiency_factor": 1.02,
                "retention_strategy": "ground_up_envelope",
            }
        )
    elif scenario_key == "existing_building":
        assumptions.update(
            {
                "wall_thickness_mm": 210,
                "core_ratio_pct": 15,
                "common_area_ratio_pct": 11,
                "floor_to_floor_m": 3.7,
                "clear_ceiling_m": 2.7,
                "hvac_space_ratio_pct": 7,
                "electrical_space_ratio_pct": 4,
                "efficiency_factor": 0.96,
                "retention_strategy": "preserve_existing_bulk",
            }
        )
    elif scenario_key == "underused_asset":
        assumptions.update(
            {
                "wall_thickness_mm": 230,
                "core_ratio_pct": 17,
                "common_area_ratio_pct": 13,
                "floor_to_floor_m": 4.0,
                "clear_ceiling_m": 2.9,
                "hvac_space_ratio_pct": 7,
                "electrical_space_ratio_pct": 4,
                "efficiency_factor": 0.99,
                "retention_strategy": "selective_repositioning",
            }
        )
    elif scenario_key == "heritage_property":
        assumptions.update(
            {
                "wall_thickness_mm": 240,
                "core_ratio_pct": 14,
                "common_area_ratio_pct": 14,
                "floor_to_floor_m": 3.6,
                "clear_ceiling_m": 2.7,
                "hvac_space_ratio_pct": 9,
                "electrical_space_ratio_pct": 5,
                "efficiency_factor": 0.92,
                "retention_strategy": "conservation_retention",
            }
        )

    if conservation:
        assumptions["retention_strategy"] = "conservation_retention"
        assumptions["efficiency_factor"] = min(
            float(assumptions["efficiency_factor"]),
            0.93,
        )
        field_sources["retention_strategy"] = "property_specific"
        field_sources["efficiency_factor"] = "property_specific"
        adjustments.append("heritage_context")

    if isinstance(year_built, int) and year_built > 0 and year_built < 1990:
        assumptions["efficiency_factor"] = round(
            min(float(assumptions["efficiency_factor"]), 0.95), 2
        )
        assumptions["floor_to_floor_m"] = max(
            3.5,
            round(float(assumptions["floor_to_floor_m"]) - 0.1, 1),
        )
        field_sources["efficiency_factor"] = "property_specific"
        field_sources["floor_to_floor_m"] = "property_specific"
        adjustments.append("older_building_age")

    if isinstance(existing_floors, int) and existing_floors > 0:
        assumptions["existing_floor_count"] = existing_floors
        adjustments.append("existing_floor_count")

    primary_asset = _infer_primary_asset_type(existing_use)
    assumptions["primary_asset_bias"] = primary_asset
    assumptions["source"] = (
        "hybrid"
        if any(value == "property_specific" for value in field_sources.values())
        else "rules"
    )
    assumptions["provenance"] = {
        "summary": (
            "rules_with_property_adjustments"
            if assumptions["source"] == "hybrid"
            else "rules_only"
        ),
        "fields": field_sources,
        "adjustments": list(dict.fromkeys(adjustments)),
    }
    return assumptions


def _target_floor_height_for_asset(
    asset_type: str,
    *,
    default_floor_to_floor_m: float,
) -> float:
    asset_key = asset_type.lower()
    if asset_key == "retail":
        return max(default_floor_to_floor_m, 4.8)
    if asset_key == "hospitality":
        return max(default_floor_to_floor_m - 0.1, 3.5)
    if asset_key == "residential":
        return max(default_floor_to_floor_m - 0.6, 3.2)
    if asset_key == "amenities":
        return max(default_floor_to_floor_m - 0.2, 3.6)
    return default_floor_to_floor_m


def _target_clear_ceiling_for_asset(
    asset_type: str,
    *,
    default_floor_to_floor_m: float,
    default_clear_ceiling_m: float,
) -> float:
    service_gap = max(default_floor_to_floor_m - default_clear_ceiling_m, 0.6)
    floor_to_floor = _target_floor_height_for_asset(
        asset_type,
        default_floor_to_floor_m=default_floor_to_floor_m,
    )
    return round(max(floor_to_floor - service_gap, 2.7), 1)


def _build_preview_asset_profiles(
    optimizations: list[DeveloperAssetOptimization],
    *,
    engineering_assumptions: dict[str, Any],
) -> list[dict[str, Any]]:
    default_floor_to_floor = float(engineering_assumptions["floor_to_floor_m"])
    default_clear_ceiling = float(engineering_assumptions["clear_ceiling_m"])
    source = str(engineering_assumptions.get("source") or "rules")
    profiles: list[dict[str, Any]] = []

    for optimization in optimizations:
        profiles.append(
            {
                "asset_type": optimization.asset_type,
                "floor_to_floor_m": optimization.target_floor_height_m,
                "clear_ceiling_m": _target_clear_ceiling_for_asset(
                    optimization.asset_type,
                    default_floor_to_floor_m=default_floor_to_floor,
                    default_clear_ceiling_m=default_clear_ceiling,
                ),
                "nia_efficiency": optimization.nia_efficiency,
                "source": source,
            }
        )

    return profiles


def _apply_preview_engineering_defaults(
    optimizations: list[DeveloperAssetOptimization],
    *,
    engineering_assumptions: dict[str, Any],
    site_area_sqm: float | None,
) -> list[DeveloperAssetOptimization]:
    default_floor_to_floor = float(engineering_assumptions["floor_to_floor_m"])
    efficiency_factor = float(engineering_assumptions["efficiency_factor"])
    updated: list[DeveloperAssetOptimization] = []
    for optimization in optimizations:
        target_floor_height = _target_floor_height_for_asset(
            optimization.asset_type,
            default_floor_to_floor_m=default_floor_to_floor,
        )
        base_efficiency = optimization.nia_efficiency or 0.82
        adjusted_efficiency = max(
            0.65,
            min(round(base_efficiency * efficiency_factor, 3), 0.92),
        )
        allocated_gfa = optimization.allocated_gfa_sqm
        nia_sqm = (
            round(allocated_gfa * adjusted_efficiency, 2)
            if allocated_gfa is not None
            else None
        )
        estimated_height = None
        if site_area_sqm and site_area_sqm > 0 and allocated_gfa:
            estimated_height = round(
                (allocated_gfa / site_area_sqm) * target_floor_height, 1
            )

        note = (
            f"Preview defaults: {engineering_assumptions['retention_strategy'].replace('_', ' ')} "
            f"with floor-to-floor {target_floor_height:.1f} m and efficiency factor {adjusted_efficiency:.2f}."
        )
        notes = list(optimization.notes)
        if note not in notes:
            notes.append(note)

        updated.append(
            copy_model(
                optimization,
                update={
                    "target_floor_height_m": target_floor_height,
                    "nia_efficiency": adjusted_efficiency,
                    "nia_sqm": nia_sqm,
                    "estimated_height_m": estimated_height,
                    "notes": notes,
                },
            )
        )
    return updated


def _append_visualization_assumption_notes(
    visualization: DeveloperVisualizationSummary,
    engineering_assumptions: dict[str, Any],
) -> None:
    assumption_note = (
        "Engineering defaults: "
        f"floor-to-floor {engineering_assumptions['floor_to_floor_m']:.1f} m, "
        f"clear ceiling {engineering_assumptions['clear_ceiling_m']:.1f} m, "
        f"core {engineering_assumptions['core_ratio_pct']:.0f}%, "
        f"common area {engineering_assumptions['common_area_ratio_pct']:.0f}%."
    )
    if assumption_note not in visualization.notes:
        visualization.notes.append(assumption_note)


def _build_asset_optimizations(
    land_use: str,
    envelope: DeveloperBuildEnvelope,
    existing_use: str | None,
    property_info: dict[str, Any] | None,
    quick_analysis: dict[str, Any] | None,
    heritage_overlay: dict[str, Any] | None,
) -> tuple[list[DeveloperAssetOptimization], dict[str, Any], AssetOptimizationOutcome]:
    total_gfa = envelope.max_buildable_gfa_sqm or envelope.current_gfa_sqm
    if (
        total_gfa is None
        and envelope.current_gfa_sqm is not None
        and envelope.additional_potential_gfa_sqm is not None
    ):
        total_gfa = envelope.current_gfa_sqm + max(
            envelope.additional_potential_gfa_sqm, 0.0
        )
    total_gfa_value = float(total_gfa) if total_gfa is not None else None

    heritage_context = _extract_heritage_context(
        envelope, property_info, quick_analysis, heritage_overlay
    )
    heritage_flag = heritage_context["flag"]
    heritage_risk = heritage_context["risk"]
    quick_metrics = _collect_quick_metrics(quick_analysis)

    assumption_note = heritage_context.get("assumption")
    if assumption_note and assumption_note not in envelope.assumptions:
        envelope.assumptions.append(assumption_note)

    outcome = build_asset_mix(
        land_use,
        achievable_gfa_sqm=total_gfa_value,
        additional_gfa=envelope.additional_potential_gfa_sqm,
        heritage=heritage_flag,
        heritage_risk=heritage_risk,
        existing_use=existing_use,
        site_area_sqm=envelope.site_area_sqm,
        current_gfa_sqm=envelope.current_gfa_sqm,
        quick_metrics=quick_metrics,
    )
    plans = outcome.plans
    constraint_summary: str | None = None
    constraints = heritage_context.get("constraints") or []
    if constraints:
        if len(constraints) > 2:
            constraint_summary = (
                "; ".join(constraints[:2]) + " + additional constraints"
            )
        else:
            constraint_summary = "; ".join(constraints)
    if constraint_summary:
        for plan in plans:
            if constraint_summary not in plan.notes:
                plan.notes.append(constraint_summary)

    optimizations = [
        DeveloperAssetOptimization(
            asset_type=plan.asset_type,
            allocation_pct=plan.allocation_pct,
            nia_efficiency=plan.nia_efficiency,
            allocated_gfa_sqm=plan.allocated_gfa_sqm,
            target_floor_height_m=plan.target_floor_height_m,
            parking_ratio_per_1000sqm=plan.parking_ratio_per_1000sqm,
            rent_psm_month=plan.rent_psm_month,
            stabilised_vacancy_pct=plan.stabilised_vacancy_pct,
            opex_pct_of_rent=plan.opex_pct_of_rent,
            estimated_revenue_sgd=plan.estimated_revenue_sgd,
            estimated_capex_sgd=plan.estimated_capex_sgd,
            fitout_cost_psm=plan.fitout_cost_psm,
            absorption_months=plan.absorption_months,
            risk_level=plan.risk_level,
            heritage_premium_pct=plan.heritage_premium_pct,
            notes=list(plan.notes),
            nia_sqm=plan.nia_sqm,
            estimated_height_m=plan.estimated_height_m,
            total_parking_bays_required=plan.total_parking_bays_required,
            revenue_basis=plan.revenue_basis,
            constraint_violations=[
                DeveloperConstraintViolation(
                    constraint_type=violation.constraint_type,
                    severity=violation.severity,
                    message=violation.message,
                    asset_type=violation.asset_type,
                )
                for violation in plan.constraint_violations
            ],
            confidence_score=plan.confidence_score,
            alternative_scenarios=list(plan.alternative_scenarios),
        )
        for plan in plans
    ]
    heritage_context["optimizer_confidence"] = outcome.confidence
    if outcome.constraint_log:
        heritage_context.setdefault("constraints", [])
        for violation in outcome.constraint_log:
            message = f"{violation.constraint_type}: {violation.message}"
            if message not in heritage_context["constraints"]:
                heritage_context["constraints"].append(message)
    return optimizations, heritage_context, outcome


# =============================================================================
# Finance Helpers
# =============================================================================


PHASE2B_FINANCE_BLUEPRINT = DeveloperFinanceBlueprint(
    capital_structure=[
        DeveloperCapitalStructureScenario(
            scenario="Base Case",
            equity_pct=35.0,
            debt_pct=60.0,
            preferred_equity_pct=5.0,
            target_ltv=60.0,
            target_ltc=65.0,
            target_dscr=1.35,
            comments=(
                "Core Singapore development structure assuming SORA + 250 bps blended cost of debt."
            ),
        ),
        DeveloperCapitalStructureScenario(
            scenario="Upside",
            equity_pct=30.0,
            debt_pct=65.0,
            preferred_equity_pct=5.0,
            target_ltv=58.0,
            target_ltc=63.0,
            target_dscr=1.40,
            comments="Higher pre-leasing allows additional leverage with tighter DSCR covenants.",
        ),
        DeveloperCapitalStructureScenario(
            scenario="Downside",
            equity_pct=45.0,
            debt_pct=50.0,
            preferred_equity_pct=5.0,
            target_ltv=55.0,
            target_ltc=60.0,
            target_dscr=1.25,
            comments="De-risked case with additional sponsor equity and conservative leverage headroom.",
        ),
    ],
    debt_facilities=[
        DeveloperDebtFacility(
            facility_type="Construction Loan",
            amount_expression="0.60 x total_dev_cost",
            interest_rate="4.8% (SORA 3M + 240 bps)",
            tenor_years=4.0,
            amortisation="Interest-only during build; convert to 20-yr schedule at PC",
            drawdown_schedule_notes="15%/30%/30%/25% drawn by construction quarter.",
            covenants_triggers="DSCR >= 1.20 post-income; quarterly cost-to-complete tests.",
        ),
        DeveloperDebtFacility(
            facility_type="Bridge / Mezzanine",
            amount_expression="0.10 x total_dev_cost",
            interest_rate="8.5% fixed",
            tenor_years=2.0,
            amortisation="Bullet",
            drawdown_schedule_notes="Tranche alongside equity for land completion and top-up costs.",
            covenants_triggers="LTV hard cap 72%; cash sweep if DSCR falls below 1.15.",
        ),
        DeveloperDebtFacility(
            facility_type="Permanent Debt",
            amount_expression="0.55 x stabilised_value",
            interest_rate="4.2% (SORA 3M + 180 bps)",
            tenor_years=7.0,
            amortisation="20-year amortisation with 30% balloon",
            drawdown_schedule_notes="Funds post-PC once 70% stabilised occupancy achieved.",
            covenants_triggers="DSCR >= 1.35; maintain LTV <= 60%; cash sweep above 1.45 DSCR.",
        ),
    ],
    equity_waterfall=DeveloperEquityWaterfall(
        tiers=[
            DeveloperEquityWaterfallTier(hurdle_irr_pct=12.0, promote_pct=10.0),
            DeveloperEquityWaterfallTier(hurdle_irr_pct=18.0, promote_pct=20.0),
        ],
        preferred_return_pct=9.0,
        catch_up_notes=(
            "50/50 catch-up after preferred return; clawback if project IRR falls below 12% on exit."
        ),
    ),
    cash_flow_timeline=[
        DeveloperCashFlowMilestone(
            item="Land Acquisition",
            start_month=0,
            duration_months=3,
            notes="Due diligence, option exercise, completion, and stamping.",
        ),
        DeveloperCashFlowMilestone(
            item="Construction",
            start_month=3,
            duration_months=30,
            notes="Includes enabling works plus six-month interior fit-out buffer.",
        ),
        DeveloperCashFlowMilestone(
            item="Leasing / Sales",
            start_month=24,
            duration_months=18,
            notes="Marketing and pre-commitments begin during final construction year.",
        ),
        DeveloperCashFlowMilestone(
            item="Stabilisation",
            start_month=42,
            duration_months=12,
            notes="Target >=90% leased with NOI run-rate established.",
        ),
        DeveloperCashFlowMilestone(
            item="Exit / Refinance",
            start_month=48,
            duration_months=3,
            notes="Refinance or partial asset sale once DSCR covenant achieved.",
        ),
    ],
    exit_assumptions=DeveloperExitAssumptions(
        exit_cap_rates={"base": 4.0, "upside": 3.6, "downside": 4.5},
        sale_costs_pct=2.25,
        sale_costs_breakdown="1.75% broker + 0.25% legal + 0.25% stamp/fees.",
        refinance_terms="65% LTV senior loan at SORA + 170 bps, 5-year tenor, 25-year amortisation.",
    ),
    sensitivity_bands=[
        DeveloperSensitivityBand(
            parameter="Rent",
            low=-8.0,
            base=0.0,
            high=6.0,
            comments="URA quarterly ranges for CBD office and prime retail benchmarks.",
        ),
        DeveloperSensitivityBand(
            parameter="Exit Cap Rate (delta bps)",
            low=0.40,
            base=0.0,
            high=-0.30,
            comments="Stress ± basis points around 4.0% base exit yield.",
        ),
        DeveloperSensitivityBand(
            parameter="Construction Cost",
            low=10.0,
            base=0.0,
            high=-5.0,
            comments="2024 BCA tender price index volatility band.",
        ),
        DeveloperSensitivityBand(
            parameter="Interest Rate (delta %)",
            low=1.50,
            base=0.0,
            high=-0.75,
            comments="SORA tightening/easing swing assumptions.",
        ),
    ],
)


def _phase2b_finance_blueprint() -> DeveloperFinanceBlueprint:
    """Return a defensive copy of the Phase 2B finance blueprint."""
    return copy_model(PHASE2B_FINANCE_BLUEPRINT, deep=True)


def _build_finance_asset_mix_inputs(
    optimizations: Sequence[DeveloperAssetOptimization],
    *,
    jurisdiction_code: str,
) -> list[dict[str, Any]]:
    jurisdiction = get_jurisdiction_config(jurisdiction_code)
    finance_inputs: list[dict[str, Any]] = []
    for opt in optimizations:
        nia = _convert_area_to_sqm(
            _decimal_or_none(opt.nia_sqm), from_units=jurisdiction.area_units
        )
        rent_psm = _convert_rent_to_psm(
            _decimal_or_none(opt.rent_psm_month), rent_metric=jurisdiction.rent_metric
        )
        finance_input = FinanceAssetMixInput(
            asset_type=opt.asset_type,
            allocation_pct=_decimal_or_none(opt.allocation_pct),
            nia_sqm=nia,
            rent_psm_month=rent_psm,
            stabilised_vacancy_pct=_decimal_or_none(opt.stabilised_vacancy_pct),
            opex_pct_of_rent=_decimal_or_none(opt.opex_pct_of_rent),
            estimated_revenue_sgd=_decimal_or_none(opt.estimated_revenue_sgd),
            estimated_capex_sgd=_decimal_or_none(opt.estimated_capex_sgd),
            absorption_months=_decimal_or_none(opt.absorption_months),
            risk_level=opt.risk_level,
            heritage_premium_pct=_decimal_or_none(opt.heritage_premium_pct),
            notes=list(opt.notes),
        )
        finance_inputs.append(finance_input.model_dump(mode="json"))
    return finance_inputs


def _summarise_financials(
    optimizations: list[DeveloperAssetOptimization],
    *,
    constraint_log: Sequence[DeveloperConstraintViolation] | None = None,
    optimizer_confidence: float | None = None,
    jurisdiction_code: str = "SG",
) -> DeveloperFinancialSummary:
    total_revenue = sum(
        (opt.estimated_revenue_sgd or 0.0)
        for opt in optimizations
        if opt.estimated_revenue_sgd
    )
    total_capex = sum(
        (opt.estimated_capex_sgd or 0.0)
        for opt in optimizations
        if opt.estimated_capex_sgd
    )
    risk_order = {"low": 1, "balanced": 2, "moderate": 3, "elevated": 4}
    dominant = None
    for opt in optimizations:
        level = opt.risk_level
        if level is None:
            continue
        if dominant is None or risk_order.get(level, 0) > risk_order.get(dominant, 0):
            dominant = level

    notes: list[str] = []
    if dominant:
        notes.append(f"Dominant risk profile driven by {dominant} allocations.")
    if total_revenue:
        notes.append(
            "Total estimated revenue assumes NIA efficiency-weighted rent across the suggested mix."
        )
    if total_capex:
        notes.append(
            "Capex estimate aggregates fit-out assumptions for each programmed use."
        )

    finance_blueprint = _phase2b_finance_blueprint()
    notes.append(
        "Phase 2B finance blueprint attached with capital stack, debt facility, and sensitivity defaults."
    )

    jurisdiction = get_jurisdiction_config(jurisdiction_code)
    summary = DeveloperFinancialSummary(
        total_estimated_revenue_sgd=total_revenue or None,
        total_estimated_capex_sgd=total_capex or None,
        dominant_risk_profile=dominant,
        notes=notes,
        finance_blueprint=finance_blueprint,
        currency_code=jurisdiction.currency_code,
        currency_symbol=jurisdiction.currency_symbol,
    )
    summary.asset_mix_finance_inputs = _build_finance_asset_mix_inputs(
        optimizations, jurisdiction_code=jurisdiction.code
    )
    if constraint_log:
        summary.constraint_log = list(constraint_log)
    if optimizer_confidence is not None:
        summary.optimizer_confidence = optimizer_confidence
        summary.notes.append(
            f"Optimiser confidence score: {optimizer_confidence:.2f} (1.0 = high certainty)."
        )
    return summary


# =============================================================================
# Request/Response Models
# =============================================================================


class DeveloperGPSLogRequest(BaseModel):
    """GPS capture request tailored for developers."""

    model_config = {"populate_by_name": True}

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    development_scenarios: list[CaptureScenario] | None = Field(
        None,
        description=(
            "Optional set of development scenarios to evaluate during capture. "
            "Defaults to the core commercial scenarios if omitted."
        ),
    )
    preview_geometry_detail_level: str | None = Field(
        default=None,
        description="Optional geometry detail override for the generated preview job.",
    )
    jurisdiction_code: str | None = Field(
        default="SG",
        alias="jurisdictionCode",
        description="Jurisdiction code for the captured property (e.g. 'SG', 'HK').",
    )

    @field_validator("preview_geometry_detail_level")
    @classmethod
    def _validate_preview_detail_level(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalised = value.strip().lower()
        if normalised not in preview_generator.SUPPORTED_GEOMETRY_DETAIL_LEVELS:
            valid = ", ".join(
                sorted(preview_generator.SUPPORTED_GEOMETRY_DETAIL_LEVELS)
            )
            raise ValueError(f"preview_geometry_detail_level must be one of: {valid}")
        return normalised

    @field_validator("jurisdiction_code")
    @classmethod
    def _normalise_jurisdiction(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip().upper()
        return trimmed or "SG"


class PreviewJobRefreshRequest(BaseModel):
    """Request body for preview job refresh operations."""

    geometry_detail_level: str | None = Field(
        default=None, description="Optional geometry detail level override"
    )
    color_legend: list[DeveloperColorLegendEntry] | None = Field(
        default=None,
        description="Optional colour legend overrides to persist on the preview job",
    )

    @field_validator("geometry_detail_level")
    @classmethod
    def _validate_detail_level(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalised = value.strip().lower()
        if normalised not in preview_generator.SUPPORTED_GEOMETRY_DETAIL_LEVELS:
            valid = ", ".join(
                sorted(preview_generator.SUPPORTED_GEOMETRY_DETAIL_LEVELS)
            )
            raise ValueError(f"geometry_detail_level must be one of: {valid}")
        return normalised


class PreviewJobCreateRequest(BaseModel):
    """Request body for scenario-specific starter model generation."""

    model_config = {"populate_by_name": True}

    scenario: CaptureScenario = Field(
        ...,
        description="Development scenario that the starter model should represent.",
    )
    geometry_detail_level: str | None = Field(
        default=None,
        description="Optional geometry detail level override",
    )
    color_legend: list[DeveloperColorLegendEntry] | None = Field(
        default=None,
        description="Optional colour legend overrides to persist on the preview job",
    )

    @field_validator("geometry_detail_level")
    @classmethod
    def _validate_detail_level(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalised = value.strip().lower()
        if normalised not in preview_generator.SUPPORTED_GEOMETRY_DETAIL_LEVELS:
            valid = ", ".join(
                sorted(preview_generator.SUPPORTED_GEOMETRY_DETAIL_LEVELS)
            )
            raise ValueError(f"geometry_detail_level must be one of: {valid}")
        return normalised


class DeveloperGPSLogResponse(BaseModel):
    """Response envelope for developer GPS capture."""

    property_id: UUID
    address: Address
    coordinates: CoordinatePair
    geocoding_source: ExternalSourceMetadata | None = None
    amenities_source: ExternalSourceMetadata | None = None
    ura_source: ExternalSourceMetadata | None = None
    jurisdiction_code: str
    ura_zoning: Dict[str, Any]
    existing_use: str
    property_info: Optional[Dict[str, Any]]
    nearby_amenities: Optional[Dict[str, Any]]
    quick_analysis: QuickAnalysisEnvelope
    build_envelope: DeveloperBuildEnvelope
    visualization: DeveloperVisualizationSummary
    optimizations: list[DeveloperAssetOptimization]
    financial_summary: DeveloperFinancialSummary
    heritage_context: dict[str, Any] | None = None
    preview_jobs: list[PreviewJobSchema] = Field(default_factory=list)
    timestamp: datetime


DeveloperGPSLogResponse.model_rebuild()


class FinanceProjectCreateRequest(BaseModel):
    """Request body for creating a finance project/scenario from a GPS capture."""

    model_config = {"populate_by_name": True}

    project_name: str | None = Field(default=None, alias="projectName")
    scenario_name: str | None = Field(default=None, alias="scenarioName")
    total_estimated_capex_sgd: float | None = Field(
        default=None,
        alias="totalEstimatedCapexSgd",
    )
    total_estimated_revenue_sgd: float | None = Field(
        default=None,
        alias="totalEstimatedRevenueSgd",
    )

    @model_validator(mode="before")
    @classmethod
    def _normalise_legacy_keys(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        if (
            "total_estimated_capex_sgd" not in payload
            and "totalEstimatedCapexSgd" not in payload
        ):
            for legacy_key in ("total_estimated_capex", "totalEstimatedCapex"):
                if legacy_key in payload:
                    payload["total_estimated_capex_sgd"] = payload[legacy_key]
                    break
        if (
            "total_estimated_revenue_sgd" not in payload
            and "totalEstimatedRevenueSgd" not in payload
        ):
            for legacy_key in ("total_estimated_revenue", "totalEstimatedRevenue"):
                if legacy_key in payload:
                    payload["total_estimated_revenue_sgd"] = payload[legacy_key]
                    break
        return payload


class FinanceProjectCreateResponse(BaseModel):
    """Response envelope for finance project creation."""

    project_id: UUID
    fin_project_id: int
    scenario_id: int
    project_name: str


class CaptureProjectCreateRequest(BaseModel):
    """Request body for saving a capture as a project."""

    model_config = {"populate_by_name": True}

    project_name: str | None = Field(default=None, alias="projectName")
    include_checklist: bool = Field(
        default=False,
        alias="includeChecklist",
    )
    development_scenarios: list[CaptureScenario] | None = Field(
        default=None,
        alias="developmentScenarios",
    )


class CaptureProjectLinkRequest(BaseModel):
    """Request body for linking a capture to an existing project."""

    model_config = {"populate_by_name": True}

    project_id: UUID = Field(..., alias="projectId")
    include_checklist: bool = Field(
        default=False,
        alias="includeChecklist",
    )
    development_scenarios: list[CaptureScenario] | None = Field(
        default=None,
        alias="developmentScenarios",
    )


class CaptureProjectLinkResponse(BaseModel):
    """Response envelope for capture/project linkage."""

    project_id: UUID
    project_name: str
    property_id: UUID


# =============================================================================
# Route Handlers
# =============================================================================


@router.post(
    "/properties/log-gps",
    response_model=DeveloperGPSLogResponse,
)
async def developer_log_property_by_gps(
    request: DeveloperGPSLogRequest,
    session: AsyncSession = Depends(get_session),
    token: TokenData | None = Depends(get_optional_user),
) -> DeveloperGPSLogResponse:
    """Log a property for developer workflows using GPS coordinates."""

    user_uuid: Optional[UUID] = None
    if token and token.user_id:
        try:
            user_uuid = UUID(token.user_id)
        except ValueError:
            logger.warning(
                "developer_gps_invalid_user_id",
                supplied_user_id=token.user_id,
            )

    try:
        result = await developer_gps_logger.log_property_from_gps(
            latitude=request.latitude,
            longitude=request.longitude,
            session=session,
            user_id=user_uuid,
            scenarios=request.development_scenarios,
            jurisdiction_code=request.jurisdiction_code,
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail="GPS capture unavailable: geocoding failed",
        ) from exc

    quick_analysis_payload = result.quick_analysis or {
        "generated_at": utcnow().isoformat(),
        "scenarios": [],
    }
    quick_analysis = QuickAnalysisEnvelope.model_validate(quick_analysis_payload)

    property_metadata = await session.get(Property, result.property_id)
    property_jurisdiction = (
        property_metadata.jurisdiction_code if property_metadata else "SG"
    )
    property_info_payload = _to_mapping(result.property_info)
    property_info_dict: dict[str, Any] = (
        dict(property_info_payload) if property_info_payload else {}
    )
    property_info_dict.setdefault("jurisdiction_code", property_jurisdiction)
    if property_metadata is not None:
        if property_metadata.is_conservation is not None:
            property_info_dict.setdefault(
                "is_conservation", property_metadata.is_conservation
            )
        if property_metadata.conservation_status:
            property_info_dict.setdefault(
                "conservation_status", property_metadata.conservation_status
            )
            property_info_dict.setdefault(
                "heritage_status", property_metadata.conservation_status
            )
        if property_metadata.heritage_constraints:
            property_info_dict.setdefault(
                "heritage_constraints", property_metadata.heritage_constraints
            )

    property_info_for_mix: dict[str, Any] | None = (
        property_info_dict if property_info_dict else None
    )
    quick_analysis_dict = quick_analysis.model_dump()
    heritage_overlay = getattr(result, "heritage_overlay", None)

    build_envelope = await _derive_build_envelope(
        result, session, property_jurisdiction
    )
    optimizations, heritage_context, optimization_outcome = _build_asset_optimizations(
        result.existing_use,
        build_envelope,
        result.existing_use,
        property_info_for_mix,
        quick_analysis_dict,
        heritage_overlay,
    )
    visualization = _build_visualization_summary(
        quick_analysis_dict,
        result.property_id,
        optimizations,
        build_envelope,
    )
    preview_service = PreviewJobService(session)
    massing_payload = [
        layer.model_dump() if hasattr(layer, "model_dump") else layer.__dict__
        for layer in visualization.massing_layers
    ]
    legend_payload = [
        entry.model_dump() if hasattr(entry, "model_dump") else entry.__dict__
        for entry in visualization.color_legend
    ]
    preview_job = await preview_service.queue_preview(
        property_id=result.property_id,
        scenario="base",
        massing_layers=massing_payload,
        camera_orbit=visualization.camera_orbit_hint or {},
        geometry_detail_level=request.preview_geometry_detail_level,
        color_legend=legend_payload,
    )
    preview_status = (
        preview_job.status.value
        if isinstance(preview_job.status, PreviewJobStatus)
        else str(preview_job.status)
    )
    preview_available = preview_status == PreviewJobStatus.READY.value
    concept_mesh_url = preview_job.preview_url if preview_available else None
    preview_metadata_url = preview_job.metadata_url if preview_available else None
    thumbnail_url = preview_job.thumbnail_url if preview_available else None
    status_for_response = preview_status
    visualization = copy_model(
        visualization,
        update={
            "status": status_for_response,
            "preview_available": preview_available,
            "concept_mesh_url": concept_mesh_url,
            "preview_metadata_url": preview_metadata_url,
            "thumbnail_url": thumbnail_url,
            "preview_job_id": preview_job.id,
        },
    )
    preview_jobs_payload = [_serialise_preview_job(preview_job)]
    constraint_log = [
        DeveloperConstraintViolation(
            constraint_type=violation.constraint_type,
            severity=violation.severity,
            message=violation.message,
            asset_type=violation.asset_type,
        )
        for violation in optimization_outcome.constraint_log
    ]
    financial_summary = _summarise_financials(
        optimizations,
        constraint_log=constraint_log,
        optimizer_confidence=optimization_outcome.confidence,
        jurisdiction_code=property_jurisdiction,
    )

    heritage_constraints = heritage_context.get("constraints") or []
    if heritage_constraints:
        constraint_text = heritage_constraints[0]
        if constraint_text not in financial_summary.notes:
            financial_summary.notes.insert(0, constraint_text)
    heritage_risk = heritage_context.get("risk")
    if heritage_risk == "high":
        financial_summary.dominant_risk_profile = "elevated"
    elif heritage_risk == "medium" and not financial_summary.dominant_risk_profile:
        financial_summary.dominant_risk_profile = "balanced"

    await session.commit()

    return DeveloperGPSLogResponse(
        property_id=result.property_id,
        address=result.address,
        coordinates=CoordinatePair(
            latitude=result.coordinates[0],
            longitude=result.coordinates[1],
        ),
        geocoding_source=result.geocoding_source,
        amenities_source=result.amenities_source,
        ura_source=result.ura_source,
        jurisdiction_code=property_jurisdiction,
        ura_zoning=result.ura_zoning,
        existing_use=result.existing_use,
        nearby_amenities=result.nearby_amenities,
        quick_analysis=quick_analysis,
        build_envelope=build_envelope,
        visualization=visualization,
        optimizations=optimizations,
        financial_summary=financial_summary,
        heritage_context=heritage_context,
        preview_jobs=preview_jobs_payload,
        property_info=property_info_dict or None,
        timestamp=result.timestamp,
    )


@router.post(
    "/properties/{property_id}/create-project",
    response_model=FinanceProjectCreateResponse,
)
async def create_finance_project_for_capture(
    property_id: UUID,
    payload: FinanceProjectCreateRequest | None = None,
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_reviewer),
) -> FinanceProjectCreateResponse:
    """Create a finance project/scenario seeded from the GPS capture."""

    request_payload = payload or FinanceProjectCreateRequest()
    try:
        result = await create_finance_project_from_capture(
            session=session,
            identity=identity,
            property_id=property_id,
            project_name=request_payload.project_name,
            scenario_name=request_payload.scenario_name,
            total_estimated_capex_sgd=request_payload.total_estimated_capex_sgd,
            total_estimated_revenue_sgd=request_payload.total_estimated_revenue_sgd,
        )
    except ValueError as exc:
        if str(exc) == "identity_required":
            raise HTTPException(
                status_code=403,
                detail=(
                    "Finance project creation requires identity headers "
                    "(X-User-Email or X-User-Id)."
                ),
            ) from exc
        if str(exc) == "property_not_found":
            raise HTTPException(status_code=404, detail="Property not found") from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return FinanceProjectCreateResponse(
        project_id=result.project_id,
        fin_project_id=result.fin_project_id,
        scenario_id=result.scenario_id,
        project_name=result.project_name,
    )


@router.post(
    "/properties/{property_id}/save-project",
    response_model=CaptureProjectLinkResponse,
)
async def save_project_from_capture(
    property_id: UUID,
    payload: CaptureProjectCreateRequest | None = None,
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_reviewer),
) -> CaptureProjectLinkResponse:
    """Create a project from a capture and link the property."""

    property_record = await session.get(Property, property_id)
    if property_record is None:
        raise HTTPException(status_code=404, detail="Property not found")

    if property_record.project_id:
        project = await session.get(Project, property_record.project_id)
        if project is not None:
            return CaptureProjectLinkResponse(
                project_id=project.id,
                project_name=project.project_name,
                property_id=property_id,
            )

    request_payload = payload or CaptureProjectCreateRequest()
    cleaned_project_name = (
        request_payload.project_name or property_record.name or "Capture Project"
    ).strip()
    if not cleaned_project_name:
        cleaned_project_name = "Capture Project"

    project_code = f"gps_{property_id.hex}"
    existing = await session.execute(
        select(Project).where(Project.project_code == project_code)
    )
    if existing.scalar_one_or_none():
        project_code = f"{project_code}_{uuid4().hex[:6]}"

    owner_email = (identity.email or "").strip() or None
    owner_id: UUID | None = None
    if identity.user_id:
        try:
            owner_id = UUID(identity.user_id)
        except ValueError:
            owner_id = None

    project = Project(
        project_name=cleaned_project_name,
        project_code=project_code,
        project_type=ProjectType.NEW_DEVELOPMENT,
        current_phase=ProjectPhase.CONCEPT,
        owner_id=owner_id,
        owner_email=owner_email,
    )
    session.add(project)
    await session.flush()

    property_record.project_id = project.id
    if owner_email and not property_record.owner_email:
        property_record.owner_email = owner_email

    if request_payload.include_checklist:
        checklist_scenarios = [
            (scenario.value if isinstance(scenario, CaptureScenario) else str(scenario))
            for scenario in (request_payload.development_scenarios or [])
        ]
        checklist_scenarios = [
            scenario.strip() for scenario in checklist_scenarios if scenario.strip()
        ]
        if not checklist_scenarios:
            raise HTTPException(
                status_code=400,
                detail="development_scenarios is required when include_checklist is true",
            )
        await DeveloperChecklistService.ensure_templates_seeded(session)
        await DeveloperChecklistService.auto_populate_checklist(
            session=session,
            property_id=property_id,
            development_scenarios=checklist_scenarios,
        )

    await session.commit()

    return CaptureProjectLinkResponse(
        project_id=project.id,
        project_name=project.project_name,
        property_id=property_id,
    )


@router.post(
    "/properties/{property_id}/link-project",
    response_model=CaptureProjectLinkResponse,
)
async def link_capture_to_project(
    property_id: UUID,
    payload: CaptureProjectLinkRequest,
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_reviewer),
) -> CaptureProjectLinkResponse:
    """Link a capture to an existing project."""

    property_record = await session.get(Property, property_id)
    if property_record is None:
        raise HTTPException(status_code=404, detail="Property not found")

    project = await session.get(Project, payload.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    property_record.project_id = project.id
    if identity.email and not property_record.owner_email:
        property_record.owner_email = identity.email

    if payload.include_checklist:
        checklist_scenarios = [
            (scenario.value if isinstance(scenario, CaptureScenario) else str(scenario))
            for scenario in (payload.development_scenarios or [])
        ]
        checklist_scenarios = [
            scenario.strip() for scenario in checklist_scenarios if scenario.strip()
        ]
        if not checklist_scenarios:
            raise HTTPException(
                status_code=400,
                detail="development_scenarios is required when include_checklist is true",
            )
        await DeveloperChecklistService.ensure_templates_seeded(session)
        await DeveloperChecklistService.auto_populate_checklist(
            session=session,
            property_id=property_id,
            development_scenarios=checklist_scenarios,
        )

    await session.commit()

    return CaptureProjectLinkResponse(
        project_id=project.id,
        project_name=project.project_name,
        property_id=property_id,
    )


@router.get(
    "/properties/{property_id}/preview-jobs",
    response_model=list[PreviewJobSchema],
)
async def list_preview_jobs(
    property_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> list[PreviewJobSchema]:
    """Return preview jobs associated with the property."""

    service = PreviewJobService(session)
    jobs = await service.list_jobs(property_id)
    return [_serialise_preview_job(job) for job in jobs]


@router.post(
    "/properties/{property_id}/preview-jobs",
    response_model=PreviewJobSchema,
)
async def create_preview_job(
    property_id: UUID,
    payload: PreviewJobCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> PreviewJobSchema:
    """Queue a starter-model preview job for the requested scenario."""

    property_record = await session.get(Property, property_id)
    if property_record is None:
        raise HTTPException(status_code=404, detail="Property not found")

    _, visualization, massing_payload, legend_payload, engineering_assumptions = (
        await _build_property_preview_inputs(
            property_record,
            session,
            (
                payload.scenario.value
                if isinstance(payload.scenario, CaptureScenario)
                else str(payload.scenario)
            ),
        )
    )
    service = PreviewJobService(session)
    preview_job = await service.queue_preview(
        property_id=property_id,
        scenario=(
            payload.scenario.value
            if isinstance(payload.scenario, CaptureScenario)
            else str(payload.scenario)
        ),
        massing_layers=massing_payload,
        camera_orbit=visualization.camera_orbit_hint or {},
        geometry_detail_level=payload.geometry_detail_level,
        color_legend=(
            [
                entry.model_dump() if hasattr(entry, "model_dump") else entry.__dict__
                for entry in payload.color_legend
            ]
            if payload.color_legend
            else legend_payload
        ),
        metadata_extras={
            "starter_model_assumptions": engineering_assumptions,
            "visualization_notes": list(visualization.notes),
        },
    )
    await session.commit()
    await session.refresh(preview_job)
    return _serialise_preview_job(preview_job)


@router.get(
    "/preview-jobs/{job_id}",
    response_model=PreviewJobSchema,
)
async def get_preview_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> PreviewJobSchema:
    """Fetch a preview job by id."""

    service = PreviewJobService(session)
    job = await service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Preview job not found")
    return _serialise_preview_job(job)


@router.post(
    "/preview-jobs/{job_id}/refresh",
    response_model=PreviewJobSchema,
)
async def refresh_preview_job(
    job_id: UUID,
    refresh_request: PreviewJobRefreshRequest | None = None,
    session: AsyncSession = Depends(get_session),
) -> PreviewJobSchema:
    """Re-render a preview job using stored metadata."""

    service = PreviewJobService(session)
    job = await service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Preview job not found")
    try:
        await service.refresh_job(
            job,
            geometry_detail_level=(
                refresh_request.geometry_detail_level if refresh_request else None
            ),
            color_legend=(refresh_request.color_legend if refresh_request else None),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await session.commit()
    await session.refresh(job)
    return _serialise_preview_job(job)
