"""v1 API router — aggregates all v1 endpoint sub-routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    comparisons,
    events,
    health,
    root_causes,
    runtime,
    traces,
)

router = APIRouter(prefix="/v1")
router.include_router(health.router)
router.include_router(traces.router)
router.include_router(events.router)
router.include_router(runtime.router)
router.include_router(comparisons.router)
router.include_router(root_causes.router)
