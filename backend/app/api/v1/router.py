"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.recommendations import router as recommendations_router
from app.api.v1.routes.version import router as version_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(recommendations_router)
api_router.include_router(version_router)