"""v1 API router — aggregates all v1 endpoint sub-routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import health

router = APIRouter(prefix="/v1")
router.include_router(health.router)
