"""Minimal uvicorn-compatible server for offline test environments."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import signal
from collections.abc import Callable, Iterable, Mapping
from http import HTTPStatus
from importlib import import_module
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlsplit

_Request = dict[str, Any]
_Response = tuple[int, list[tuple[str, str]], bytes]


@dataclass
class Config:
    """Runtime configuration for the lightweight server."""

    app: str | Callable[..., Any]
    host: str = "127.0.0.1"
    port: int = 8000


class Server:
    """Tiny HTTP/1.1 server compatible with FastAPI's testing stub."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._app: Any = None
        self._server: asyncio.AbstractServer | None = None
        self._shutdown = asyncio.Event()
        self._supports_handle_request = False
        self._lifespan_queue: asyncio.Queue[dict[str, str]] | None = None
        self._lifespan_task: asyncio.Task[Any] | None = None
        self._lifespan_error: Exception | None = None
        self._lifespan_shutdown = asyncio.Event()
        self._state: dict[str, Any] = {}

    def run(self) -> None:
        """Run the server until interrupted."""

        try:
            asyncio.run(self.serve())
        except KeyboardInterrupt:  # pragma: no cover - manual interruption
            pass

    async def serve(self) -> None:
        """Start listening for HTTP connections."""

        self._app = self._load_application(self.config.app)
        self._supports_handle_request = hasattr(self._app, "handle_request")

        try:
            if not self._supports_handle_request:
                await self._lifespan_start()
        except Exception:
            await self._lifespan_cleanup()
            raise

        try:
            self._server = await asyncio.start_server(
                self._handle_connection, host=self.config.host, port=self.config.port
            )
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                try:
                    loop.add_signal_handler(sig, self._shutdown.set)
                except (
                    NotImplementedError,
                    RuntimeError,
                ):  # pragma: no cover - platform specific
                    pass

            sockets = self._server.sockets or []
            bound = ", ".join(
                f"http://{sock.getsockname()[0]}:{sock.getsockname()[1]}"
                for sock in sockets
            )
            if bound:
                print(f"Uvicorn stub running on {bound} (Press CTRL+C to quit)")

            async with self._server:
                await self._shutdown.wait()
        except asyncio.CancelledError:  # pragma: no cover - defensive cancellation
            pass
        finally:
            if self._server is not None:
                self._server.close()
                await self._server.wait_closed()
            await self._lifespan_cleanup()

            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                with contextlib.suppress(
                    NotImplementedError, RuntimeError
                ):  # pragma: no cover - platform specific
                    loop.remove_signal_handler(sig)

    async def _handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            request = await self._read_request(reader)
            if request is None:
                return
            request["client"] = writer.get_extra_info("peername") or (None, None)
            status_code, headers, payload = await self._dispatch(request)
        except Exception as exc:  # pragma: no cover - defensive error handling
            status_code, headers, payload = self._build_error_response(exc)
        try:
            await self._write_response(writer, status_code, headers, payload)
        finally:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()

    async def _read_request(self, reader: asyncio.StreamReader) -> _Request | None:
        request_line = await reader.readline()
        if not request_line:
            return None
        try:
            method, target, http_version = (
                request_line.decode("latin-1").strip().split()
            )
        except ValueError as exc:
            raise ValueError("Malformed HTTP request line") from exc

        headers: list[tuple[str, str]] = []
        content_length = 0
        content_type = ""
        while True:
            line = await reader.readline()
            if line in {b"\r\n", b"\n", b""}:
                break
            try:
                name, value = line.decode("latin-1").split(":", 1)
            except ValueError as exc:
                raise ValueError("Malformed HTTP header line") from exc
            header_name = name.strip()
            header_value = value.strip()
            headers.append((header_name, header_value))
            if header_name.lower() == "content-length":
                try:
                    content_length = int(header_value)
                except ValueError as length_exc:
                    raise ValueError("Invalid Content-Length header") from length_exc
            elif header_name.lower() == "content-type":
                content_type = header_value

        body = b""
        if content_length > 0:
            body = await reader.readexactly(content_length)

        return {
            "method": method,
            "target": target,
            "http_version": http_version,
            "headers": headers,
            "body": body,
            "content_type": content_type,
        }

    async def _dispatch(self, request: _Request) -> _Response:
        split = urlsplit(request["target"])
        path = split.path or "/"
        query_params = {
            key: values[0] if len(values) == 1 else values
            for key, values in parse_qs(split.query, keep_blank_values=True).items()
        }
        headers = {name.lower(): value for name, value in request["headers"]}

        if self._supports_handle_request:
            json_body: Any = None
            form_data: Mapping[str, Any] | None = None
            files: Mapping[str, Any] | None = None
            body = request["body"]
            content_type = headers.get("content-type", "")
            if body:
                if "application/json" in content_type:
                    try:
                        json_body = json.loads(body.decode("utf-8"))
                    except json.JSONDecodeError as exc:
                        raise ValueError("Invalid JSON payload") from exc
                elif "application/x-www-form-urlencoded" in content_type:
                    parsed = parse_qs(body.decode("utf-8"), keep_blank_values=True)
                    form_data = {
                        k: v[0] if len(v) == 1 else v for k, v in parsed.items()
                    }
            status_code, response_headers, payload = await self._app.handle_request(  # type: ignore[call-arg]
                method=request["method"],
                path=path,
                query_params=query_params,
                json_body=json_body,
                form_data=form_data,
                files=files,
                headers=headers,
            )
            header_items = (
                list(response_headers.items())
                if isinstance(response_headers, Mapping)
                else list(response_headers)
            )
            normalised_headers = [
                (str(name), str(value)) for name, value in header_items
            ]
            return status_code, normalised_headers, payload

        return await self._dispatch_asgi(request, path, split.query)

    async def _dispatch_asgi(
        self, request: _Request, path: str, query_string: str
    ) -> _Response:
        body = request["body"]
        headers = [
            (
                name.lower().encode("latin-1"),
                value.encode("latin-1"),
            )
            for name, value in request["headers"]
        ]
        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.1"},
            "http_version": request["http_version"].replace("HTTP/", ""),
            "method": request["method"],
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("utf-8"),
            "query_string": query_string.encode("latin-1"),
            "headers": headers,
            "client": request.get("client"),
            "server": (self.config.host, self.config.port),
            "state": self._state,
        }

        body_sent = False
        response_headers: list[tuple[bytes, bytes]] = []
        body_chunks: list[bytes] = []
        status_code = 500

        async def receive() -> dict[str, Any]:
            nonlocal body_sent
            if not body_sent:
                body_sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            await asyncio.sleep(0)
            return {"type": "http.disconnect"}

        async def send(message: Mapping[str, Any]) -> None:
            nonlocal status_code
            message_type = message.get("type")
            if message_type == "http.response.start":
                try:
                    status_code = int(message.get("status", 200))
                except (TypeError, ValueError):
                    status_code = 200
                response_headers.clear()
                for header_name, header_value in message.get("headers", []) or []:
                    if isinstance(header_name, (bytes, bytearray)):
                        name_bytes = bytes(header_name)
                    else:
                        name_bytes = str(header_name).encode("latin-1")
                    if isinstance(header_value, (bytes, bytearray)):
                        value_bytes = bytes(header_value)
                    else:
                        value_bytes = str(header_value).encode("latin-1")
                    response_headers.append((name_bytes, value_bytes))
            elif message_type == "http.response.body":
                chunk = message.get("body", b"")
                if not isinstance(chunk, (bytes, bytearray)):
                    chunk = str(chunk).encode("utf-8")
                body_chunks.append(bytes(chunk))
            # Other ASGI message types are ignored by the stub.

        await self._app(scope, receive, send)  # type: ignore[misc]

        payload = b"".join(body_chunks)
        header_items = [
            (name.decode("latin-1"), value.decode("latin-1"))
            for name, value in response_headers
        ]
        return status_code, header_items, payload

    async def _write_response(
        self,
        writer: asyncio.StreamWriter,
        status_code: int,
        headers: Iterable[tuple[str, str]],
        body: bytes,
    ) -> None:
        if not isinstance(body, (bytes, bytearray)):
            body = bytes(body)
        header_list = list(headers)
        if not any(name.lower() == "content-length" for name, _ in header_list):
            header_list.append(("content-length", str(len(body))))
        if not any(name.lower() == "connection" for name, _ in header_list):
            header_list.append(("connection", "close"))

        try:
            reason = HTTPStatus(status_code).phrase
        except ValueError:
            reason = "OK"

        writer.write(f"HTTP/1.1 {status_code} {reason}\r\n".encode("latin-1"))
        for name, value in header_list:
            writer.write(f"{name}: {value}\r\n".encode("latin-1"))
        writer.write(b"\r\n")
        if body:
            writer.write(body)
        await writer.drain()

    def _build_error_response(self, exc: Exception) -> _Response:
        payload = json.dumps({"detail": str(exc)}).encode("utf-8")
        headers = [("content-type", "application/json")]
        return (HTTPStatus.INTERNAL_SERVER_ERROR.value, headers, payload)

    async def _lifespan_start(self) -> None:
        queue: asyncio.Queue[dict[str, str]] = asyncio.Queue()
        startup_event = asyncio.Event()
        shutdown_event = asyncio.Event()
        self._lifespan_error = None

        async def receive() -> dict[str, str]:
            return await queue.get()

        async def send(message: Mapping[str, Any]) -> None:
            message_type = message.get("type")
            if message_type == "lifespan.startup.complete":
                startup_event.set()
            elif message_type == "lifespan.shutdown.complete":
                shutdown_event.set()
            elif message_type == "lifespan.startup.failed":
                self._lifespan_error = RuntimeError(
                    message.get("message", "lifespan startup failed")
                )
                startup_event.set()
            elif message_type == "lifespan.shutdown.failed":
                self._lifespan_error = RuntimeError(
                    message.get("message", "lifespan shutdown failed")
                )
                shutdown_event.set()

        scope = {
            "type": "lifespan",
            "asgi": {"version": "3.0", "spec_version": "2.1"},
            "state": self._state,
        }

        task = asyncio.create_task(self._app(scope, receive, send))  # type: ignore[misc]
        await queue.put({"type": "lifespan.startup"})
        await startup_event.wait()
        if self._lifespan_error:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
            raise self._lifespan_error

        self._lifespan_queue = queue
        self._lifespan_task = task
        self._lifespan_shutdown = shutdown_event

    async def _lifespan_cleanup(self) -> None:
        if self._lifespan_queue is None or self._lifespan_task is None:
            return
        await self._lifespan_queue.put({"type": "lifespan.shutdown"})
        await self._lifespan_shutdown.wait()
        self._lifespan_queue = None
        if self._lifespan_error:
            raise self._lifespan_error
        with contextlib.suppress(asyncio.CancelledError):
            await self._lifespan_task
        self._lifespan_task = None

    @staticmethod
    def _load_application(target: str | Callable[..., Any]) -> Any:
        if callable(target):
            return target
        module_path, _, attribute = target.partition(":")
        if not module_path:
            raise ImportError("Invalid application import string")
        module = import_module(module_path)
        obj: Any = module
        if attribute:
            for attr in attribute.split("."):
                if not attr:
                    continue
                obj = getattr(obj, attr)
        return obj


def run(
    app: str | Callable[..., Any], *, host: str = "127.0.0.1", port: int = 8000
) -> None:
    """Run the server for the supplied application."""

    server = Server(Config(app=app, host=host, port=port))
    server.run()


def main(argv: Iterable[str] | None = None) -> None:
    """Entry point emulating ``uvicorn``'s CLI."""

    parser = argparse.ArgumentParser(description="Lightweight uvicorn stub")
    parser.add_argument("app", help="Application import string, e.g. module:app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Reload is not supported in the stub implementation.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.reload:
        print("Reload option is not supported by the uvicorn stub.")

    run(args.app, host=args.host, port=args.port)


__all__ = ["Config", "Server", "run", "main"]
