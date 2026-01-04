"""Health check router."""

import os
from pathlib import Path

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter()


def check_storage_health() -> dict:
    """Check storage availability."""
    campaigns_dir = Path(os.getenv("CAMPAIGNS_DIR", "/data/campaigns"))
    rules_dir = Path(os.getenv("RULES_DIR", "/data/rules"))

    checks = {
        "campaigns": {
            "exists": campaigns_dir.exists(),
            "writable": campaigns_dir.exists() and os.access(campaigns_dir, os.W_OK),
        },
        "rules": {
            "exists": rules_dir.exists(),
            "writable": rules_dir.exists() and os.access(rules_dir, os.W_OK),
        },
    }
    return checks


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    storage_health = check_storage_health()
    all_healthy = (
        storage_health["campaigns"]["exists"]
        and storage_health["campaigns"]["writable"]
        and storage_health["rules"]["exists"]
        and storage_health["rules"]["writable"]
    )

    response_data = {
        "status": "healthy" if all_healthy else "degraded",
        "service": "gm-chatbot",
        "storage": storage_health,
    }

    if not all_healthy:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response_data,
        )

    return response_data


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    storage_health = check_storage_health()
    is_ready = (
        storage_health["campaigns"]["exists"]
        and storage_health["campaigns"]["writable"]
        and storage_health["rules"]["exists"]
        and storage_health["rules"]["writable"]
    )

    response_data = {
        "status": "ready" if is_ready else "not_ready",
        "service": "gm-chatbot",
        "storage": storage_health,
    }

    if not is_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response_data,
        )

    return response_data
