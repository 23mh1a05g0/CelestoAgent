"""Failure detection and recovery policy service."""
import json
import os
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from app.services.celesto_service import celesto_service
from app.services.lifecycle_service import lifecycle_service
from app.tools.shell_tool import ShellTool


class RecoveryService:
    """Manages failure recovery and trace logging."""

    RATIONALE = (
        "The Celesto Cloud SDK does not expose snapshot or rollback capabilities for hosted computers. "
        "When a failure occurs (such as deliberate step 7 failure injection), the control plane deletes the "
        "failed sandbox, provisions a fresh computer with a new unique name, and re-executes the task from step 1. "
        "This provides maximum correctness: each retry starts from a known-clean state with no residual side effects "
        "from the failed attempt. The trade-off is higher cost and longer wall-clock time, but it guarantees absolute "
        "state integrity."
    )

    def __init__(self, trace_file_path: str = "reports/failure_trace.jsonl"):
        self.trace_file_path = trace_file_path
        os.makedirs(os.path.dirname(self.trace_file_path), exist_ok=True)

    def log_trace_event(self, event: Dict[str, Any]) -> None:
        """Append event to failure_trace.jsonl."""
        with open(self.trace_file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    def export_policy_spec(self, output_path: str = "reports/failure_policy.json") -> Dict[str, Any]:
        """Export failure_policy.json specification."""
        spec = {
            "policy": "fresh",
            "rationale": self.RATIONALE,
            "failure_trigger_step": 7,
            "max_retries": 2,
            "recovery_action": "terminate_failed_sandbox_and_provision_fresh",
            "updated_at": datetime.utcnow().isoformat()
        }
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2)
        return spec

    def execute_workflow_with_recovery(
        self,
        run_id: str,
        steps: List[Dict[str, Any]],
        failure_step: Optional[int] = None,
        template_id: str = "coding-agent",
        force_simulator: bool = False,
    ) -> Dict[str, Any]:
        """Execute a series of workflow steps with fresh-sandbox failure recovery."""
        attempt = 1
        max_attempts = 2
        overall_start = time.time()
        
        while attempt <= max_attempts:
            # 1. Provision sandbox
            t_boot_0 = time.time()
            sandbox = celesto_service.create_sandbox(template_id=template_id, force_simulator=force_simulator)
            boot_s = time.time() - t_boot_0
            lifecycle_service.record_transition(
                sandbox.name, "created", "ready", duration_s=round(boot_s, 2),
                metadata={"recovery_attempt": attempt, "run_id": run_id}
            )
            shell = ShellTool(sandbox, run_id=run_id)
            
            self.log_trace_event({
                "timestamp": datetime.utcnow().isoformat(),
                "event": "sandbox_provisioned",
                "run_id": run_id,
                "attempt": attempt,
                "sandbox_name": sandbox.name
            })
            
            failed = False
            executed_steps = 0
            
            for idx, step_info in enumerate(steps, start=1):
                step_name = step_info.get("name", f"step_{idx}")
                cmd = step_info.get("command", "echo 'step'")
                
                # Check for deliberate failure injection
                if failure_step and idx == failure_step and attempt == 1:
                    failed = True
                    self.log_trace_event({
                        "timestamp": datetime.utcnow().isoformat(),
                        "event": "step_failure_injected",
                        "run_id": run_id,
                        "attempt": attempt,
                        "step_index": idx,
                        "step_name": step_name,
                        "error": "Simulated environment failure at checkpoint"
                    })
                    break

                res = shell.execute(cmd)
                executed_steps += 1
                
                self.log_trace_event({
                    "timestamp": datetime.utcnow().isoformat(),
                    "event": "step_completed",
                    "run_id": run_id,
                    "attempt": attempt,
                    "step_index": idx,
                    "step_name": step_name,
                    "exit_code": res.exit_code
                })
                
                if res.exit_code != 0:
                    failed = True
                    break

            if not failed:
                # Succeeded!
                self.log_trace_event({
                    "timestamp": datetime.utcnow().isoformat(),
                    "event": "workflow_completed",
                    "run_id": run_id,
                    "attempt": attempt,
                    "sandbox_name": sandbox.name,
                    "total_steps": executed_steps
                })
                celesto_service.delete_sandbox(sandbox.name)
                lifecycle_service.record_transition(sandbox.name, "ready", "deleted", metadata={"outcome": "completed"})
                return {
                    "success": True,
                    "attempts": attempt,
                    "total_steps": executed_steps,
                    "wall_clock_s": round(time.time() - overall_start, 2)
                }

            # Failure recovery triggered
            self.log_trace_event({
                "timestamp": datetime.utcnow().isoformat(),
                "event": "recovery_triggered",
                "run_id": run_id,
                "attempt": attempt,
                "policy": "fresh",
                "action": "destroying_failed_sandbox",
                "failed_sandbox": sandbox.name
            })
            celesto_service.delete_sandbox(sandbox.name)
            lifecycle_service.record_transition(sandbox.name, "ready", "deleted", metadata={"outcome": "failed_recovery_destroy"})
            attempt += 1

        return {
            "success": False,
            "attempts": attempt - 1,
            "error": "Max recovery attempts exceeded",
            "wall_clock_s": round(time.time() - overall_start, 2)
        }


recovery_service = RecoveryService()
