"""Health endpoint tests."""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data


def test_liveness(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "Code Review Assistant"
    assert data["environment"] == "development"
    assert data["version"] == "0.1.0"


def test_readiness_returns_structured_response(client: TestClient) -> None:
    """Readiness may be 200 or 503 depending on DB/Redis availability."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "redis" in data
    assert data["database"]["status"] in ("ok", "error")
    assert data["redis"]["status"] in ("ok", "error")
