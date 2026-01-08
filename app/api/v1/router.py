"""
API router aggregator for v1 endpoints.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import health, jobs

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])