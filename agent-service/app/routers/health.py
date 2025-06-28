import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "Agent Service",
            "version": "1.0.0",
            "port": settings.port
        }
    )


@router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {
        "status": "pong",
        "message": "Agent Service is running",
        "port": settings.port
    }


@router.get("/status")
async def status():
    """Detailed status endpoint"""
    return {
        "service": "Agent Service",
        "status": "running",
        "configuration": {
            "port": settings.port,
            "debug": settings.debug,
            "log_level": settings.log_level,
            "available_roles": settings.available_roles,
            "default_role": settings.default_role,
            "max_concurrent_jobs": settings.max_concurrent_jobs,
            "job_timeout": settings.job_timeout,
            "claude_cli_path": settings.claude_cli_path
        },
        "timestamp": datetime.utcnow().isoformat()
    }