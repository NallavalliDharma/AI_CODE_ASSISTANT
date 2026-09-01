"""Team management service."""

from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ConflictError, NotFoundError
from app.models.team import Team, TeamMember, TeamMemberRole
from app.models.user import User
from app.schemas.team import TeamCreate, TeamMemberAdd, TeamUpdate


def list_teams(db: Session) -> list[Team]:
    return (
        db.query(Team)
        .options(joinedload(Team.members).joinedload(TeamMember.user))
        .order_by(Team.name)
        .all()
    )


def get_team(db: Session, team_id: int) -> Team:
    team = (
        db.query(Team)
        .options(joinedload(Team.members).joinedload(TeamMember.user))
        .filter(Team.id == team_id)
        .first()
    )
    if not team:
        raise NotFoundError("Team not found")
    return team


def create_team(db: Session, data: TeamCreate, owner: User) -> Team:
    if db.query(Team).filter(Team.name == data.name).first():
        raise ConflictError("Team name already exists")
    team = Team(name=data.name, description=data.description)
    db.add(team)
    db.flush()
    member = TeamMember(team_id=team.id, user_id=owner.id, role=TeamMemberRole.OWNER)
    db.add(member)
    db.commit()
    db.refresh(team)
    return get_team(db, team.id)


def update_team(db: Session, team_id: int, data: TeamUpdate) -> Team:
    team = get_team(db, team_id)
    if data.name is not None:
        existing = db.query(Team).filter(Team.name == data.name, Team.id != team_id).first()
        if existing:
            raise ConflictError("Team name already exists")
        team.name = data.name
    if data.description is not None:
        team.description = data.description
    db.commit()
    return get_team(db, team_id)


def delete_team(db: Session, team_id: int) -> None:
    team = get_team(db, team_id)
    db.delete(team)
    db.commit()


def add_team_member(db: Session, team_id: int, data: TeamMemberAdd) -> TeamMember:
    get_team(db, team_id)
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise NotFoundError("User not found")
    existing = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == data.user_id)
        .first()
    )
    if existing:
        raise ConflictError("User is already a team member")
    member = TeamMember(team_id=team_id, user_id=data.user_id, role=data.role)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def remove_team_member(db: Session, team_id: int, user_id: int) -> None:
    member = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        .first()
    )
    if not member:
        raise NotFoundError("Team member not found")
    db.delete(member)
    db.commit()
