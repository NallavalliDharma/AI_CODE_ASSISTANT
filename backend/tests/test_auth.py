"""Authentication endpoint tests."""

from fastapi.testclient import TestClient


def test_register(client: TestClient):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "securepass123",
            "full_name": "New User",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert "hashed_password" not in data


def test_register_duplicate_email(client: TestClient):
    payload = {
        "email": "dup@example.com",
        "username": "user1",
        "password": "securepass123",
    }
    client.post("/api/v1/auth/register", json=payload)
    resp = client.post(
        "/api/v1/auth/register",
        json={**payload, "username": "user2"},
    )
    assert resp.status_code == 409


def test_login(client: TestClient):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "username": "loginuser",
            "password": "securepass123",
        },
    )
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "securepass123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client: TestClient):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "wrongpass"},
    )
    assert resp.status_code == 401


def test_me(client: TestClient, auth_headers: dict):
    resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "testuser"


def test_refresh_token(client: TestClient):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh@example.com",
            "username": "refreshuser",
            "password": "securepass123",
        },
    )
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "securepass123"},
    )
    refresh_token = login_resp.json()["refresh_token"]
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_logout(client: TestClient, auth_headers: dict):
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@example.com", "password": "testpass123"},
    )
    refresh_token = login_resp.json()["refresh_token"]
    resp = client.post(
        "/api/v1/auth/logout",
        headers=auth_headers,
        json={"refresh_token": refresh_token},
    )
    assert resp.status_code == 204
