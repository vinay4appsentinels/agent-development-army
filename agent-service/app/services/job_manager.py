import asyncio
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from app.config import settings
from app.models.job import (
    JobRequest, JobResponse, JobResult, JobInfo, JobStatus,
    generate_job_id
)
from app.services.claude_service import ClaudeService

logger = logging.getLogger(__name__)


class JobManager:
    """Manager for handling job lifecycle and storage"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.JobManager")
        self.jobs: Dict[str, JobInfo] = {}
        self.job_results: Dict[str, JobResult] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.claude_service = ClaudeService()
        
        # Load existing jobs from storage
        self._load_jobs_from_storage()
    
    async def create_job(self, job_id: str, request: JobRequest) -> JobResponse:
        """Create a new job"""
        now = datetime.utcnow()
        
        # Create job info
        job_info = JobInfo(
            job_id=job_id,
            status=JobStatus.PENDING,
            role=request.role,
            task_description=request.task.description,
            created_at=now
        )
        
        # Store job
        self.jobs[job_id] = job_info
        
        # Save to persistent storage
        await self._save_job_to_storage(job_id, request, job_info)
        
        # Create response
        response = JobResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            message="Job created successfully",
            estimated_completion=None  # TODO: Estimate based on task type and role
        )
        
        self.logger.info(f"Created job {job_id} with role {request.role}")
        return response
    
    async def start_job(self, job_id: str) -> bool:
        """Start job execution asynchronously"""
        if job_id not in self.jobs:
            self.logger.error(f"Job {job_id} not found")
            return False
        
        job_info = self.jobs[job_id]
        if job_info.status != JobStatus.PENDING:
            self.logger.warning(f"Job {job_id} is not in PENDING status")
            return False
        
        # Check concurrent job limit
        running_count = len([j for j in self.jobs.values() if j.status == JobStatus.RUNNING])
        if running_count >= settings.max_concurrent_jobs:
            self.logger.warning(f"Maximum concurrent jobs ({settings.max_concurrent_jobs}) reached")
            return False
        
        # Load job request from storage
        request = await self._load_job_request_from_storage(job_id)
        if not request:
            self.logger.error(f"Could not load job request for {job_id}")
            return False
        
        # Update job status
        job_info.status = JobStatus.RUNNING
        job_info.started_at = datetime.utcnow()
        
        # Create and start async task
        task = asyncio.create_task(self._execute_job(job_id, request))
        self.running_tasks[job_id] = task
        
        self.logger.info(f"Started job {job_id}")
        return True
    
    async def _execute_job(self, job_id: str, request: JobRequest):
        """Execute a job (runs in background task)"""
        try:
            self.logger.info(f"Executing job {job_id}")
            
            # Execute job using Claude service
            result = await self.claude_service.execute_job(job_id, request)
            
            # Update job status
            if job_id in self.jobs:
                job_info = self.jobs[job_id]
                job_info.status = result.status
                job_info.completed_at = result.completed_at
                
                # Store result
                self.job_results[job_id] = result
                
                # Save result to storage
                await self._save_job_result_to_storage(job_id, result)
                
                self.logger.info(f"Job {job_id} completed with status: {result.status}")
            
        except Exception as e:
            self.logger.error(f"Error executing job {job_id}: {e}", exc_info=True)
            
            # Update job as failed
            if job_id in self.jobs:
                job_info = self.jobs[job_id]
                job_info.status = JobStatus.FAILED
                job_info.completed_at = datetime.utcnow()
                
                # Create error result
                error_result = JobResult(
                    job_id=job_id,
                    status=JobStatus.FAILED,
                    role=request.role,
                    task_type=request.task.type,
                    started_at=job_info.started_at or datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    error=str(e),
                    logs=[f"Job execution failed: {str(e)}"]
                )
                
                self.job_results[job_id] = error_result
                await self._save_job_result_to_storage(job_id, error_result)
        
        finally:
            # Clean up running task
            if job_id in self.running_tasks:
                del self.running_tasks[job_id]
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        if job_id not in self.jobs:
            return False
        
        job_info = self.jobs[job_id]
        
        # Can only cancel pending or running jobs
        if job_info.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
            return False
        
        # Cancel running task if exists
        if job_id in self.running_tasks:
            task = self.running_tasks[job_id]
            task.cancel()
            del self.running_tasks[job_id]
        
        # Update job status
        job_info.status = JobStatus.CANCELLED
        job_info.completed_at = datetime.utcnow()
        
        self.logger.info(f"Cancelled job {job_id}")
        return True
    
    async def get_job(self, job_id: str) -> Optional[JobInfo]:
        """Get job information"""
        return self.jobs.get(job_id)
    
    async def get_job_result(self, job_id: str) -> Optional[JobResult]:
        """Get job result"""
        return self.job_results.get(job_id)
    
    async def list_jobs(self) -> List[JobInfo]:
        """List all jobs"""
        return list(self.jobs.values())
    
    async def get_job_logs(self, job_id: str) -> Optional[List[str]]:
        """Get job execution logs"""
        result = self.job_results.get(job_id)
        if result:
            return result.logs
        return None
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        total_jobs = len(self.jobs)
        running_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.RUNNING])
        completed_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.COMPLETED])
        failed_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.FAILED])
        cancelled_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.CANCELLED])
        
        # Role statistics
        role_stats = {}
        for role in settings.available_roles:
            role_jobs = [j for j in self.jobs.values() if j.role == role]
            role_stats[role] = {
                "total": len(role_jobs),
                "running": len([j for j in role_jobs if j.status == JobStatus.RUNNING]),
                "completed": len([j for j in role_jobs if j.status == JobStatus.COMPLETED]),
                "failed": len([j for j in role_jobs if j.status == JobStatus.FAILED])
            }
        
        return {
            "total_jobs": total_jobs,
            "running_jobs": running_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "cancelled_jobs": cancelled_jobs,
            "role_statistics": role_stats,
            "max_concurrent_jobs": settings.max_concurrent_jobs,
            "available_roles": settings.available_roles
        }
    
    def _load_jobs_from_storage(self):
        """Load existing jobs from persistent storage"""
        jobs_dir = os.path.join(settings.jobs_storage_path, "jobs")
        if not os.path.exists(jobs_dir):
            return
        
        try:
            for filename in os.listdir(jobs_dir):
                if filename.endswith("_info.json"):
                    job_id = filename.replace("_info.json", "")
                    info_path = os.path.join(jobs_dir, filename)
                    
                    with open(info_path, 'r') as f:
                        job_data = json.load(f)
                        job_info = JobInfo(**job_data)
                        self.jobs[job_id] = job_info
                    
                    # Load result if available
                    result_path = os.path.join(jobs_dir, f"{job_id}_result.json")
                    if os.path.exists(result_path):
                        with open(result_path, 'r') as f:
                            result_data = json.load(f)
                            # Convert datetime strings back to datetime objects
                            for field in ['started_at', 'completed_at']:
                                if result_data.get(field):
                                    result_data[field] = datetime.fromisoformat(result_data[field])
                            job_result = JobResult(**result_data)
                            self.job_results[job_id] = job_result
            
            self.logger.info(f"Loaded {len(self.jobs)} jobs from storage")
            
        except Exception as e:
            self.logger.error(f"Error loading jobs from storage: {e}", exc_info=True)
    
    async def _save_job_to_storage(self, job_id: str, request: JobRequest, job_info: JobInfo):
        """Save job to persistent storage"""
        jobs_dir = os.path.join(settings.jobs_storage_path, "jobs")
        os.makedirs(jobs_dir, exist_ok=True)
        
        try:
            # Save job info
            info_path = os.path.join(jobs_dir, f"{job_id}_info.json")
            with open(info_path, 'w') as f:
                json.dump(job_info.dict(), f, default=str, indent=2)
            
            # Save job request
            request_path = os.path.join(jobs_dir, f"{job_id}_request.json")
            with open(request_path, 'w') as f:
                json.dump(request.dict(), f, default=str, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving job {job_id} to storage: {e}", exc_info=True)
    
    async def _save_job_result_to_storage(self, job_id: str, result: JobResult):
        """Save job result to persistent storage"""
        jobs_dir = os.path.join(settings.jobs_storage_path, "jobs")
        
        try:
            result_path = os.path.join(jobs_dir, f"{job_id}_result.json")
            with open(result_path, 'w') as f:
                json.dump(result.dict(), f, default=str, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving job result {job_id} to storage: {e}", exc_info=True)
    
    async def _load_job_request_from_storage(self, job_id: str) -> Optional[JobRequest]:
        """Load job request from persistent storage"""
        jobs_dir = os.path.join(settings.jobs_storage_path, "jobs")
        request_path = os.path.join(jobs_dir, f"{job_id}_request.json")
        
        try:
            if os.path.exists(request_path):
                with open(request_path, 'r') as f:
                    request_data = json.load(f)
                    return JobRequest(**request_data)
        except Exception as e:
            self.logger.error(f"Error loading job request {job_id} from storage: {e}", exc_info=True)
        
        return None