import os
from typing import List, Optional
from pydantic import BaseSettings, Field
import yaml


class WebhookConfig(BaseSettings):
    secret: str = Field(..., env="GITHUB_WEBHOOK_SECRET")
    
    class Config:
        env_prefix = "GITHUB_WEBHOOK_"


class Settings(BaseSettings):
    port: int = Field(default=4044, env="PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    debug: bool = Field(default=False, env="DEBUG")
    
    github_webhook_secret: str = Field(..., env="GITHUB_WEBHOOK_SECRET")
    
    config_file: str = Field(default="config/config.yml", env="CONFIG_FILE")
    
    repository_whitelist: List[str] = []
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __init__(self, **values):
        super().__init__(**values)
        self._load_config_file()
    
    def _load_config_file(self):
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), self.config_file)
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                if config_data and 'webhook' in config_data:
                    webhook_config = config_data['webhook']
                    if 'github' in webhook_config and 'repositories' in webhook_config['github']:
                        repos = webhook_config['github']['repositories']
                        self.repository_whitelist = [
                            f"{repo['owner']}/{repo['repo']}" 
                            for repo in repos 
                            if repo.get('enabled', True)
                        ]


settings = Settings()