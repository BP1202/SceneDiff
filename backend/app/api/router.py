"""Top-level API router.

Mounts all versioned sub-routers under /api.
Adding a new API version means including a new sub-router here only.
"""

from fastapi import APIRouter

from app.api.v1 import router as v1_router

router = APIRouter(prefix="/api")
router.include_router(v1_router.router)
