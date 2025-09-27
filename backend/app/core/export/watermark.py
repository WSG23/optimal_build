"""Watermark helper utilities for exports."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.auth import PolicyContext, watermark_text


@dataclass(frozen=True)
class ExportPayload:
    content: bytes
    watermark: str | None = None


def apply_watermark(payload: ExportPayload, context: PolicyContext) -> ExportPayload:
    text = watermark_text(context)
    if not text:
        return payload
    if payload.watermark == text:
        return payload
    return ExportPayload(content=payload.content, watermark=text)


__all__ = ["ExportPayload", "apply_watermark"]
