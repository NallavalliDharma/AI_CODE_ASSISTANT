"""Team schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.team import TeamMemberRole


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class TeamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class TeamMemberAdd(BaseModel):
    user_id: int
    role: TeamMemberRole = TeamMemberRole.MEMBER


class TeamMemberResponse(BaseModel):
    id: int
    user_id: int
    role: TeamMemberRole
    joined_at: datetime
    username: str | None = None
    email: str | None = None

    model_config = {"from_attributes": True}


class TeamResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    members: list[TeamMemberResponse] = []

    model_config = {"from_attributes": True}
