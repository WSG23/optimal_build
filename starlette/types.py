"""ASGI type aliases for the Starlette stub."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, MutableMapping

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

__all__ = ["Scope", "Message", "Receive", "Send", "ASGIApp"]
