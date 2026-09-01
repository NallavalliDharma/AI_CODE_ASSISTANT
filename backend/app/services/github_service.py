"""GitHub integration service."""

import secrets
from urllib.parse import urlencode

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.exceptions import AppException, NotFoundError
from app.models.pull_request import PullRequest, PullRequestState
from app.models.repository import GitHubConnection, Repository
from app.services.repository_service import get_repository

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_BASE = "https://api.github.com"

_oauth_states: dict[str, int] = {}


def get_authorize_url(user_id: int) -> str:
    settings = get_settings()
    if not settings.github_client_id:
        raise AppException("GitHub OAuth is not configured", error_code="GITHUB_NOT_CONFIGURED")
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = user_id
    params = urlencode(
        {
            "client_id": settings.github_client_id,
            "redirect_uri": settings.github_callback_url,
            "scope": "repo read:user",
            "state": state,
        }
    )
    return f"{GITHUB_AUTH_URL}?{params}"


def handle_oauth_callback(db: Session, code: str, state: str) -> GitHubConnection:
    settings = get_settings()
    user_id = _oauth_states.pop(state, None)
    if user_id is None:
        raise AppException("Invalid OAuth state", error_code="INVALID_STATE")

    with httpx.Client() as client:
        token_resp = client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_callback_url,
            },
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise AppException("Failed to obtain GitHub access token")

        user_resp = client.get(
            f"{GITHUB_API_BASE}/user",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
        )
        user_resp.raise_for_status()
        gh_user = user_resp.json()

    existing = db.query(GitHubConnection).filter(GitHubConnection.user_id == user_id).first()
    if existing:
        existing.access_token = access_token
        existing.github_username = gh_user["login"]
        existing.github_user_id = gh_user.get("id")
        db.commit()
        db.refresh(existing)
        return existing

    connection = GitHubConnection(
        user_id=user_id,
        access_token=access_token,
        github_username=gh_user["login"],
        github_user_id=gh_user.get("id"),
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)
    return connection


def _get_connection(db: Session, user_id: int) -> GitHubConnection:
    conn = db.query(GitHubConnection).filter(GitHubConnection.user_id == user_id).first()
    if not conn:
        raise NotFoundError("GitHub account not connected")
    return conn


def list_github_repos(db: Session, user_id: int) -> list[dict]:
    conn = _get_connection(db, user_id)
    with httpx.Client() as client:
        resp = client.get(
            f"{GITHUB_API_BASE}/user/repos",
            headers={"Authorization": f"Bearer {conn.access_token}", "Accept": "application/vnd.github+json"},
            params={"per_page": 100, "sort": "updated"},
        )
        resp.raise_for_status()
        return resp.json()


def fetch_branches(db: Session, user_id: int, owner: str, repo: str) -> list[dict]:
    conn = _get_connection(db, user_id)
    with httpx.Client() as client:
        resp = client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/branches",
            headers={"Authorization": f"Bearer {conn.access_token}", "Accept": "application/vnd.github+json"},
        )
        resp.raise_for_status()
        return resp.json()


def sync_pull_requests(db: Session, user_id: int, repo_id: int) -> list[PullRequest]:
    repository = get_repository(db, repo_id)
    if not repository.url:
        raise AppException("Repository has no GitHub URL")
    conn = _get_connection(db, user_id)

    parts = repository.url.rstrip("/").split("/")
    owner, repo_name = parts[-2], parts[-1]

    with httpx.Client() as client:
        resp = client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo_name}/pulls",
            headers={"Authorization": f"Bearer {conn.access_token}", "Accept": "application/vnd.github+json"},
            params={"state": "all", "per_page": 50},
        )
        resp.raise_for_status()
        prs_data = resp.json()

    results = []
    for pr_data in prs_data:
        existing = (
            db.query(PullRequest)
            .filter(PullRequest.repository_id == repo_id, PullRequest.number == pr_data["number"])
            .first()
        )
        state_map = {"open": PullRequestState.OPEN, "closed": PullRequestState.CLOSED}
        state = state_map.get(pr_data["state"], PullRequestState.CLOSED)
        if pr_data.get("merged_at"):
            state = PullRequestState.MERGED

        if existing:
            existing.title = pr_data["title"]
            existing.state = state
            existing.source_branch = pr_data["head"]["ref"]
            existing.target_branch = pr_data["base"]["ref"]
            existing.author = pr_data["user"]["login"]
            existing.diff_url = pr_data["url"]
            existing.github_id = pr_data["id"]
            results.append(existing)
        else:
            pr = PullRequest(
                repository_id=repo_id,
                number=pr_data["number"],
                title=pr_data["title"],
                state=state,
                source_branch=pr_data["head"]["ref"],
                target_branch=pr_data["base"]["ref"],
                author=pr_data["user"]["login"],
                diff_url=pr_data["url"],
                github_id=pr_data["id"],
            )
            db.add(pr)
            results.append(pr)

    db.commit()
    for pr in results:
        db.refresh(pr)
    return results


def fetch_pr_diff(db: Session, user_id: int, repo_id: int, pr_number: int) -> str:
    repository = get_repository(db, repo_id)
    conn = _get_connection(db, user_id)
    parts = repository.url.rstrip("/").split("/")
    owner, repo_name = parts[-2], parts[-1]

    with httpx.Client() as client:
        resp = client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo_name}/pulls/{pr_number}",
            headers={
                "Authorization": f"Bearer {conn.access_token}",
                "Accept": "application/vnd.github.v3.diff",
            },
        )
        resp.raise_for_status()
        diff_content = resp.text

    pr = (
        db.query(PullRequest)
        .filter(PullRequest.repository_id == repo_id, PullRequest.number == pr_number)
        .first()
    )
    if pr:
        pr.diff_content = diff_content
        db.commit()

    return diff_content
