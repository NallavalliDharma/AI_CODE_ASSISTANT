"""User management API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user, get_db_session, require_admin
from app.models.user import User
from app.schemas.auth import UserCreate, UserResponse, UserUpdate
from app.services import auth_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserResponse])
def list_users(
    db: Annotated[Session, Depends(get_db_session)],
    _admin: Annotated[User, Depends(require_admin)],
):
    return db.query(User).order_by(User.username).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db_session)],
    current: Annotated[User, Depends(get_current_user)],
):
    if current.id != user_id and current.role.value != "admin":
        from app.core.rbac import require_role
        from app.models.user import UserRole
        require_role(current, UserRole.ADMIN)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User not found")
    return user


@router.post("", response_model=UserResponse, status_code=201)
def create_user(
    data: UserCreate,
    db: Annotated[Session, Depends(get_db_session)],
    _admin: Annotated[User, Depends(require_admin)],
):
    return auth_service.create_user(db, data)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Annotated[Session, Depends(get_db_session)],
    _admin: Annotated[User, Depends(require_admin)],
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User not found")
    if data.email is not None:
        user.email = data.email
    if data.username is not None:
        user.username = data.username
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db_session)],
    admin: Annotated[User, Depends(require_admin)],
):
    if admin.id == user_id:
        from app.core.exceptions import AppException
        raise AppException("Cannot delete your own account")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User not found")
    db.delete(user)
    db.commit()
