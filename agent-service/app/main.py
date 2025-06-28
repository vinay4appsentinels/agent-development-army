import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings
from app.routers import jobs, health

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Agent Service")
    logger.info(f"Service running on port {settings.port}")
    logger.info(f"Available roles: {', '.join(settings.available_roles)}")
    yield
    logger.info("Shutting down Agent Service")


app = FastAPI(
    title="Agent Service",
    description="Role-based AI agent service using Claude CLI",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(jobs.router, prefix="/agent", tags=["agent"])


@app.get("/")
async def root():
    return {
        "service": "Agent Service",
        "status": "running",
        "version": "1.0.0",
        "available_roles": settings.available_roles
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug
    )