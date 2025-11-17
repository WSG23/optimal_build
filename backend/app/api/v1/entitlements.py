"""Entitlements API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse

from app.api.deps import require_reviewer, require_viewer
from app.core.database import get_session
from app.core.export.entitlements import (
    EntitlementsExportFormat,
    generate_entitlements_export,
)
from app.schemas.entitlements import (
    EntEngagementCollection,
    EntEngagementCreate,
    EntEngagementSchema,
    EntEngagementUpdate,
    EntLegalInstrumentCollection,
    EntLegalInstrumentCreate,
    EntLegalInstrumentSchema,
    EntLegalInstrumentUpdate,
    EntRoadmapCollection,
    EntRoadmapItemCreate,
    EntRoadmapItemSchema,
    EntRoadmapItemUpdate,
    EntStudyCollection,
    EntStudyCreate,
    EntStudySchema,
    EntStudyUpdate,
)
from app.services.entitlements import EntitlementsService
from app.utils import metrics
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/entitlements", tags=["entitlements"])


def _normalise_pagination(limit: int, offset: int) -> tuple[int, int]:
    limit_value = max(1, min(limit, 200))
    offset_value = max(0, offset)
    return limit_value, offset_value


def _model_list(schema: Any, records: Any) -> list[Any]:
    return [schema.model_validate(record, from_attributes=True) for record in records]


@router.api_route(
    "",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
async def entitlements_root_placeholder() -> None:
    """Provide a clearer error when project-specific path parameters are missing."""

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            "Specify a project-scoped endpoint, e.g.\n"
            "POST /api/v1/entitlements/{project_id}/roadmap"
        ),
    )


@router.get(
    "/{project_id}/roadmap",
    response_model=EntRoadmapCollection,
    summary="List entitlement roadmap items",
)
async def list_roadmap_items(
    project_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> EntRoadmapCollection:
    """Return paginated roadmap items for the supplied project."""

    metrics.REQUEST_COUNTER.labels(endpoint="entitlements_roadmap_list").inc()
    metrics.ENTITLEMENTS_ROADMAP_COUNTER.labels(operation="list").inc()
    limit_value, offset_value = _normalise_pagination(limit, offset)
    service = EntitlementsService(session)
    page = await service.list_roadmap_items(
        project_id=project_id, limit=limit_value, offset=offset_value
    )
    return EntRoadmapCollection(
        items=_model_list(EntRoadmapItemSchema, page.items),
        total=page.total,
        limit=limit_value,
        offset=offset_value,
    )


@router.post(
    "/{project_id}/roadmap",
    response_model=EntRoadmapItemSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a roadmap item",
)
async def create_roadmap_item(
    project_id: int,
    payload: EntRoadmapItemCreate,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_reviewer),
) -> EntRoadmapItemSchema:
    """Insert a new roadmap item for the project."""

    if payload.project_id != project_id:
        raise HTTPException(status_code=400, detail="Project ID mismatch")

    service = EntitlementsService(session)
    item = await service.create_roadmap_item(
        project_id=project_id,
        approval_type_id=payload.approval_type_id,
        sequence_order=payload.sequence_order,
        status=payload.status,
        status_changed_at=payload.status_changed_at,
        target_submission_date=payload.target_submission_date,
        target_decision_date=payload.target_decision_date,
        actual_submission_date=payload.actual_submission_date,
        actual_decision_date=payload.actual_decision_date,
        notes=payload.notes,
        metadata=payload.metadata,
    )
    await session.commit()
    await session.refresh(item)

    metrics.REQUEST_COUNTER.labels(endpoint="entitlements_roadmap_create").inc()
    metrics.ENTITLEMENTS_ROADMAP_COUNTER.labels(operation="create").inc()
    return EntRoadmapItemSchema.model_validate(item, from_attributes=True)


@router.put(
    "/{project_id}/roadmap/{item_id}",
    response_model=EntRoadmapItemSchema,
    summary="Update a roadmap item",
)
async def update_roadmap_item(
    project_id: int,
    item_id: int,
    payload: EntRoadmapItemUpdate,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_reviewer),
) -> EntRoadmapItemSchema:
    """Update an existing roadmap item."""

    service = EntitlementsService(session)
    data = payload.model_dump(exclude_unset=True)
    item = await service.update_roadmap_item(
        item_id=item_id,
        project_id=project_id,
        **data,
    )
    await session.commit()
    await session.refresh(item)

    metrics.REQUEST_COUNTER.labels(endpoint="entitlements_roadmap_update").inc()
    metrics.ENTITLEMENTS_ROADMAP_COUNTER.labels(operation="update").inc()
    return EntRoadmapItemSchema.model_validate(item, from_attributes=True)


@router.delete(
    "/{project_id}/roadmap/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a roadmap item",
)
async def delete_roadmap_item(
    project_id: int,
    item_id: int,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_reviewer),
) -> Response:
    """Remove the specified roadmap entry."""

    service = EntitlementsService(session)
    await service.delete_roadmap_item(item_id=item_id, project_id=project_id)
    await session.commit()
    metrics.REQUEST_COUNTER.labels(endpoint="entitlements_roadmap_delete").inc()
    metrics.ENTITLEMENTS_ROADMAP_COUNTER.labels(operation="delete").inc()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{project_id}/studies",
    response_model=EntStudyCollection,
    summary="List entitlement studies",
)
async def list_studies(
    project_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> EntStudyCollection:
    """Return paginated entitlement studies."""

    metrics.REQUEST_COUNTER.labels(endpoint="entitlements_study_list").inc()
    metrics.ENTITLEMENTS_STUDY_COUNTER.labels(operation="list").inc()
    limit_value, offset_value = _normalise_pagination(limit, offset)
    service = EntitlementsService(session)
    page = await service.list_studies(
        project_id=project_id, limit=limit_value, offset=offset_value
    )
    return EntStudyCollection(
        items=_model_list(EntStudySchema, page.items),
        total=page.total,
        limit=limit_value,
        offset=offset_value,
    )


@router.post(
    "/{project_id}/studies",
    response_model=EntStudySchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a study record",
)
async def create_study(
    project_id: int,
    payload: EntStudyCreate,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_reviewer),
) -> EntStudySchema:
    """Persist a new entitlement study."""

    if payload.project_id != project_id:
        raise HTTPException(status_code=400, detail="Project ID mismatch")
    service = EntitlementsService(session)
    record = await service.create_study(**payload.model_dump())
    await session.commit()
    await session.refresh(record)
    metrics.REQUEST_COUNTER.labels(endpoint="entitlements_study_create").inc()
    metrics.ENTITLEMENTS_STUDY_COUNTER.labels(operation="create").inc()
    return EntStudySchema.model_validate(record, from_attributes=True)


@router.put(
    "/{project_id}/studies/{study_id}",
    response_model=EntStudySchema,
    summary="Update a study",
)
async def update_study(
    project_id: int,
    study_id: int,
    payload: EntStudyUpdate,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_reviewer),
) -> EntStudySchema:
    """Modify an existing entitlement study."""

    data = payload.model_dump(exclude_unset=True)
    service = EntitlementsService(session)
    record = await service.update_study(
        study_id=study_id,
        project_id=project_id,
        **data,
    )
    await session.commit()
    await session.refresh(record)
    metrics.REQUEST_COUNTER.labels(endpoint="entitlements_study_update").inc()
    metrics.ENTITLEMENTS_STUDY_COUNTER.labels(operation="update").inc()
    return EntStudySchema.model_validate(record, from_attributes=True)


@router.delete(
    "/{project_id}/studies/{study_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a study",
)
async def delete_study(
    project_id: int,
    study_id: int,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_reviewer),
) -> Response:
    """Delete the specified study."""

    service = EntitlementsService(session)
    await service.delete_study(study_id=study_id, project_id=project_id)
    await session.commit()
    metrics.REQUEST_COUNTER.labels(endpoint="entitlements_study_delete").inc()
    metrics.ENTITLEMENTS_STUDY_COUNTER.labels(operation="delete").inc()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{project_id}/stakeholders",
    response_model=EntEngagementCollection,
    summary="List stakeholder engagements",
)
async def list_engagements(
    project_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> EntEngagementCollection:
    """Return stakeholder engagements for the project."""

    metrics.REQUEST_COUNTER.labels(endpoint="entitlements_engagement_list").inc()
    metrics.ENTITLEMENTS_ENGAGEMENT_COUNTER.labels(operation="list").inc()
    limit_value, offset_value = _normalise_pagination(limit, offset)
    service = EntitlementsService(session)
    page = await service.list_engagements(
        project_id=project_id, limit=limit_value, offset=offset_value
    )
    return EntEngagementCollection(
        items=_model_list(EntEngagementSchema, page.items),
        total=page.total,
        limit=limit_value,
        offset=offset_value,
    )


@router.post(
    "/{project_id}/stakeholders",
    response_model=EntEngagementSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a stakeholder engagement",
)
async def create_engagement(
    project_id: int,
    payload: EntEngagementCreate,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_reviewer),
) -> EntEngagementSchema:
    """Record a new stakeholder engagement."""

    if payload.project_id != project_id:
        raise HTTPException(status_code=400, detail="Project ID mismatch")
    service = EntitlementsService(session)
    record = await service.create_engagement(**payload.model_dump())
    await session.commit()
    await session.refresh(record)
    metrics.REQUEST_COUNTER.labels(endpoint="entitlements_engagement_create").inc()
    metrics.ENTITLEMENTS_ENGAGEMENT_COUNTER.labels(operation="create").inc()
    return EntEngagementSchema.model_validate(record, from_attributes=True)


@router.put(
    "/{project_id}/stakeholders/{engagement_id}",
    response_model=EntEngagementSchema,
    summary="Update a stakeholder engagement",
)
async def update_engagement(
    project_id: int,
    engagement_id: int,
    payload: EntEngagementUpdate,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_reviewer),
) -> EntEngagementSchema:
    """Modify an existing engagement record."""

    data = payload.model_dump(exclude_unset=True)
    service = EntitlementsService(session)
    record = await service.update_engagement(
        engagement_id=engagement_id,
        project_id=project_id,
        **data,
    )
    await session.commit()
    await session.refresh(record)
    metrics.REQUEST_COUNTER.labels(endpoint="entitlements_engagement_update").inc()
    metrics.ENTITLEMENTS_ENGAGEMENT_COUNTER.labels(operation="update").inc()
    return EntEngagementSchema.model_validate(record, from_attributes=True)


@router.delete(
    "/{project_id}/stakeholders/{engagement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a stakeholder engagement",
)
async def delete_engagement(
    project_id: int,
    engagement_id: int,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_reviewer),
) -> Response:
    """Remove an engagement record."""

    service = EntitlementsService(session)
    await service.delete_engagement(engagement_id=engagement_id, project_id=project_id)
    await session.commit()
    metrics.REQUEST_COUNTER.labels(endpoint="entitlements_engagement_delete").inc()
    metrics.ENTITLEMENTS_ENGAGEMENT_COUNTER.labels(operation="delete").inc()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{project_id}/legal",
    response_model=EntLegalInstrumentCollection,
    summary="List legal instruments",
)
async def list_legal_instruments(
    project_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> EntLegalInstrumentCollection:
    """Return paginated legal instruments."""

    metrics.REQUEST_COUNTER.labels(endpoint="entitlements_legal_list").inc()
    metrics.ENTITLEMENTS_LEGAL_COUNTER.labels(operation="list").inc()
    limit_value, offset_value = _normalise_pagination(limit, offset)
    service = EntitlementsService(session)
    page = await service.list_legal_instruments(
        project_id=project_id, limit=limit_value, offset=offset_value
    )
    return EntLegalInstrumentCollection(
        items=_model_list(EntLegalInstrumentSchema, page.items),
        total=page.total,
        limit=limit_value,
        offset=offset_value,
    )


@router.post(
    "/{project_id}/legal",
    response_model=EntLegalInstrumentSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a legal instrument",
)
async def create_legal_instrument(
    project_id: int,
    payload: EntLegalInstrumentCreate,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_reviewer),
) -> EntLegalInstrumentSchema:
    """Persist a new legal instrument."""

    if payload.project_id != project_id:
        raise HTTPException(status_code=400, detail="Project ID mismatch")
    service = EntitlementsService(session)
    record = await service.create_legal_instrument(**payload.model_dump())
    await session.commit()
    await session.refresh(record)
    metrics.REQUEST_COUNTER.labels(endpoint="entitlements_legal_create").inc()
    metrics.ENTITLEMENTS_LEGAL_COUNTER.labels(operation="create").inc()
    return EntLegalInstrumentSchema.model_validate(record, from_attributes=True)


@router.put(
    "/{project_id}/legal/{instrument_id}",
    response_model=EntLegalInstrumentSchema,
    summary="Update a legal instrument",
)
async def update_legal_instrument(
    project_id: int,
    instrument_id: int,
    payload: EntLegalInstrumentUpdate,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_reviewer),
) -> EntLegalInstrumentSchema:
    """Update an existing legal instrument."""

    data = payload.model_dump(exclude_unset=True)
    service = EntitlementsService(session)
    record = await service.update_legal_instrument(
        instrument_id=instrument_id,
        project_id=project_id,
        **data,
    )
    await session.commit()
    await session.refresh(record)
    metrics.REQUEST_COUNTER.labels(endpoint="entitlements_legal_update").inc()
    metrics.ENTITLEMENTS_LEGAL_COUNTER.labels(operation="update").inc()
    return EntLegalInstrumentSchema.model_validate(record, from_attributes=True)


@router.delete(
    "/{project_id}/legal/{instrument_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a legal instrument",
)
async def delete_legal_instrument(
    project_id: int,
    instrument_id: int,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_reviewer),
) -> Response:
    """Delete the specified legal instrument."""

    service = EntitlementsService(session)
    await service.delete_legal_instrument(
        instrument_id=instrument_id, project_id=project_id
    )
    await session.commit()
    metrics.REQUEST_COUNTER.labels(endpoint="entitlements_legal_delete").inc()
    metrics.ENTITLEMENTS_LEGAL_COUNTER.labels(operation="delete").inc()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{project_id}/export",
    response_class=StreamingResponse,
    summary="Export entitlement roadmap and registers",
)
async def export_entitlements(
    project_id: int,
    format: EntitlementsExportFormat = Query(EntitlementsExportFormat.CSV),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> StreamingResponse:
    """Export entitlement information in CSV, HTML, or PDF formats."""

    metrics.REQUEST_COUNTER.labels(endpoint="entitlements_export").inc()
    metrics.ENTITLEMENTS_EXPORT_COUNTER.labels(format=format.value).inc()
    payload, media_type, filename = await generate_entitlements_export(
        session, project_id=project_id, fmt=format
    )
    response = StreamingResponse(iter([payload]), media_type=media_type)
    disposition = f"attachment; filename={filename}"
    response.headers["content-disposition"] = disposition
    response.headers["Content-Disposition"] = disposition
    return response


__all__ = ["router"]
