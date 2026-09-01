"""Static analysis orchestration service."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError
from app.models.analysis import AnalysisRun, AnalysisStatus, Finding, TestResult
from app.services.repository_service import get_repository


def create_analysis_run(
    db: Session,
    repo_id: int,
    user_id: int | None = None,
    pull_request_id: int | None = None,
    patch_id: int | None = None,
) -> AnalysisRun:
    get_repository(db, repo_id)
    run = AnalysisRun(
        repository_id=repo_id,
        pull_request_id=pull_request_id,
        patch_id=patch_id,
        triggered_by=user_id,
        status=AnalysisStatus.PENDING,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_analysis_run(db: Session, run_id: int) -> AnalysisRun:
    run = (
        db.query(AnalysisRun)
        .options(
            joinedload(AnalysisRun.test_results).joinedload(TestResult.findings),
            joinedload(AnalysisRun.findings),
        )
        .filter(AnalysisRun.id == run_id)
        .first()
    )
    if not run:
        raise NotFoundError("Analysis run not found")
    return run


def list_analysis_runs(db: Session, repo_id: int) -> list[AnalysisRun]:
    return (
        db.query(AnalysisRun)
        .filter(AnalysisRun.repository_id == repo_id)
        .order_by(AnalysisRun.created_at.desc())
        .all()
    )


def mark_running(db: Session, run_id: int) -> AnalysisRun:
    run = get_analysis_run(db, run_id)
    run.status = AnalysisStatus.RUNNING
    run.started_at = datetime.now(UTC)
    db.commit()
    db.refresh(run)
    return run


def mark_completed(db: Session, run_id: int) -> AnalysisRun:
    run = get_analysis_run(db, run_id)
    run.status = AnalysisStatus.COMPLETED
    run.completed_at = datetime.now(UTC)
    db.commit()
    db.refresh(run)
    return run


def mark_failed(db: Session, run_id: int, error: str) -> AnalysisRun:
    run = get_analysis_run(db, run_id)
    run.status = AnalysisStatus.FAILED
    run.error_message = error
    run.completed_at = datetime.now(UTC)
    db.commit()
    db.refresh(run)
    return run
