"""Response classes re-exported for compatibility."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import Response, StreamingResponse


class FileResponse(Response):
    """Minimal approximation of :class:`fastapi.responses.FileResponse`."""

    def __init__(
        self,
        path: str | Path,
        *,
        media_type: str | None = None,
        filename: str | None = None,
        headers: dict[str, Any] | None = None,
    ) -> None:
        file_path = Path(path)
        content = file_path.read_bytes()
        response_headers: dict[str, Any] = dict(headers or {})
        if filename is None:
            filename = file_path.name
        response_headers.setdefault(
            "content-disposition", f"attachment; filename={filename!r}"
        )
        super().__init__(
            content,
            media_type=media_type or "application/octet-stream",
            headers=response_headers,
        )


class JSONResponse(Response):
    """JSON response wrapper matching FastAPI's interface."""

    def __init__(
        self,
        content: Any,
        *,
        status_code: int = 200,
        headers: dict[str, Any] | None = None,
        media_type: str | None = "application/json",
    ) -> None:
        super().__init__(
            content,
            status_code=status_code,
            headers=headers,
            media_type=media_type or "application/json",
        )


__all__ = ["Response", "StreamingResponse", "FileResponse", "JSONResponse"]
