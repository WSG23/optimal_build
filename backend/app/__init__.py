"""Backend application package exposing compatibility aliases."""

from __future__ import annotations

import sys

_parent = sys.modules.get("backend")
if _parent is not None:
    setattr(_parent, "app", sys.modules[__name__])

_utils = sys.modules.get("backend.app.utils")
if _utils is not None:
    setattr(sys.modules[__name__], "utils", _utils)
