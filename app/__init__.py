"""Compatibility wrapper exposing :mod:`backend.app` as :mod:`app`.

This project historically imported modules using the short ``app`` package
name (for example ``from app.core.config import settings``).  In the current
repository layout the actual package lives under ``backend.app`` which breaks
those imports when the backend code is executed without installing the project
as a package.  Providing this lightweight wrapper keeps the original import
paths working by aliasing ``app`` to ``backend.app`` at import time.
"""

from __future__ import annotations

import sys
from importlib import import_module

# from backend._sqlalchemy_stub import ensure_sqlalchemy
# ensure_sqlalchemy()

_backend_app = import_module("backend.app")

# Expose ``backend.app`` under the historical ``app`` module name.  Using the
# existing module instance ensures submodules such as ``app.core`` resolve to
# the backend implementations without duplicating any package contents.
sys.modules[__name__] = _backend_app
