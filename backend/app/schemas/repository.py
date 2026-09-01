"""Repository and pull request schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.pull_request import PullRequestState
from app.models.repository import RepositoryProvider


class RepositoryCreate(BaseModel):
    team_id: int
    name: str = Field(min_length=1, max_length=255)
    url: str | None = None
    provider: RepositoryProvider = RepositoryProvider.MANUAL
    default_branch: str = "main"
    description: str | None = None


class RepositoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    url: str | None = None
    default_branch: str | None = None
    description: str | None = None


class RepositoryResponse(BaseModel):
    id: int
    team_id: int
    name: str
    url: str | None
    provider: RepositoryProvider
    github_repo_id: int | None
    default_branch: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PullRequestResponse(BaseModel):
    id: int
    repository_id: int
    number: int
    title: str
    state: PullRequestState
    source_branch: str
    target_branch: str
    author: str | None
    diff_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PatchCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    file_path: str | None = None
    content: str = Field(min_length=1)


class PatchResponse(BaseModel):
    id: int
    repository_id: int
    title: str
    description: str | None
    file_path: str | None
    created_by: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class GitHubRepoImport(BaseModel):
    team_id: int
    github_repo_id: int
    name: str
    url: str
    default_branch: str = "main"
    description: str | None = None
