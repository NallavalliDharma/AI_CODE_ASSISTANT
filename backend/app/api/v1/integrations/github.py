"""GitHub integration API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.dependencies import get_current_user, get_db_session
from app.models.user import User
from app.schemas.repository import GitHubRepoImport, RepositoryResponse
from app.services import github_service, repository_service

router = APIRouter(prefix="/integrations/github", tags=["GitHub Integration"])


@router.get("/authorize")
def authorize(user: Annotated[User, Depends(get_current_user)]):
    url = github_service.get_authorize_url(user.id)
    return {"authorize_url": url}


@router.get("/callback")
def callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Annotated[Session, Depends(get_db_session)] = ...,
):
    github_service.handle_oauth_callback(db, code, state)
    settings = get_settings()
    return RedirectResponse(url=f"{settings.frontend_url}/repositories?github=connected")


@router.get("/repos")
def list_repos(
    db: Annotated[Session, Depends(get_db_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    repos = github_service.list_github_repos(db, user.id)
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "full_name": r["full_name"],
            "url": r["html_url"],
            "default_branch": r.get("default_branch", "main"),
            "description": r.get("description"),
            "private": r.get("private", False),
        }
        for r in repos
    ]


@router.get("/repos/{owner}/{repo}/branches")
def list_branches(
    owner: str,
    repo: str,
    db: Annotated[Session, Depends(get_db_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    branches = github_service.fetch_branches(db, user.id, owner, repo)
    return [{"name": b["name"], "sha": b["commit"]["sha"]} for b in branches]


@router.post("/import", response_model=RepositoryResponse, status_code=201)
def import_repo(
    data: GitHubRepoImport,
    db: Annotated[Session, Depends(get_db_session)],
    _user: Annotated[User, Depends(get_current_user)],
):
    return repository_service.import_github_repository(db, data)
