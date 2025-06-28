import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime

from app.config import settings
from app.models.job import (
    JobRequest, JobResponse, JobResult, JobInfo, JobStatus,
    generate_job_id
)
from app.services.job_manager import JobManager
from app.services.claude_service import ClaudeService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
job_manager = JobManager()
claude_service = ClaudeService()


@router.post("/jobs", response_model=JobResponse)
async def create_job(request: JobRequest):
    """Create a new agent job"""
    try:
        # Validate role
        if request.role not in settings.available_roles:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role '{request.role}'. Available roles: {', '.join(settings.available_roles)}"
            )
        
        # Generate job ID
        job_id = generate_job_id()
        
        # Create job in manager
        job_response = await job_manager.create_job(job_id, request)
        
        # Start job execution asynchronously
        await job_manager.start_job(job_id)
        
        logger.info(f"Created job {job_id} with role {request.role}")
        
        return job_response
        
    except ValueError as e:
        logger.error(f"Validation error creating job: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create job")


@router.get("/jobs", response_model=List[JobInfo])
async def list_jobs():
    """List all jobs"""
    try:
        jobs = await job_manager.list_jobs()
        return jobs
    except Exception as e:
        logger.error(f"Error listing jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list jobs")


@router.get("/jobs/{job_id}", response_model=JobInfo)
async def get_job(job_id: str):
    """Get job information by ID"""
    try:
        job = await job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get job")


@router.get("/jobs/{job_id}/result", response_model=JobResult)
async def get_job_result(job_id: str):
    """Get job result by ID"""
    try:
        result = await job_manager.get_job_result(job_id)
        if not result:
            raise HTTPException(status_code=404, detail="Job result not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job result {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get job result")


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a running job"""
    try:
        success = await job_manager.cancel_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail="Job not found or cannot be cancelled")
        
        logger.info(f"Cancelled job {job_id}")
        return {"message": f"Job {job_id} cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to cancel job")


@router.get("/jobs/{job_id}/logs")
async def get_job_logs(job_id: str):
    """Get job execution logs"""
    try:
        logs = await job_manager.get_job_logs(job_id)
        if logs is None:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {"job_id": job_id, "logs": logs}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job logs {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get job logs")


@router.get("/roles")
async def list_roles():
    """List available agent roles"""
    roles_info = {}
    for role in settings.available_roles:
        role_config = settings.get_role_config(role)
        roles_info[role] = {
            "name": role,
            "description": role_config.get("description", f"{role} agent role"),
            "timeout": settings.get_role_timeout(role),
            "system_prompt_file": settings.get_role_prompt_file(role)
        }
    
    return {
        "available_roles": settings.available_roles,
        "default_role": settings.default_role,
        "roles": roles_info
    }


@router.get("/stats")
async def get_stats():
    """Get service statistics"""
    try:
        stats = await job_manager.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get statistics")