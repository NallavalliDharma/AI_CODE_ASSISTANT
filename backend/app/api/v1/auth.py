"""Authentication API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.dependencies import get_client_ip, get_current_user, get_db_session
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services import auth_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(
    data: RegisterRequest,
    db: Annotated[Session, Depends(get_db_session)],
    request: Request,
):
    user = auth_service.register_user(db, data)
    log_action(db, "user.register", user_id=user.id, resource_type="user", resource_id=user.id,
               ip_address=get_client_ip(request))
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    db: Annotated[Session, Depends(get_db_session)],
    request: Request,
):
    user = auth_service.authenticate_user(db, data)
    tokens = auth_service.issue_tokens(db, user)
    log_action(db, "user.login", user_id=user.id, resource_type="user", resource_id=user.id,
               ip_address=get_client_ip(request))
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db: Annotated[Session, Depends(get_db_session)]):
    return auth_service.refresh_access_token(db, data.refresh_token)


@router.post("/logout", status_code=204)
def logout(
    data: RefreshRequest,
    db: Annotated[Session, Depends(get_db_session)],
    user: Annotated[User, Depends(get_current_user)],
    request: Request,
):
    auth_service.logout_user(db, data.refresh_token)
    log_action(db, "user.logout", user_id=user.id, resource_type="user", resource_id=user.id,
               ip_address=get_client_ip(request))


@router.get("/me", response_model=UserResponse)
def me(user: Annotated[User, Depends(get_current_user)]):
    return user
