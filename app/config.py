"""Application configuration using Pydantic Settings."""
from typing import Optional, List
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/celesto_ledger"
    )
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "celesto_ledger"
    POSTGRES_PORT: int = 5432

    # Celesto Credentials
    CELESTO_API_KEY: Optional[str] = None

    # LLM Settings
    LLM_PROVIDER: str = "openai_compatible"
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o"

    # Sandbox Defaults
    DEFAULT_SANDBOX_TEMPLATE: str = "coding-agent"
    DEFAULT_SANDBOX_CPUS: int = 1
    DEFAULT_SANDBOX_MEMORY_MB: int = 1024
    DEFAULT_SANDBOX_DISK_MB: int = 15360
    SANDBOX_TIMEOUT_SECONDS: int = 600

    # Safety & Audit
    AUDIT_LOG_PATH: str = "logs/commands.jsonl"
    BLOCKED_COMMAND_PATTERNS: str = "rm -rf /|:(){ :|:& };:|mkfs|dd if=|curl.*http://.*exfil|wget.*http://.*exfil"
    ALLOWED_COMMAND_PREFIXES: str = "git,python,pytest,pytest-3,pip,ls,dir,cat,echo,mkdir,touch,cp,mv,grep,find,pwd,which,uname,whoami,head,tail,diff"

    @property
    def is_celesto_configured(self) -> bool:
        return bool(self.CELESTO_API_KEY and self.CELESTO_API_KEY != "your_celesto_api_key_here")

    @property
    def is_llm_configured(self) -> bool:
        return bool(self.LLM_API_KEY and self.LLM_API_KEY != "your_llm_api_key_here")


settings = Settings()
