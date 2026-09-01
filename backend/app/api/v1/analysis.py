"""Static analysis API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db_session
from app.models.user import User
from app.schemas.analysis import AnalysisRunCreate, AnalysisRunResponse, FindingResponse, TestResultResponse
from app.services import analysis_service
from app.workers.analysis_tasks import run_static_analysis

router = APIRouter(tags=["Analysis"])


def _run_to_response(run) -> AnalysisRunResponse:
    test_results = []
    for tr in run.test_results:
        test_results.append(
            TestResultResponse(
                id=tr.id,
                tool_name=tr.tool_name,
                tool_type=tr.tool_type,
                status=tr.status,
                issue_count=tr.issue_count,
                created_at=tr.created_at,
                findings=[FindingResponse.model_validate(f) for f in tr.findings],
            )
        )
    return AnalysisRunResponse(
        id=run.id,
        repository_id=run.repository_id,
        pull_request_id=run.pull_request_id,
        patch_id=run.patch_id,
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        error_message=run.error_message,
        created_at=run.created_at,
        test_results=test_results,
        findings=[FindingResponse.model_validate(f) for f in run.findings],
    )


@router.get("/repositories/{repo_id}/analysis", response_model=list[AnalysisRunResponse])
def list_analysis_runs(
    repo_id: int,
    db: Annotated[Session, Depends(get_db_session)],
    _user: Annotated[User, Depends(get_current_user)],
):
    runs = analysis_service.list_analysis_runs(db, repo_id)
    return [_run_to_response(r) for r in runs]


@router.post("/repositories/{repo_id}/analysis", response_model=AnalysisRunResponse, status_code=202)
def trigger_analysis(
    repo_id: int,
    data: AnalysisRunCreate,
    db: Annotated[Session, Depends(get_db_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    run = analysis_service.create_analysis_run(
        db,
        repo_id,
        user_id=user.id,
        pull_request_id=data.pull_request_id,
        patch_id=data.patch_id,
    )
    run_static_analysis.delay(run.id)
    return _run_to_response(run)


@router.get("/analysis/{run_id}", response_model=AnalysisRunResponse)
def get_analysis_run(
    run_id: int,
    db: Annotated[Session, Depends(get_db_session)],
    _user: Annotated[User, Depends(get_current_user)],
):
    run = analysis_service.get_analysis_run(db, run_id)
    return _run_to_response(run)
