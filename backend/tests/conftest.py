"""Pytest configuration and shared fixtures."""

import os

import pytest
from fastapi.testclient import TestClient

# Use test-friendly defaults before app import
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
    """Return a FastAPI test client."""
    from app.main import app

    return TestClient(app)
