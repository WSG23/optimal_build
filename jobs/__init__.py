"""Compatibility wrapper exposing :mod:`backend.jobs` as :mod:`jobs`."""

from __future__ import annotations

from importlib import import_module
import sys

_backend_jobs = import_module("backend.jobs")

# Reuse the backend implementation so imports like ``from jobs import job``
# continue to resolve without installing the package.
sys.modules[__name__] = _backend_jobs
