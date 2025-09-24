"""Model package exports."""

from .base import Base  # noqa: F401

import sys

# Import model modules so their metadata is registered with SQLAlchemy.
from . import audit, entitlements, finance, imports, overlay, rkp, rulesets  # noqa: F401  pylint: disable=unused-import

if __name__.startswith("backend.app"):
    sys.modules["app.models"] = sys.modules[__name__]
else:  # pragma: no cover
    sys.modules["backend.app.models"] = sys.modules[__name__]

__all__ = ["Base"]
