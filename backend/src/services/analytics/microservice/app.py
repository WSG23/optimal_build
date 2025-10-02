"""Minimal FastAPI app for analytics microservice tests."""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="Analytics Microservice")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
