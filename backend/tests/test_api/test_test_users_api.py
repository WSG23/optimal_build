from __future__ import annotations

import pytest

from app.api.v1 import test_users as test_users_module


@pytest.fixture(autouse=True)
def clear_fake_users_db():
    test_users_module.fake_users_db.clear()
    yield
    test_users_module.fake_users_db.clear()


@pytest.mark.asyncio
async def test_test_users_healthcheck(client):
    response = await client.get("/api/v1/users/test")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert "Users API" in payload["message"]


@pytest.mark.asyncio
async def test_signup_creates_user_and_masks_password(client):
    payload = {
        "email": "demo@example.com",
        "username": "demo",
        "full_name": "Demo User",
        "password": "plaintext",
    }
    response = await client.post("/api/v1/users/signup", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == payload["email"]
    assert body["message"] == "User registered successfully!"

    list_response = await client.get("/api/v1/users/list")
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["total"] == 1
    stored_user = list_payload["users"][0]
    assert stored_user["email"] == payload["email"]
    assert "password" not in stored_user


@pytest.mark.asyncio
async def test_signup_rejects_duplicate_email(client):
    payload = {
        "email": "dup@example.com",
        "username": "dup",
        "full_name": "Dup User",
        "password": "plaintext",
    }
    first = await client.post("/api/v1/users/signup", json=payload)
    assert first.status_code == 200

    second = await client.post("/api/v1/users/signup", json=payload)
    assert second.status_code == 400
    assert second.json()["detail"] == "Email already registered"
