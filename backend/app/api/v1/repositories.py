"""Repository management API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db_session
from app.models.user import User
from app.schemas.repository import (
    PatchCreate,
    PatchResponse,
    PullRequestResponse,
    RepositoryCreate,
    RepositoryResponse,
    RepositoryUpdate,
)
from app.services import github_service, patch_service, repository_service

router = APIRouter(prefix="/repositories", tags=["Repositories"])


@router.get("", response_model=list[RepositoryResponse])
def list_repositories(
    db: Annotated[Session, Depends(get_db_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    return repository_service.list_repositories(db, user_id=user.id)


@router.get("/{repo_id}", response_model=RepositoryResponse)
def get_repository(
    repo_id: int,
    db: Annotated[Session, Depends(get_db_session)],
    _user: Annotated[User, Depends(get_current_user)],
):
    return repository_service.get_repository(db, repo_id)


@router.post("", response_model=RepositoryResponse, status_code=201)
def create_repository(
    data: RepositoryCreate,
    db: Annotated[Session, Depends(get_db_session)],
    _user: Annotated[User, Depends(get_current_user)],
):
    return repository_service.create_repository(db, data)


@router.patch("/{repo_id}", response_model=RepositoryResponse)
def update_repository(
    repo_id: int,
    data: RepositoryUpdate,
    db: Annotated[Session, Depends(get_db_session)],
    _user: Annotated[User, Depends(get_current_user)],
):
    return repository_service.update_repository(db, repo_id, data)


@router.delete("/{repo_id}", status_code=204)
def delete_repository(
    repo_id: int,
    db: Annotated[Session, Depends(get_db_session)],
    _user: Annotated[User, Depends(get_current_user)],
):
    repository_service.delete_repository(db, repo_id)


@router.get("/{repo_id}/pull-requests", response_model=list[PullRequestResponse])
def list_pull_requests(
    repo_id: int,
    db: Annotated[Session, Depends(get_db_session)],
    _user: Annotated[User, Depends(get_current_user)],
):
    from app.models.pull_request import PullRequest
    return (
        db.query(PullRequest)
        .filter(PullRequest.repository_id == repo_id)
        .order_by(PullRequest.number.desc())
        .all()
    )


@router.post("/{repo_id}/pull-requests/sync", response_model=list[PullRequestResponse])
def sync_pull_requests(
    repo_id: int,
    db: Annotated[Session, Depends(get_db_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    return github_service.sync_pull_requests(db, user.id, repo_id)


@router.get("/{repo_id}/pull-requests/{pr_number}/diff")
def get_pr_diff(
    repo_id: int,
    pr_number: int,
    db: Annotated[Session, Depends(get_db_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    diff = github_service.fetch_pr_diff(db, user.id, repo_id, pr_number)
    return {"diff": diff}


@router.get("/{repo_id}/patches", response_model=list[PatchResponse])
def list_patches(
    repo_id: int,
    db: Annotated[Session, Depends(get_db_session)],
    _user: Annotated[User, Depends(get_current_user)],
):
    return patch_service.list_patches(db, repo_id)


@router.post("/{repo_id}/patches", response_model=PatchResponse, status_code=201)
def upload_patch(
    repo_id: int,
    data: PatchCreate,
    db: Annotated[Session, Depends(get_db_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    return patch_service.create_patch(db, repo_id, data, user_id=user.id)


@router.get("/{repo_id}/patches/{patch_id}/parsed")
def parse_patch(
    repo_id: int,
    patch_id: int,
    db: Annotated[Session, Depends(get_db_session)],
    _user: Annotated[User, Depends(get_current_user)],
):
    patch = patch_service.get_patch(db, patch_id)
    files = patch_service.parse_unified_diff(patch.content)
    return {"files": files, "file_count": len(files)}
