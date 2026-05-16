"""PDF pack generation endpoints for the commercial property agent flows."""

from __future__ import annotations

import os
from pathlib import Path as PathLib
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import FileResponse

from backend._compat.datetime import utcnow

from app.api.deps import RequestIdentity, Role, get_request_role, require_viewer
from app.api.v1.agents import _load_optional_class
from app.core.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/agents/commercial-property", tags=["Commercial Property Agent"]
)


def _report_storage_path(property_id: str, filename: str) -> PathLib:
    storage_base = PathLib(os.getenv("STORAGE_LOCAL_PATH", ".storage"))
    storage_prefix = os.getenv("STORAGE_PREFIX", "uploads")
    return storage_base / storage_prefix / "reports" / property_id / filename


@router.post("/properties/{property_id}/generate-pack/{pack_type}")
async def generate_professional_pack(
    property_id: str,
    pack_type: str = Path(..., pattern="^(universal|investment|sales|lease)$"),
    db: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
) -> dict[str, object]:
    """
    Generate professional PDF packs.

    Pack types:
    - universal: 20-page Universal Site Pack
    - investment: Institutional-grade Investment Memorandum
    - sales: Sales marketing brochure
    - lease: Leasing marketing brochure
    """
    del role

    try:
        property_uuid = UUID(property_id)

        if pack_type == "universal":
            generator_cls = _load_optional_class(
                "UniversalSitePackGenerator",
                "app.services.agents.universal_site_pack",
            )
            if generator_cls is None:
                raise HTTPException(
                    status_code=503,
                    detail="Universal Site Pack generation unavailable in this environment",
                )
            generator = generator_cls()
            pdf_buffer = await generator.generate(property_id=property_uuid, session=db)
            filename = f"universal_site_pack_{property_id}.pdf"

        elif pack_type == "investment":
            generator_cls = _load_optional_class(
                "InvestmentMemorandumGenerator",
                "app.services.agents.investment_memorandum",
            )
            if generator_cls is None:
                raise HTTPException(
                    status_code=503,
                    detail="Investment memorandum generation unavailable in this environment",
                )
            generator = generator_cls()
            pdf_buffer = await generator.generate(property_id=property_uuid, session=db)
            filename = f"investment_memorandum_{property_id}.pdf"

        elif pack_type in ["sales", "lease"]:
            generator_cls = _load_optional_class(
                "MarketingMaterialsGenerator",
                "app.services.agents.marketing_materials",
            )
            if generator_cls is None:
                raise HTTPException(
                    status_code=503,
                    detail="Marketing material generation unavailable in this environment",
                )
            generator = generator_cls()
            pdf_buffer = await generator.generate_sales_brochure(
                property_id=property_uuid,
                session=db,
                material_type="sale" if pack_type == "sales" else "lease",
            )
            filename = f"{pack_type}_brochure_{property_id}.pdf"

        else:
            raise HTTPException(status_code=400, detail="Invalid pack type")

        await generator.save_to_storage(
            pdf_buffer=pdf_buffer,
            filename=filename,
            property_id=property_id,
        )

        download_url = (
            "http://localhost:9400/api/v1/agents/commercial-property/files/"
            f"{property_id}/{filename}"
        )

        return {
            "pack_type": pack_type,
            "property_id": property_id,
            "filename": filename,
            "download_url": download_url,
            "generated_at": utcnow().isoformat(),
            "size_bytes": len(pdf_buffer.getvalue()),
        }

    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/files/{property_id}/{filename}")
async def download_generated_file(
    property_id: str,
    filename: str,
    _identity: RequestIdentity = Depends(require_viewer),
) -> FileResponse:
    """Download a generated PDF file from local storage."""

    file_path = _report_storage_path(property_id, filename)

    try:
        resolved_path = file_path.resolve()
        storage_base = PathLib(os.getenv("STORAGE_LOCAL_PATH", ".storage"))
        storage_prefix = os.getenv("STORAGE_PREFIX", "uploads")
        storage_root = (storage_base / storage_prefix).resolve()
        if not str(resolved_path).startswith(str(storage_root)):
            raise HTTPException(status_code=403, detail="Access denied")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid file path") from None

    if not resolved_path.exists() or not resolved_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(resolved_path),
        media_type="application/pdf",
        filename=filename,
    )
