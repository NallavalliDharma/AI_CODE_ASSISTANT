"""Audit log middleware."""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.security import decode_token
from app.db.session import SessionLocal
from app.services.audit_service import log_action

AUDITED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
AUDITED_PREFIXES = ("/api/v1/auth", "/api/v1/users", "/api/v1/teams", "/api/v1/repositories")


class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        if request.method not in AUDITED_METHODS:
            return response
        if not request.url.path.startswith(AUDITED_PREFIXES):
            return response
        if response.status_code >= 400:
            return response

        user_id: int | None = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                payload = decode_token(auth_header[7:])
                user_id = int(payload["sub"])
            except (ValueError, KeyError):
                pass

        ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or (
            request.client.host if request.client else None
        )

        db = SessionLocal()
        try:
            log_action(
                db,
                action=f"{request.method} {request.url.path}",
                user_id=user_id,
                resource_type="api",
                details={"status_code": response.status_code},
                ip_address=ip,
            )
        finally:
            db.close()

        return response
