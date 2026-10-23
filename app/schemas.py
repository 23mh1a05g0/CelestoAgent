"""Pydantic request and response schemas."""
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re

RunStatus = Literal["pending", "provisioning", "running", "completed", "failed", "cancelled"]
ExecutionTarget = Literal["celesto_sandbox", "simulated_sandbox"]


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["healthy"])
    database: str = Field(..., examples=["connected"])
    environment: str = Field(..., examples=["development"])
    celesto_configured: bool = Field(..., examples=[False])
    llm_configured: bool = Field(..., examples=[False])
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RunCreateRequest(BaseModel):
    task_description: str = Field(..., min_length=3, description="Description of the task for the agent")
    template_id: Optional[str] = Field("coding-agent", description="Celesto sandbox template")
    execution_target: Optional[ExecutionTarget] = Field("celesto_sandbox", description="Target execution environment")
    sandbox_name: Optional[str] = Field(None, max_length=128, description="Explicit sandbox identifier override")
    cpus: Optional[int] = Field(1, ge=1, le=8, description="Number of vCPUs")
    memory_mb: Optional[int] = Field(1024, ge=512, le=32768, description="RAM in MB")
    disk_mb: Optional[int] = Field(15360, ge=512, le=51200, description="Disk size in MB")
    network_policy: Optional[Dict[str, Any]] = Field(default_factory=lambda: {"mode": "open"})
    recovery_policy: Optional[str] = Field("fresh", description="Failure recovery policy: fresh or retry")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("sandbox_name")
    @classmethod
    def validate_sandbox_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.match(r"^[a-zA-Z0-9_\-\.]{1,128}$", v):
                raise ValueError("sandbox_name must contain only alphanumeric characters, hyphens, underscores, or periods")
        return v


class RunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: str
    task_description: str
    status: str
    execution_target: Optional[str] = "celesto_sandbox"
    sandbox_name: Optional[str] = None
    sandbox_id: Optional[str] = None
    template_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    wall_clock_s: Optional[float] = None
    boot_to_ready_s: Optional[float] = None
    cost_usd: float = 0.0
    steps_count: int = 0
    commands_executed: int = 0
    safety_violations: int = 0
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, alias="run_metadata")


class RunListResponse(BaseModel):
    items: List[RunResponse]
    total: int


class CommandExecutionRequest(BaseModel):
    command: str = Field(..., min_length=1, description="Shell command to execute in sandbox")
    timeout_seconds: Optional[int] = Field(60, ge=1, le=600)


class CommandExecutionResult(BaseModel):
    command: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    wall_clock_s: float = 0.0
    blocked: bool = False
    block_reason: Optional[str] = None
