"""Compatibility shim that exposes :mod:`backend.jobs` as ``jobs``."""

from __future__ import annotations

from importlib import import_module
import sys

_backend_jobs = import_module("backend.jobs")

# Replace this module entry so ``import jobs`` returns ``backend.jobs`` directly.
sys.modules[__name__] = _backend_jobs
