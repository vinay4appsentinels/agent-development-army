import os
from typing import List, Dict, Any
from pydantic import BaseSettings, Field
import yaml


class Settings(BaseSettings):
    port: int = Field(default=4045, env="PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Claude CLI configuration
    claude_cli_path: str = Field(default="claude", env="CLAUDE_CLI_PATH")
    
    # Role configuration
    default_role: str = Field(default="DEVELOPER", env="DEFAULT_ROLE")
    available_roles: List[str] = ["DEVELOPER", "ARCHITECT", "ANALYST"]
    
    # Job configuration
    job_timeout: int = Field(default=1800, env="JOB_TIMEOUT")  # 30 minutes
    max_concurrent_jobs: int = Field(default=3, env="MAX_CONCURRENT_JOBS")
    
    # Paths
    prompts_dir: str = Field(default="prompts", env="PROMPTS_DIR")
    config_file: str = Field(default="config/roles.yml", env="CONFIG_FILE")
    
    # Storage
    jobs_storage_path: str = Field(default="jobs", env="JOBS_STORAGE_PATH")
    
    # Dynamic role config (loaded at runtime)
    role_config: Dict[str, Any] = {}
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __init__(self, **values):
        super().__init__(**values)
        self._load_role_config()
        self._ensure_directories()
    
    def _load_role_config(self):
        """Load role configuration from YAML file"""
        config_path = self.config_file
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    self.role_config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Could not load role config: {e}")
                self.role_config = {}
        else:
            self.role_config = {}
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(self.prompts_dir, exist_ok=True)
        os.makedirs(self.jobs_storage_path, exist_ok=True)
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
    
    def get_role_config(self, role: str) -> Dict[str, Any]:
        """Get configuration for a specific role"""
        return self.role_config.get("roles", {}).get(role, {})
    
    def get_role_prompt_file(self, role: str) -> str:
        """Get prompt file path for a specific role"""
        role_config = self.get_role_config(role)
        prompt_file = role_config.get("system_prompt_file", f"{role.lower()}.txt")
        return os.path.join(self.prompts_dir, prompt_file)
    
    def get_role_timeout(self, role: str) -> int:
        """Get timeout for a specific role"""
        role_config = self.get_role_config(role)
        return role_config.get("timeout", self.job_timeout)


settings = Settings()