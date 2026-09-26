"""SceneDiff FastAPI application entry point.

Responsibilities:
- Create the FastAPI application instance.
- Register routers.
- Attach middleware.

No business logic lives here.
"""
from fastapi import FastAPI

app = FastAPI(
    title="SceneDiff",
    version="0.1.0",
    description="AI-powered runtime behavior diff platform.",
)
