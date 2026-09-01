"""Authentication service."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token_value,
    get_refresh_token_expiry,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.auth import RefreshToken
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserCreate


def register_user(db: Session, data: RegisterRequest) -> User:
    if db.query(User).filter(User.email == data.email).first():
        raise ConflictError("Email already registered")
    if db.query(User).filter(User.username == data.username).first():
        raise ConflictError("Username already taken")

    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=UserRole.USER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_user(db: Session, data: UserCreate) -> User:
    if db.query(User).filter(User.email == data.email).first():
        raise ConflictError("Email already registered")
    if db.query(User).filter(User.username == data.username).first():
        raise ConflictError("Username already taken")

    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, data: LoginRequest) -> User:
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise UnauthorizedError("Invalid email or password")
    if not user.is_active:
        raise UnauthorizedError("Account is deactivated")
    return user


def issue_tokens(db: Session, user: User) -> TokenResponse:
    access_token = create_access_token(user.id, {"role": user.role.value})
    refresh_value = create_refresh_token_value()
    refresh = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_value),
        expires_at=get_refresh_token_expiry(),
    )
    db.add(refresh)
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh_value)


def refresh_access_token(db: Session, refresh_token: str) -> TokenResponse:
    token_hash = hash_token(refresh_token)
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if not stored or stored.revoked_at is not None:
        raise UnauthorizedError("Invalid refresh token")
    expires = stored.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    if expires < datetime.now(UTC):
        raise UnauthorizedError("Refresh token expired")

    user = db.query(User).filter(User.id == stored.user_id).first()
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")

    stored.revoked_at = datetime.now(UTC)
    db.commit()
    return issue_tokens(db, user)


def logout_user(db: Session, refresh_token: str) -> None:
    token_hash = hash_token(refresh_token)
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if stored and stored.revoked_at is None:
        stored.revoked_at = datetime.now(UTC)
        db.commit()
