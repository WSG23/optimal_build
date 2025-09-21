"""API endpoints for managing and validating rule packs."""

from __future__ import annotations

from typing import Any, Dict

try:  # pragma: no cover - FastAPI may be unavailable in offline environments
    from fastapi import APIRouter, Depends, HTTPException
except ModuleNotFoundError:  # pragma: no cover - provide lightweight fallbacks
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str | None = None) -> None:
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail or f"HTTP {status_code}")

    class APIRouter:  # type: ignore[override]
        def __init__(self) -> None:
            self.routes: list[tuple[str, str, Any]] = []

        def get(self, path: str, response_model: Any | None = None):
            def decorator(func: Any) -> Any:
                self.routes.append(("GET", path, func))
                return func

            return decorator

        def post(self, path: str, response_model: Any | None = None):
            def decorator(func: Any) -> Any:
                self.routes.append(("POST", path, func))
                return func

            return decorator

        def include_router(self, router: "APIRouter", prefix: str = "") -> None:
            for method, route_path, handler in getattr(router, "routes", []):
                combined = "/".join(
                    part.strip("/")
                    for part in (prefix or "", route_path or "")
                    if part is not None
                )
                self.routes.append((method, f"/{combined}".rstrip("/"), handler))

    def Depends(call: Any) -> Any:  # type: ignore[override]
        return call

from app.core.rules.engine import RuleEngine
from app.models.rulesets import (
    InMemoryRulePackRepository,
    RulePackRepository,
    SQLALCHEMY_INSTALLED,
    get_in_memory_repository,
)
from app.schemas.rulesets import (
    RulePackListResponse,
    RulePackResponse,
    RuleValidationResult,
    RulesetValidationRequest,
    RulesetValidationResponse,
)

router = APIRouter()

_sqlalchemy_runtime_available = False

if SQLALCHEMY_INSTALLED:  # pragma: no cover - executed only when dependency is available
    try:  # pragma: no cover - import may fail if SQLAlchemy is unavailable at runtime
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.core.database import get_session
        from app.models.rulesets import SQLAlchemyRulePackRepository

        _sqlalchemy_runtime_available = True

        async def get_ruleset_repository(
            session: AsyncSession = Depends(get_session),
        ) -> RulePackRepository:
            """Provide a SQLAlchemy-backed repository instance."""

            return SQLAlchemyRulePackRepository(session)

    except ModuleNotFoundError:  # pragma: no cover - fallback to in-memory behaviour
        _sqlalchemy_runtime_available = False


if not _sqlalchemy_runtime_available:

    async def get_ruleset_repository() -> InMemoryRulePackRepository:
        """Return the shared in-memory repository used for offline testing."""

        return get_in_memory_repository()


@router.get("/rulesets", response_model=RulePackListResponse)
async def list_rulesets(
    repository: RulePackRepository = Depends(get_ruleset_repository),
) -> Dict[str, Any]:
    """Return all stored rule packs."""

    packs = await repository.list()
    schemas = [RulePackResponse.model_validate(pack, from_attributes=True) for pack in packs]
    return {
        "items": [schema.model_dump(mode="json") for schema in schemas],
        "count": len(schemas),
    }


@router.post("/rulesets/validate", response_model=RulesetValidationResponse)
async def validate_ruleset(
    payload: RulesetValidationRequest,
    repository: RulePackRepository = Depends(get_ruleset_repository),
) -> Dict[str, Any]:
    """Validate geometry payloads against a stored rule pack."""

    ruleset = await repository.get(payload.ruleset_id)
    if ruleset is None:
        raise HTTPException(status_code=404, detail="Ruleset not found")

    engine = RuleEngine()
    evaluation = engine.validate(ruleset.rules, payload.geometries)
    result_models = [RuleValidationResult.model_validate(item) for item in evaluation["results"]]

    response = RulesetValidationResponse(
        ruleset=RulePackResponse.model_validate(ruleset, from_attributes=True),
        valid=bool(evaluation.get("valid", False)),
        results=result_models,
    )
    return response.model_dump(mode="json")


__all__ = ["router", "get_ruleset_repository"]

