"""Entitlement management endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequestUser, require_reviewer, require_viewer
from app.core.database import get_session
from app.core.export.entitlements import (
    EntitlementsExportError,
    generate_entitlements_export,
)
from app.schemas import entitlements as schema
from app.services.entitlements import EntitlementNotFoundError, EntitlementsService
from app.utils import metrics


router = APIRouter(prefix="/entitlements", tags=["Entitlements"])


def _service(session: AsyncSession) -> EntitlementsService:
    return EntitlementsService(session)


def _provenance() -> schema.ProvenanceStamp:
    return schema.ProvenanceStamp(generated_at=datetime.now(timezone.utc))


@router.get(
    "/roadmap/{project_id}",
    response_model=schema.RoadmapCollection,
    summary="List roadmap items for a project",
)
async def list_roadmap_items(
    project_id: int,
    *,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    _: RequestUser = Depends(require_viewer),
) -> schema.RoadmapCollection:
    metrics.ENTITLEMENTS_REQUEST_COUNTER.labels(resource="roadmap", method="GET").inc()
    service = _service(session)
    result = await service.list_roadmap(project_id=project_id, limit=limit, offset=offset)
    return schema.RoadmapCollection(items=list(result.items), total=result.total, provenance=_provenance())


@router.post(
    "/roadmap/{project_id}",
    response_model=schema.RoadmapItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create a roadmap item",
)
async def create_roadmap_item(
    project_id: int,
    payload: schema.RoadmapItemCreate,
    *,
    session: AsyncSession = Depends(get_session),
    _: RequestUser = Depends(require_reviewer),
) -> schema.RoadmapItem:
    metrics.ENTITLEMENTS_REQUEST_COUNTER.labels(resource="roadmap", method="POST").inc()
    service = _service(session)
    try:
        item = await service.create_roadmap_item(project_id=project_id, payload=payload)
        await session.commit()
        return item
    except EntitlementNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put(
    "/roadmap/{project_id}/{item_id}",
    response_model=schema.RoadmapItem,
    summary="Update a roadmap item",
)
async def update_roadmap_item(
    project_id: int,
    item_id: int,
    payload: schema.RoadmapItemUpdate,
    *,
    session: AsyncSession = Depends(get_session),
    _: RequestUser = Depends(require_reviewer),
) -> schema.RoadmapItem:
    metrics.ENTITLEMENTS_REQUEST_COUNTER.labels(resource="roadmap", method="PUT").inc()
    service = _service(session)
    try:
        item = await service.update_roadmap_item(
            project_id=project_id, item_id=item_id, payload=payload
        )
        await session.commit()
        return item
    except EntitlementNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/roadmap/{project_id}/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a roadmap item",
)
async def delete_roadmap_item(
    project_id: int,
    item_id: int,
    *,
    session: AsyncSession = Depends(get_session),
    _: RequestUser = Depends(require_reviewer),
) -> Response:
    metrics.ENTITLEMENTS_REQUEST_COUNTER.labels(resource="roadmap", method="DELETE").inc()
    service = _service(session)
    try:
        await service.delete_roadmap_item(project_id=project_id, item_id=item_id)
        await session.commit()
    except EntitlementNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/studies/{project_id}",
    response_model=schema.StudyCollection,
    summary="List entitlement studies",
)
async def list_studies(
    project_id: int,
    *,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    _: RequestUser = Depends(require_viewer),
) -> schema.StudyCollection:
    metrics.ENTITLEMENTS_REQUEST_COUNTER.labels(resource="studies", method="GET").inc()
    service = _service(session)
    result = await service.list_studies(project_id=project_id, limit=limit, offset=offset)
    return schema.StudyCollection(items=list(result.items), total=result.total, provenance=_provenance())


@router.post(
    "/studies/{project_id}",
    response_model=schema.Study,
    status_code=status.HTTP_201_CREATED,
    summary="Create a study",
)
async def create_study(
    project_id: int,
    payload: schema.StudyCreate,
    *,
    session: AsyncSession = Depends(get_session),
    _: RequestUser = Depends(require_reviewer),
) -> schema.Study:
    metrics.ENTITLEMENTS_REQUEST_COUNTER.labels(resource="studies", method="POST").inc()
    service = _service(session)
    study = await service.create_study(project_id=project_id, payload=payload)
    await session.commit()
    return study


@router.put(
    "/studies/{project_id}/{study_id}",
    response_model=schema.Study,
    summary="Update a study",
)
async def update_study(
    project_id: int,
    study_id: int,
    payload: schema.StudyUpdate,
    *,
    session: AsyncSession = Depends(get_session),
    _: RequestUser = Depends(require_reviewer),
) -> schema.Study:
    metrics.ENTITLEMENTS_REQUEST_COUNTER.labels(resource="studies", method="PUT").inc()
    service = _service(session)
    try:
        study = await service.update_study(project_id=project_id, study_id=study_id, payload=payload)
        await session.commit()
        return study
    except EntitlementNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/studies/{project_id}/{study_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a study",
)
async def delete_study(
    project_id: int,
    study_id: int,
    *,
    session: AsyncSession = Depends(get_session),
    _: RequestUser = Depends(require_reviewer),
) -> Response:
    metrics.ENTITLEMENTS_REQUEST_COUNTER.labels(resource="studies", method="DELETE").inc()
    service = _service(session)
    try:
        await service.delete_study(project_id=project_id, study_id=study_id)
        await session.commit()
    except EntitlementNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/stakeholders/{project_id}",
    response_model=schema.StakeholderCollection,
    summary="List stakeholder engagements",
)
async def list_stakeholders(
    project_id: int,
    *,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    _: RequestUser = Depends(require_viewer),
) -> schema.StakeholderCollection:
    metrics.ENTITLEMENTS_REQUEST_COUNTER.labels(resource="stakeholders", method="GET").inc()
    service = _service(session)
    result = await service.list_stakeholders(project_id=project_id, limit=limit, offset=offset)
    return schema.StakeholderCollection(items=list(result.items), total=result.total, provenance=_provenance())


@router.post(
    "/stakeholders/{project_id}",
    response_model=schema.Stakeholder,
    status_code=status.HTTP_201_CREATED,
    summary="Create a stakeholder engagement",
)
async def create_stakeholder(
    project_id: int,
    payload: schema.StakeholderCreate,
    *,
    session: AsyncSession = Depends(get_session),
    _: RequestUser = Depends(require_reviewer),
) -> schema.Stakeholder:
    metrics.ENTITLEMENTS_REQUEST_COUNTER.labels(resource="stakeholders", method="POST").inc()
    service = _service(session)
    stakeholder = await service.create_stakeholder(project_id=project_id, payload=payload)
    await session.commit()
    return stakeholder


@router.put(
    "/stakeholders/{project_id}/{engagement_id}",
    response_model=schema.Stakeholder,
    summary="Update a stakeholder engagement",
)
async def update_stakeholder(
    project_id: int,
    engagement_id: int,
    payload: schema.StakeholderUpdate,
    *,
    session: AsyncSession = Depends(get_session),
    _: RequestUser = Depends(require_reviewer),
) -> schema.Stakeholder:
    metrics.ENTITLEMENTS_REQUEST_COUNTER.labels(resource="stakeholders", method="PUT").inc()
    service = _service(session)
    try:
        stakeholder = await service.update_stakeholder(
            project_id=project_id, stakeholder_id=engagement_id, payload=payload
        )
        await session.commit()
        return stakeholder
    except EntitlementNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/stakeholders/{project_id}/{engagement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a stakeholder engagement",
)
async def delete_stakeholder(
    project_id: int,
    engagement_id: int,
    *,
    session: AsyncSession = Depends(get_session),
    _: RequestUser = Depends(require_reviewer),
) -> Response:
    metrics.ENTITLEMENTS_REQUEST_COUNTER.labels(resource="stakeholders", method="DELETE").inc()
    service = _service(session)
    try:
        await service.delete_stakeholder(project_id=project_id, stakeholder_id=engagement_id)
        await session.commit()
    except EntitlementNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/legal/{project_id}",
    response_model=schema.LegalInstrumentCollection,
    summary="List legal instruments",
)
async def list_legal_instruments(
    project_id: int,
    *,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    _: RequestUser = Depends(require_viewer),
) -> schema.LegalInstrumentCollection:
    metrics.ENTITLEMENTS_REQUEST_COUNTER.labels(resource="legal", method="GET").inc()
    service = _service(session)
    result = await service.list_legal_instruments(project_id=project_id, limit=limit, offset=offset)
    return schema.LegalInstrumentCollection(items=list(result.items), total=result.total, provenance=_provenance())


@router.post(
    "/legal/{project_id}",
    response_model=schema.LegalInstrument,
    status_code=status.HTTP_201_CREATED,
    summary="Create a legal instrument",
)
async def create_legal_instrument(
    project_id: int,
    payload: schema.LegalInstrumentCreate,
    *,
    session: AsyncSession = Depends(get_session),
    _: RequestUser = Depends(require_reviewer),
) -> schema.LegalInstrument:
    metrics.ENTITLEMENTS_REQUEST_COUNTER.labels(resource="legal", method="POST").inc()
    service = _service(session)
    instrument = await service.create_legal_instrument(project_id=project_id, payload=payload)
    await session.commit()
    return instrument


@router.put(
    "/legal/{project_id}/{instrument_id}",
    response_model=schema.LegalInstrument,
    summary="Update a legal instrument",
)
async def update_legal_instrument(
    project_id: int,
    instrument_id: int,
    payload: schema.LegalInstrumentUpdate,
    *,
    session: AsyncSession = Depends(get_session),
    _: RequestUser = Depends(require_reviewer),
) -> schema.LegalInstrument:
    metrics.ENTITLEMENTS_REQUEST_COUNTER.labels(resource="legal", method="PUT").inc()
    service = _service(session)
    try:
        instrument = await service.update_legal_instrument(
            project_id=project_id, instrument_id=instrument_id, payload=payload
        )
        await session.commit()
        return instrument
    except EntitlementNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/legal/{project_id}/{instrument_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a legal instrument",
)
async def delete_legal_instrument(
    project_id: int,
    instrument_id: int,
    *,
    session: AsyncSession = Depends(get_session),
    _: RequestUser = Depends(require_reviewer),
) -> Response:
    metrics.ENTITLEMENTS_REQUEST_COUNTER.labels(resource="legal", method="DELETE").inc()
    service = _service(session)
    try:
        await service.delete_legal_instrument(project_id=project_id, instrument_id=instrument_id)
        await session.commit()
    except EntitlementNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/export/{project_id}",
    summary="Export entitlements for a project",
)
async def export_entitlements(
    project_id: int,
    *,
    fmt: schema.EntitlementExportFormat = Query(schema.EntitlementExportFormat.CSV),
    session: AsyncSession = Depends(get_session),
    _: RequestUser = Depends(require_viewer),
) -> StreamingResponse:
    metrics.ENTITLEMENTS_REQUEST_COUNTER.labels(resource="export", method="GET").inc()
    service = _service(session)
    try:
        export_payload = await generate_entitlements_export(
            service=service, project_id=project_id, fmt=fmt
        )
    except EntitlementsExportError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    metrics.ENTITLEMENTS_EXPORT_COUNTER.labels(
        format=export_payload.format.value,
        fallback="yes" if export_payload.fallback else "no",
    ).inc()

    headers = {
        "Content-Disposition": f"attachment; filename={export_payload.filename}",
    }
    if export_payload.fallback:
        headers["X-Export-Fallback"] = export_payload.fallback

    return StreamingResponse(
        export_payload.stream(),
        media_type=export_payload.media_type,
        headers=headers,
    )


__all__ = ["router"]
