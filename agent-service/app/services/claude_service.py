import asyncio
import subprocess
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.config import settings
from app.models.job import JobRequest, JobResult, JobStatus, TaskType

logger = logging.getLogger(__name__)


class ClaudeService:
    """Service for executing Claude CLI commands with role-based prompts"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ClaudeService")
    
    async def execute_job(self, job_id: str, request: JobRequest) -> JobResult:
        """Execute a job using Claude CLI with role-specific configuration"""
        start_time = datetime.utcnow()
        
        try:
            # Get role configuration
            role_config = settings.get_role_config(request.role)
            timeout = settings.get_role_timeout(request.role)
            
            # Build Claude CLI command
            command = await self._build_claude_command(request, role_config)
            
            # Set up environment
            env = self._setup_environment(request)
            
            # Set working directory
            working_dir = self._get_working_directory(request)
            
            self.logger.info(f"Executing job {job_id} with role {request.role}")
            self.logger.debug(f"Command: {' '.join(command)}")
            self.logger.debug(f"Working directory: {working_dir}")
            
            # Execute command
            result = await self._execute_command(
                command=command,
                timeout=timeout,
                env=env,
                cwd=working_dir
            )
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Determine final status
            status = JobStatus.COMPLETED if result["returncode"] == 0 else JobStatus.FAILED
            
            # Create job result
            job_result = JobResult(
                job_id=job_id,
                status=status,
                role=request.role,
                task_type=request.task.type,
                started_at=start_time,
                completed_at=end_time,
                duration=duration,
                output=result["stdout"] if status == JobStatus.COMPLETED else None,
                error=result["stderr"] if status == JobStatus.FAILED else None,
                logs=result["logs"],
                files_created=[],  # TODO: Detect created files
                files_modified=[],  # TODO: Detect modified files
                metadata={
                    "command": command,
                    "returncode": result["returncode"],
                    "working_directory": working_dir
                }
            )
            
            return job_result
            
        except asyncio.TimeoutError:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            return JobResult(
                job_id=job_id,
                status=JobStatus.FAILED,
                role=request.role,
                task_type=request.task.type,
                started_at=start_time,
                completed_at=end_time,
                duration=duration,
                error=f"Job timed out after {timeout} seconds",
                logs=[f"Job execution timed out"],
                metadata={"timeout": timeout}
            )
            
        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.error(f"Error executing job {job_id}: {e}", exc_info=True)
            
            return JobResult(
                job_id=job_id,
                status=JobStatus.FAILED,
                role=request.role,
                task_type=request.task.type,
                started_at=start_time,
                completed_at=end_time,
                duration=duration,
                error=str(e),
                logs=[f"Execution error: {str(e)}"],
                metadata={"exception": str(e)}
            )
    
    async def _build_claude_command(self, request: JobRequest, role_config: Dict[str, Any]) -> List[str]:
        """Build the Claude CLI command with role-specific parameters"""
        command = [settings.claude_cli_path]
        
        # Add system prompt if available
        prompt_file = settings.get_role_prompt_file(request.role)
        if os.path.exists(prompt_file):
            command.extend(["--system-prompt", f"@{prompt_file}"])
        
        # Add task description as the main prompt
        task_prompt = self._build_task_prompt(request)
        command.append(task_prompt)
        
        # Add role-specific CLI arguments from config
        cli_args = role_config.get("cli_args", [])
        if cli_args:
            command.extend(cli_args)
        
        return command
    
    def _build_task_prompt(self, request: JobRequest) -> str:
        """Build the task prompt based on the job request"""
        lines = []
        
        # Role introduction
        lines.append(f"You are acting as a {request.role} agent.")
        
        # Context information
        lines.append(f"Repository: {request.context.repository}")
        if request.context.issue_number:
            lines.append(f"GitHub Issue: #{request.context.issue_number}")
        lines.append(f"Branch: {request.context.branch}")
        
        # Task details
        lines.append(f"Task Type: {request.task.type.value}")
        lines.append(f"Task Description: {request.task.description}")
        
        # Requirements and constraints
        if request.task.requirements:
            lines.append("Requirements:")
            for req in request.task.requirements:
                lines.append(f"- {req}")
        
        if request.task.constraints:
            lines.append("Constraints:")
            for constraint in request.task.constraints:
                lines.append(f"- {constraint}")
        
        # Priority
        lines.append(f"Priority: {request.task.priority.value}")
        
        return "\\n".join(lines)
    
    def _setup_environment(self, request: JobRequest) -> Dict[str, str]:
        """Set up environment variables for the command execution"""
        env = os.environ.copy()
        
        # Add job-specific environment variables
        if request.environment and request.environment.variables:
            env.update(request.environment.variables)
        
        # Add context-specific variables
        env["REPO_NAME"] = request.context.repository
        env["BRANCH"] = request.context.branch
        if request.context.issue_number:
            env["ISSUE_NUMBER"] = str(request.context.issue_number)
        if request.context.commit_sha:
            env["COMMIT_SHA"] = request.context.commit_sha
        
        return env
    
    def _get_working_directory(self, request: JobRequest) -> str:
        """Get the working directory for command execution"""
        if request.environment and request.environment.working_directory:
            return request.environment.working_directory
        elif request.context.workspace_path:
            return request.context.workspace_path
        else:
            # Default to a job-specific directory
            return os.path.join(settings.jobs_storage_path, "workspace")
    
    async def _execute_command(
        self, 
        command: List[str], 
        timeout: int, 
        env: Dict[str, str], 
        cwd: str
    ) -> Dict[str, Any]:
        """Execute the command asynchronously with timeout"""
        logs = []
        
        try:
            # Ensure working directory exists
            os.makedirs(cwd, exist_ok=True)
            
            # Log command execution
            logs.append(f"Executing command: {' '.join(command)}")
            logs.append(f"Working directory: {cwd}")
            logs.append(f"Timeout: {timeout} seconds")
            
            # Create subprocess
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=cwd
            )
            
            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            # Decode output
            stdout_text = stdout.decode('utf-8') if stdout else ""
            stderr_text = stderr.decode('utf-8') if stderr else ""
            
            logs.append(f"Command completed with return code: {process.returncode}")
            
            return {
                "returncode": process.returncode,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "logs": logs
            }
            
        except asyncio.TimeoutError:
            logs.append(f"Command timed out after {timeout} seconds")
            # Try to terminate the process
            try:
                process.terminate()
                await process.wait()
            except:
                pass
            raise
            
        except Exception as e:
            logs.append(f"Command execution failed: {str(e)}")
            raise