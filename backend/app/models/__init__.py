"""Model package exports."""

from __future__ import annotations

import sys
from types import ModuleType


def _counterpart(name: str) -> str | None:
    """Return the alternate import path for ``app``/``backend.app`` modules."""

    if name.startswith("backend."):
        return name.removeprefix("backend.")
    if name.startswith("app."):
        return f"backend.{name}"
    return None


_ALIAS = _counterpart(__name__)
if _ALIAS and _ALIAS in sys.modules:
    _existing: ModuleType = sys.modules[_ALIAS]
    globals().update(_existing.__dict__)
    sys.modules[__name__] = _existing
else:
    # Import model modules so their metadata is registered with SQLAlchemy.
    from . import agent_advisory  # Added: agent advisory feedback model
    from . import ai_agents  # Added: AI agents model
    from . import ai_config  # Added: AI configuration model
    from . import developer_condition  # Added: developer condition assessments
    from . import development_phase  # Added: Phase 2D development phases
    from . import hong_kong_property  # Added: Hong Kong property model
    from . import listing_integration  # Added: external listing integrations
    from . import new_zealand_property  # Added: New Zealand property model
    from . import projects  # Added: development projects model
    from . import seattle_property  # Added: Seattle property model
    from . import singapore_property  # Added: Singapore property model
    from . import toronto_property  # Added: Toronto property model
    from . import users  # Added: user authentication model
    from . import team  # Added: Phase 2E team management
    from . import workflow  # Added: Phase 2E approval workflows
    from . import (  # noqa: F401  pylint: disable=unused-import
        audit,
        business_performance,
        developer_checklists,
        entitlements,
        finance,
        imports,
        overlay,
        preview,
        property as property_model,
        rkp,
        rulesets,
        regulatory,
    )
    from .base import Base  # noqa: F401

    _SUBMODULES: dict[str, ModuleType] = {
        "agent_advisory": agent_advisory,  # Added: agent advisory feedback model
        "ai_agents": ai_agents,  # Added: AI agents model
        "ai_config": ai_config,  # Added: AI configuration model
        "developer_condition": developer_condition,
        "development_phase": development_phase,  # Added: Phase 2D development phases
        "hong_kong_property": hong_kong_property,  # Added: Hong Kong property model
        "new_zealand_property": new_zealand_property,  # Added: New Zealand property model
        "seattle_property": seattle_property,  # Added: Seattle property model
        "audit": audit,
        "business_performance": business_performance,
        "developer_checklists": developer_checklists,
        "entitlements": entitlements,
        "finance": finance,
        "imports": imports,
        "overlay": overlay,
        "preview": preview,
        "property": property_model,
        "listing_integration": listing_integration,
        "projects": projects,  # Added: development projects model
        "rkp": rkp,
        "rulesets": rulesets,
        "singapore_property": singapore_property,  # Added: Singapore property model
        "toronto_property": toronto_property,  # Added: Toronto property model
        "users": users,  # Added: user authentication model
        "team": team,  # Added: Phase 2E team management
        "workflow": workflow,  # Added: Phase 2E approval workflows
        "regulatory": regulatory,
    }

    for _name, _module in _SUBMODULES.items():
        _module_alias = _counterpart(f"{__name__}.{_name}")
        if _module_alias and _module_alias not in sys.modules:
            sys.modules[_module_alias] = _module

    __all__ = ["Base"]

    if _ALIAS:
        sys.modules[_ALIAS] = sys.modules[__name__]
