from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import uuid


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class TaskType(str, Enum):
    CODE_REVIEW = "code_review"
    BUG_FIX = "bug_fix"
    FEATURE_IMPLEMENTATION = "feature_implementation"
    ARCHITECTURE_DESIGN = "architecture_design"
    CODE_ANALYSIS = "code_analysis"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    OPTIMIZATION = "optimization"


class JobContext(BaseModel):
    repository: str = Field(..., description="Repository name (org/repo)")
    issue_number: Optional[int] = Field(None, description="GitHub issue number")
    branch: str = Field(default="main", description="Git branch to work on")
    workspace_path: Optional[str] = Field(None, description="Local workspace path")
    commit_sha: Optional[str] = Field(None, description="Specific commit SHA")


class JobTask(BaseModel):
    type: TaskType = Field(..., description="Type of task to perform")
    description: str = Field(..., description="Detailed task description")
    priority: JobPriority = Field(default=JobPriority.NORMAL, description="Task priority")
    requirements: Optional[List[str]] = Field(default=[], description="Specific requirements")
    constraints: Optional[List[str]] = Field(default=[], description="Task constraints")


class JobEnvironment(BaseModel):
    variables: Dict[str, str] = Field(default={}, description="Environment variables")
    tools: List[str] = Field(default=[], description="Required tools")
    working_directory: Optional[str] = Field(None, description="Working directory")


class JobRequest(BaseModel):
    role: str = Field(..., description="Agent role (DEVELOPER, ARCHITECT, ANALYST)")
    context: JobContext = Field(..., description="Job context information")
    task: JobTask = Field(..., description="Task details")
    environment: Optional[JobEnvironment] = Field(default=JobEnvironment(), description="Environment configuration")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")


class JobResponse(BaseModel):
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    message: str = Field(..., description="Status message")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")


class JobResult(BaseModel):
    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Final job status")
    role: str = Field(..., description="Agent role used")
    task_type: TaskType = Field(..., description="Task type")
    
    # Execution details
    started_at: datetime = Field(..., description="Job start time")
    completed_at: Optional[datetime] = Field(None, description="Job completion time")
    duration: Optional[float] = Field(None, description="Execution duration in seconds")
    
    # Results
    output: Optional[str] = Field(None, description="Job output/result")
    error: Optional[str] = Field(None, description="Error message if failed")
    logs: List[str] = Field(default=[], description="Execution logs")
    
    # Files and changes
    files_created: List[str] = Field(default=[], description="Files created during execution")
    files_modified: List[str] = Field(default=[], description="Files modified during execution")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default={}, description="Additional result metadata")


class JobInfo(BaseModel):
    job_id: str
    status: JobStatus
    role: str
    task_description: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: Optional[str] = None


def generate_job_id() -> str:
    """Generate a unique job ID"""
    return str(uuid.uuid4())