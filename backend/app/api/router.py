"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import analysis, auth, health, repositories, teams, users
from app.api.v1.integrations import github

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(teams.router)
api_v1_router.include_router(repositories.router)
api_v1_router.include_router(github.router)
api_v1_router.include_router(analysis.router)
