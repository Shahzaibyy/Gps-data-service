"""
Health check endpoints.
"""
from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "GPS Data Collection Service",
        "version": "1.0.0"
    }


@router.get("/liveness")
async def liveness_probe() -> Dict[str, str]:
    """
    Kubernetes liveness probe.
    """
    return {"status": "alive"}


@router.get("/readiness")
async def readiness_probe() -> Dict[str, str]:
    """
    Kubernetes readiness probe.
    """
    return {"status": "ready"}