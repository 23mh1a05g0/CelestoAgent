"""Safety service providing pre-execution validation, hooks, and audit logging."""
import json
import os
import time
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from app.config import settings
from app.security.command_policy import CommandPolicy, PolicyDecision
from app.security.redaction import redact_text, redact_data


class SafetyService:
    def __init__(self, audit_log_path: Optional[str] = None):
        self.policy = CommandPolicy()
        self.audit_log_path = audit_log_path or settings.AUDIT_LOG_PATH
        # Ensure log directory exists
        log_dir = os.path.dirname(self.audit_log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

    def log_audit_entry(self, entry: Dict[str, Any]) -> None:
        """Append an entry to the commands.jsonl audit log."""
        try:
            redacted_entry = redact_data(entry)
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(redacted_entry) + "\n")
        except Exception as exc:
            print(f"Warning: Failed to write to audit log: {exc}")

    def pre_command(
        self,
        command: str,
        run_id: Optional[str] = None,
        sandbox_name: Optional[str] = None
    ) -> PolicyDecision:
        """Hook called before executing any command in the sandbox."""
        decision = self.policy.evaluate(command)
        if not decision.allowed:
            # Audit log the blocked attempt immediately
            self.log_audit_entry({
                "timestamp": datetime.utcnow().isoformat(),
                "event": "command_blocked",
                "execution_target": "celesto_sandbox",
                "run_id": run_id,
                "sandbox_name": sandbox_name,
                "command": command,
                "reason": decision.reason,
                "risk_level": decision.risk_level,
            })
        return decision

    def post_command(
        self,
        command: str,
        exit_code: int,
        stdout: str,
        stderr: str,
        wall_clock_s: float,
        run_id: Optional[str] = None,
        sandbox_name: Optional[str] = None
    ) -> None:
        """Hook called after command execution in the sandbox."""
        self.log_audit_entry({
            "timestamp": datetime.utcnow().isoformat(),
            "event": "command_executed",
            "execution_target": "celesto_sandbox",
            "run_id": run_id,
            "sandbox_name": sandbox_name,
            "command": command,
            "exit_code": exit_code,
            "wall_clock_s": round(wall_clock_s, 4),
            "stdout": stdout[:2000] if stdout else "",  # truncate for audit log
            "stderr": stderr[:2000] if stderr else "",
        })


safety_service = SafetyService()
