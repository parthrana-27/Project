from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache
from typing import Literal

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    app_name: str = "NL2Code Compiler"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # LLM Settings
    llm_provider: Literal["mock", "gemini", "openai", "anthropic"] = "mock"
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    
    gemini_model: str = "gemini-2.0-flash"
    openai_model: str = "gpt-4o"
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    
    # Storage
    database_url: str = "sqlite:///./nl2code.db"
    
    # Sandbox configuration
    sandbox_timeout_seconds: int = 5
    sandbox_memory_limit: str = "256m"
    sandbox_cpu_limit: float = 1.0
    use_docker_sandbox: bool = False  # Auto-detected or forced
    
    # Rate Limiting & Safety
    rate_limit_per_minute: int = 60
    max_repair_iterations: int = 3

@lru_cache()
def get_settings() -> Settings:
    return Settings()
