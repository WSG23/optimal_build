"""CLI entry point delegating to the repository-level uvicorn stub."""

from __future__ import annotations

from uvicorn_app.__main__ import main

if __name__ == "__main__":
    main()
