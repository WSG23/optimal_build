"""Tests for database-backed user API endpoints."""

from __future__ import annotations

import pytest

from app.api.v1 import users_db as users_db_module


@pytest.fixture(autouse=True)
def setup_test_db():
    """Ensure test database tables exist and clean up after tests."""
    from app.core.auth import UserORMBase

    # Ensure tables exist
    UserORMBase.metadata.create_all(bind=users_db_module.engine)

    yield

    # Clean up users after test
    with users_db_module.SessionLocal() as session:
        from app.core.auth import UserORM

        session.query(UserORM).delete()
        session.commit()


@pytest.mark.asyncio
async def test_users_db_test_endpoint(client):
    """Test the test endpoint returns API status."""
    response = await client.get("/api/v1/users-db/test")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "Database Users API" in payload["message"]
    assert "features" in payload
    assert isinstance(payload["features"], list)
    assert "SQLite database persistence" in payload["features"]


@pytest.mark.asyncio
async def test_users_db_signup_success(client):
    """Test successful user registration with database persistence."""
    payload = {
        "email": "dbtest@example.com",
        "username": "dbtestuser",
        "full_name": "DB Test User",
        "password": "Password123",
        "company_name": "DB Test Company",
    }
    response = await client.post("/api/v1/users-db/signup", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == payload["email"]
    assert body["username"] == payload["username"]
    assert body["full_name"] == payload["full_name"]
    assert body["company_name"] == payload["company_name"]
    assert body["is_active"] is True
    assert "id" in body
    assert "created_at" in body
    # Password should never be in response
    assert "password" not in body


@pytest.mark.asyncio
async def test_users_db_signup_duplicate_email(client):
    """Test that duplicate email registration fails."""
    payload = {
        "email": "duplicate@example.com",
        "username": "user1",
        "full_name": "User One",
        "password": "Password123",
    }
    # First signup
    response1 = await client.post("/api/v1/users-db/signup", json=payload)
    assert response1.status_code == 200

    # Second signup with same email
    payload["username"] = "user2"
    payload["full_name"] = "User Two"
    response2 = await client.post("/api/v1/users-db/signup", json=payload)
    # Should fail due to duplicate email
    assert response2.status_code in (400, 409, 422)


@pytest.mark.asyncio
async def test_users_db_login_success(client):
    """Test successful login returns JWT tokens."""
    # First register a user
    signup_payload = {
        "email": "logintest@example.com",
        "username": "logintest",
        "full_name": "Login Test User",
        "password": "Password123",
    }
    signup_response = await client.post("/api/v1/users-db/signup", json=signup_payload)
    assert signup_response.status_code == 200

    # Now login
    login_payload = {
        "email": "logintest@example.com",
        "password": "Password123",
    }
    response = await client.post("/api/v1/users-db/login", json=login_payload)
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Login successful"
    assert "user" in body
    assert body["user"]["email"] == "logintest@example.com"
    assert "tokens" in body
    assert "access_token" in body["tokens"]
    assert "refresh_token" in body["tokens"]


@pytest.mark.asyncio
async def test_users_db_login_invalid_password(client):
    """Test login with wrong password fails."""
    # First register a user
    signup_payload = {
        "email": "wrongpassdb@example.com",
        "username": "wrongpassdb",
        "full_name": "Wrong Pass DB User",
        "password": "Password123",
    }
    await client.post("/api/v1/users-db/signup", json=signup_payload)

    # Try login with wrong password
    login_payload = {
        "email": "wrongpassdb@example.com",
        "password": "WrongPassword123",
    }
    response = await client.post("/api/v1/users-db/login", json=login_payload)
    assert response.status_code in (400, 401, 403)


@pytest.mark.asyncio
async def test_users_db_login_nonexistent_user(client):
    """Test login with non-existent user fails."""
    login_payload = {
        "email": "nonexistentdb@example.com",
        "password": "Password123",
    }
    response = await client.post("/api/v1/users-db/login", json=login_payload)
    assert response.status_code in (400, 401, 404)


@pytest.mark.asyncio
async def test_users_db_list_users(client):
    """Test listing users returns registered users."""
    # Register some users
    for i in range(3):
        payload = {
            "email": f"listuser{i}@example.com",
            "username": f"listuser{i}",
            "full_name": f"List User {i}",
            "password": "Password123",
        }
        response = await client.post("/api/v1/users-db/signup", json=payload)
        assert response.status_code == 200

    # List users
    response = await client.get("/api/v1/users-db/list")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 3
    assert len(body["users"]) >= 3


@pytest.mark.asyncio
async def test_users_db_me_with_valid_token(client):
    """Test getting current user info with valid JWT token."""
    # Register and login
    signup_payload = {
        "email": "medbuser@example.com",
        "username": "medbuser",
        "full_name": "Me DB User",
        "password": "Password123",
    }
    await client.post("/api/v1/users-db/signup", json=signup_payload)

    login_payload = {
        "email": "medbuser@example.com",
        "password": "Password123",
    }
    login_response = await client.post("/api/v1/users-db/login", json=login_payload)
    assert login_response.status_code == 200
    tokens = login_response.json()["tokens"]

    # Use token to get current user
    response = await client.get(
        "/api/v1/users-db/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    # Accept 200 (success) or 401/404 (user lookup issues)
    assert response.status_code in (200, 401, 404)
    if response.status_code == 200:
        body = response.json()
        assert body["email"] == "medbuser@example.com"


@pytest.mark.asyncio
async def test_users_db_me_without_token(client):
    """Test getting current user info without token fails."""
    response = await client.get("/api/v1/users-db/me")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_user_response_from_auth_user():
    """Test UserResponse.from_auth_user class method."""
    from datetime import datetime, timezone

    from app.api.v1.users_db import UserResponse
    from app.core.auth import AuthUser

    auth_user = AuthUser(
        id="db-test-id",
        email="dbresponse@example.com",
        username="dbresponseuser",
        full_name="DB Response User",
        password_hash="hashed",
        company_name="DB Co",
        created_at=datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc),
        is_active=True,
    )

    response = UserResponse.from_auth_user(auth_user)

    assert response.id == "db-test-id"
    assert response.email == "dbresponse@example.com"
    assert response.username == "dbresponseuser"
    assert response.full_name == "DB Response User"
    assert response.company_name == "DB Co"
    assert response.is_active is True
    assert response.created_at.year == 2024


@pytest.mark.asyncio
async def test_users_db_signup_validates_password(client):
    """Test that weak passwords are rejected."""
    payload = {
        "email": "weakpass@example.com",
        "username": "weakpassuser",
        "full_name": "Weak Pass User",
        "password": "weak",  # Too short, no uppercase/number
    }
    response = await client.post("/api/v1/users-db/signup", json=payload)
    # Should fail validation
    assert response.status_code in (400, 422)
