"""Notification utilities regressions."""

from backend.jobs import notifications


def test_notify_webhook_without_httpx(monkeypatch):
    monkeypatch.setattr(notifications, "httpx", None, raising=False)
    delivered = notifications.notify_webhook("https://example.invalid", {"ok": True})
    assert delivered is False
