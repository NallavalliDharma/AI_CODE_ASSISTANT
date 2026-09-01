"""Repository management service."""

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.repository import Repository, RepositoryProvider
from app.models.team import TeamMember
from app.schemas.repository import GitHubRepoImport, RepositoryCreate, RepositoryUpdate


def _user_in_team(db: Session, user_id: int, team_id: int) -> bool:
    return (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        .first()
        is not None
    )


def list_repositories(db: Session, user_id: int | None = None) -> list[Repository]:
    query = db.query(Repository).order_by(Repository.name)
    if user_id is not None:
        team_ids = [
            m.team_id
            for m in db.query(TeamMember).filter(TeamMember.user_id == user_id).all()
        ]
        query = query.filter(Repository.team_id.in_(team_ids))
    return query.all()


def get_repository(db: Session, repo_id: int) -> Repository:
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise NotFoundError("Repository not found")
    return repo


def create_repository(db: Session, data: RepositoryCreate) -> Repository:
    repo = Repository(
        team_id=data.team_id,
        name=data.name,
        url=data.url,
        provider=data.provider,
        default_branch=data.default_branch,
        description=data.description,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo


def import_github_repository(db: Session, data: GitHubRepoImport) -> Repository:
    existing = (
        db.query(Repository)
        .filter(Repository.github_repo_id == data.github_repo_id)
        .first()
    )
    if existing:
        return existing
    repo = Repository(
        team_id=data.team_id,
        name=data.name,
        url=data.url,
        provider=RepositoryProvider.GITHUB,
        github_repo_id=data.github_repo_id,
        default_branch=data.default_branch,
        description=data.description,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo


def update_repository(db: Session, repo_id: int, data: RepositoryUpdate) -> Repository:
    repo = get_repository(db, repo_id)
    if data.name is not None:
        repo.name = data.name
    if data.url is not None:
        repo.url = data.url
    if data.default_branch is not None:
        repo.default_branch = data.default_branch
    if data.description is not None:
        repo.description = data.description
    db.commit()
    db.refresh(repo)
    return repo


def delete_repository(db: Session, repo_id: int) -> None:
    repo = get_repository(db, repo_id)
    db.delete(repo)
    db.commit()
