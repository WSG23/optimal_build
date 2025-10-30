"""Minimal OpenAPI utilities for the FastAPI shadow implementation."""

from __future__ import annotations

from typing import Any


def get_openapi(
    *,
    title: str,
    version: str,
    openapi_version: str = "3.1.0",
    summary: str | None = None,
    description: str | None = None,
    routes: Any = None,
    tags: list[dict[str, Any]] | None = None,
    servers: list[dict[str, Any]] | None = None,
    terms_of_service: str | None = None,
    contact: dict[str, Any] | None = None,
    license_info: dict[str, Any] | None = None,
    webhooks: Any = None,
    separate_input_output_schemas: bool = True,
) -> dict[str, Any]:
    """Generate a minimal OpenAPI schema for the FastAPI application.

    This is a stub implementation that returns a basic schema structure.
    In a real implementation, this would introspect routes and generate
    a complete OpenAPI specification.
    """
    info: dict[str, Any] = {
        "title": title,
        "version": version,
    }

    if summary:
        info["summary"] = summary
    if description:
        info["description"] = description
    if terms_of_service:
        info["termsOfService"] = terms_of_service
    if contact:
        info["contact"] = contact
    if license_info:
        info["license"] = license_info

    schema: dict[str, Any] = {
        "openapi": openapi_version,
        "info": info,
        "paths": {},
    }

    if tags:
        schema["tags"] = tags
    if servers:
        schema["servers"] = servers

    return schema


__all__ = ["get_openapi"]
