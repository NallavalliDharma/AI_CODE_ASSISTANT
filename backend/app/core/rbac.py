"""Role-based access control helpers."""

from app.core.exceptions import ForbiddenError
from app.models.user import User, UserRole

ROLE_HIERARCHY: dict[UserRole, int] = {
    UserRole.USER: 1,
    UserRole.MANAGER: 2,
    UserRole.STAFF: 3,
    UserRole.ADMIN: 4,
}


def has_min_role(user: User, min_role: UserRole) -> bool:
    return ROLE_HIERARCHY.get(user.role, 0) >= ROLE_HIERARCHY.get(min_role, 0)


def require_role(user: User, min_role: UserRole) -> None:
    if not has_min_role(user, min_role):
        raise ForbiddenError(f"Requires {min_role.value} role or higher")


def can_manage_users(user: User) -> bool:
    return has_min_role(user, UserRole.ADMIN)


def can_manage_teams(user: User) -> bool:
    return has_min_role(user, UserRole.MANAGER)
