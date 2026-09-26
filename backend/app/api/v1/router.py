"""v1 API router — aggregates all v1 endpoint sub-routers."""
from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")
