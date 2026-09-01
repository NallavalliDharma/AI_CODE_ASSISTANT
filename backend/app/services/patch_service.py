"""Patch parsing and management."""

import re

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.pull_request import Patch
from app.schemas.repository import PatchCreate
from app.services.repository_service import get_repository


def parse_unified_diff(content: str) -> list[dict]:
    """Parse a unified diff into structured hunks."""
    files: list[dict] = []
    current_file: dict | None = None
    current_hunk: dict | None = None

    for line in content.splitlines():
        if line.startswith("diff --git"):
            if current_file:
                if current_hunk:
                    current_file["hunks"].append(current_hunk)
                files.append(current_file)
            match = re.search(r"b/(.+)$", line)
            current_file = {"filename": match.group(1) if match else "unknown", "hunks": []}
            current_hunk = None
        elif line.startswith("@@"):
            if current_file:
                if current_hunk:
                    current_file["hunks"].append(current_hunk)
                current_hunk = {"header": line, "lines": []}
        elif current_hunk is not None:
            current_hunk["lines"].append(line)

    if current_file:
        if current_hunk:
            current_file["hunks"].append(current_hunk)
        files.append(current_file)

    return files


def create_patch(db: Session, repo_id: int, data: PatchCreate, user_id: int | None = None) -> Patch:
    get_repository(db, repo_id)
    patch = Patch(
        repository_id=repo_id,
        title=data.title,
        description=data.description,
        file_path=data.file_path,
        content=data.content,
        created_by=user_id,
    )
    db.add(patch)
    db.commit()
    db.refresh(patch)
    return patch


def get_patch(db: Session, patch_id: int) -> Patch:
    patch = db.query(Patch).filter(Patch.id == patch_id).first()
    if not patch:
        raise NotFoundError("Patch not found")
    return patch


def list_patches(db: Session, repo_id: int) -> list[Patch]:
    return db.query(Patch).filter(Patch.repository_id == repo_id).order_by(Patch.created_at.desc()).all()
