"""SQLAlchemy ORM models for Celesto Agent Platform."""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    JSON,
    func
)
from app.database import Base


class Run(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(String(64), unique=True, index=True, nullable=False)
    task_description = Column(Text, nullable=False)
    status = Column(String(32), index=True, nullable=False, default="pending")
    sandbox_name = Column(String(128), nullable=True)
    sandbox_id = Column(String(128), nullable=True)
    template_id = Column(String(64), nullable=True, default="coding-agent")
    execution_target = Column(String(64), nullable=True, default="celesto_sandbox")
    
    started_at = Column(DateTime(timezone=True), default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    wall_clock_s = Column(Float, nullable=True)
    boot_to_ready_s = Column(Float, nullable=True)
    cost_usd = Column(Float, default=0.0)
    
    steps_count = Column(Integer, default=0)
    commands_executed = Column(Integer, default=0)
    safety_violations = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # Using 'run_metadata' for column attribute while mapping to db column 'metadata'
    run_metadata = Column("metadata", JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "task_description": self.task_description,
            "status": self.status,
            "sandbox_name": self.sandbox_name,
            "sandbox_id": self.sandbox_id,
            "template_id": self.template_id,
            "execution_target": self.execution_target or "celesto_sandbox",
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "wall_clock_s": self.wall_clock_s,
            "boot_to_ready_s": self.boot_to_ready_s,
            "cost_usd": self.cost_usd,
            "steps_count": self.steps_count,
            "commands_executed": self.commands_executed,
            "safety_violations": self.safety_violations,
            "error_message": self.error_message,
            "metadata": self.run_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
