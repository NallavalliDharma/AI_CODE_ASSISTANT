"""Placeholder Celery tasks — expanded in later phases."""

from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.ping")
def ping() -> dict[str, str]:
    """Simple health-check task for verifying worker connectivity."""
    return {"status": "pong"}
