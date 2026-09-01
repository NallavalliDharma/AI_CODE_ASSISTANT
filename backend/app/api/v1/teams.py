"""Team management API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db_session, require_manager
from app.models.user import User
from app.schemas.team import (
    TeamCreate,
    TeamMemberAdd,
    TeamMemberResponse,
    TeamResponse,
    TeamUpdate,
)
from app.services import team_service

router = APIRouter(prefix="/teams", tags=["Teams"])


def _team_to_response(team) -> TeamResponse:
    members = []
    for m in team.members:
        members.append(
            TeamMemberResponse(
                id=m.id,
                user_id=m.user_id,
                role=m.role,
                joined_at=m.joined_at,
                username=m.user.username if m.user else None,
                email=m.user.email if m.user else None,
            )
        )
    return TeamResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        created_at=team.created_at,
        updated_at=team.updated_at,
        members=members,
    )


@router.get("", response_model=list[TeamResponse])
def list_teams(
    db: Annotated[Session, Depends(get_db_session)],
    _user: Annotated[User, Depends(get_current_user)],
):
    return [_team_to_response(t) for t in team_service.list_teams(db)]


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: int,
    db: Annotated[Session, Depends(get_db_session)],
    _user: Annotated[User, Depends(get_current_user)],
):
    return _team_to_response(team_service.get_team(db, team_id))


@router.post("", response_model=TeamResponse, status_code=201)
def create_team(
    data: TeamCreate,
    db: Annotated[Session, Depends(get_db_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    return _team_to_response(team_service.create_team(db, data, user))


@router.patch("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: int,
    data: TeamUpdate,
    db: Annotated[Session, Depends(get_db_session)],
    _manager: Annotated[User, Depends(require_manager)],
):
    return _team_to_response(team_service.update_team(db, team_id, data))


@router.delete("/{team_id}", status_code=204)
def delete_team(
    team_id: int,
    db: Annotated[Session, Depends(get_db_session)],
    _manager: Annotated[User, Depends(require_manager)],
):
    team_service.delete_team(db, team_id)


@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=201)
def add_member(
    team_id: int,
    data: TeamMemberAdd,
    db: Annotated[Session, Depends(get_db_session)],
    _manager: Annotated[User, Depends(require_manager)],
):
    member = team_service.add_team_member(db, team_id, data)
    return TeamMemberResponse(
        id=member.id,
        user_id=member.user_id,
        role=member.role,
        joined_at=member.joined_at,
    )


@router.delete("/{team_id}/members/{user_id}", status_code=204)
def remove_member(
    team_id: int,
    user_id: int,
    db: Annotated[Session, Depends(get_db_session)],
    _manager: Annotated[User, Depends(require_manager)],
):
    team_service.remove_team_member(db, team_id, user_id)
