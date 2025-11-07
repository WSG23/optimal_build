from __future__ import annotations

from app import jobs_registry


def test_enlist_default_jobs_registers_expected_handlers(monkeypatch):
    registered: list[tuple[str, str, str]] = []

    class StubQueue:
        def register(self, func, name: str, queue: str):
            registered.append((func.__name__, name, queue))

    monkeypatch.setattr(jobs_registry, "job_queue", StubQueue())
    jobs_registry.enlist_default_jobs()
    names = {entry[1] for entry in registered}
    assert "market.generate_report_bundle" in names
    assert "performance.generate_snapshots" in names
    assert "performance.seed_benchmarks" in names
