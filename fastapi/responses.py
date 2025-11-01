"""Response objects for the FastAPI stub."""

from __future__ import annotations

from typing import Any, Iterable

__all__ = ["Response", "StreamingResponse"]


class Response:
    """Minimal HTTP response container."""

    def __init__(self, content: Any = b"", status_code: int = 200, media_type: str = "application/json") -> None:
        if isinstance(content, bytes):
            body = content
        elif content is None:
            body = b""
        else:
            body = str(content).encode("utf-8")
        self._body = body
        self.status_code = status_code
        self.media_type = media_type

    @property
    def body(self) -> bytes:
        return self._body


class StreamingResponse(Response):
    """Extremely small streaming response implementation."""

    def __init__(self, content: Iterable[bytes], status_code: int = 200, media_type: str = "application/octet-stream") -> None:
        aggregated = b"".join(content)
        super().__init__(aggregated, status_code=status_code, media_type=media_type)


__all__ = ["Response", "StreamingResponse"]
