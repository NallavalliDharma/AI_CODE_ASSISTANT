"""Health check API endpoints."""

import redis
from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field

from app.config import get_settings
from app.db.session import check_database_connection

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    """Liveness check response."""

    status: str = Field(examples=["ok"])
    service: str = Field(examples=["Code Review Assistant"])
    environment: str = Field(examples=["development"])
    version: str = Field(examples=["0.1.0"])


class ComponentHealth(BaseModel):
    """Individual component health status."""

    status: str = Field(examples=["ok", "error"])
    message: str = Field(examples=["Connection successful"])


class ReadinessResponse(BaseModel):
    """Readiness check response with dependency status."""

    status: str = Field(examples=["ready", "not_ready"])
    database: ComponentHealth
    redis: ComponentHealth


def _check_redis_connection() -> tuple[bool, str]:
    """Verify Redis connectivity."""
    settings = get_settings()
    try:
        client = redis.from_url(settings.redis_url, socket_connect_timeout=3)
        client.ping()
        return True, "Redis connection successful"
    except Exception as exc:
        return False, f"Redis connection failed: {exc}"


@router.get(
    "",
    response_model=HealthResponse,
    summary="Liveness check",
    description="Returns basic service health. Used by load balancers and orchestrators.",
)
async def liveness() -> HealthResponse:
    """Return liveness status — does not check external dependencies."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
        version="0.1.0",
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness check",
    description="Verifies database and Redis connectivity before accepting traffic.",
    responses={
        status.HTTP_200_OK: {"description": "All dependencies healthy"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "One or more dependencies unavailable"
        },
    },
)
async def readiness(http_response: Response) -> ReadinessResponse:
    """Return readiness status including dependency health checks."""
    db_ok, db_msg = check_database_connection()
    redis_ok, redis_msg = _check_redis_connection()

    all_ready = db_ok and redis_ok

    if not all_ready:
        http_response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status="ready" if all_ready else "not_ready",
        database=ComponentHealth(
            status="ok" if db_ok else "error",
            message=db_msg,
        ),
        redis=ComponentHealth(
            status="ok" if redis_ok else "error",
            message=redis_msg,
        ),
    )
