"""Pytest configuration and shared fixtures."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("APP_DEBUG", "true")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://cra_user:cra_password@localhost:5432/code_review_assistant",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("APP_SECRET_KEY", "test-secret-key-minimum-32-characters-long")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-minimum-32-chars")


@pytest.fixture
def client() -> TestClient:
    from app.main import app
    return TestClient(app)


@pytest.fixture
def db_session():
    """In-memory SQLite session for unit tests."""
    from app.db.session import Base

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    """Register a user and return auth headers."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "testuser@example.com",
            "username": "testuser",
            "password": "testpass123",
            "full_name": "Test User",
        },
    )
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@example.com", "password": "testpass123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client: TestClient, db_session) -> dict[str, str]:
    """Create admin user and return auth headers."""
    from app.core.security import hash_password
    from app.db.session import get_db
    from app.main import app
    from app.models.user import User, UserRole

    admin = User(
        email="admin@test.com",
        username="admintest",
        hashed_password=hash_password("adminpass123"),
        role=UserRole.ADMIN,
    )
    db_session.add(admin)
    db_session.commit()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "adminpass123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
