"""Shell command execution tool integrated with safety hooks and audit logging."""
import time
from typing import Optional, Dict, Any
from app.schemas import CommandExecutionResult
from app.services.safety_service import safety_service


class ShellTool:
    """Safely executes shell commands within a sandbox."""

    def __init__(self, sandbox: Any, run_id: Optional[str] = None):
        self.sandbox = sandbox
        self.run_id = run_id
        self.sandbox_name = getattr(sandbox, "name", "unknown")

    def execute(self, command: str, timeout: int = 60) -> CommandExecutionResult:
        # 1. Pre-execution safety hook
        decision = safety_service.pre_command(
            command=command,
            run_id=self.run_id,
            sandbox_name=self.sandbox_name
        )
        if not decision.allowed:
            return CommandExecutionResult(
                command=command,
                stdout="",
                stderr=f"Execution blocked by safety policy: {decision.reason}",
                exit_code=126,
                wall_clock_s=0.0,
                blocked=True,
                block_reason=decision.reason
            )

        # 2. Execution in sandbox with timing
        t0 = time.time()
        try:
            raw_res = self.sandbox.run(command, timeout=timeout)
            t1 = time.time()
            wall_clock_s = t1 - t0

            stdout = raw_res.get("stdout", "")
            stderr = raw_res.get("stderr", "")
            exit_code = raw_res.get("exit_code", 0)

            # 3. Post-execution hook & audit log
            safety_service.post_command(
                command=command,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                wall_clock_s=wall_clock_s,
                run_id=self.run_id,
                sandbox_name=self.sandbox_name
            )

            return CommandExecutionResult(
                command=command,
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                wall_clock_s=round(wall_clock_s, 4),
                blocked=False,
                block_reason=None
            )
        except Exception as exc:
            wall_clock_s = time.time() - t0
            stderr = f"Command execution exception: {str(exc)}"
            safety_service.post_command(
                command=command,
                exit_code=1,
                stdout="",
                stderr=stderr,
                wall_clock_s=wall_clock_s,
                run_id=self.run_id,
                sandbox_name=self.sandbox_name
            )
            return CommandExecutionResult(
                command=command,
                stdout="",
                stderr=stderr,
                exit_code=1,
                wall_clock_s=round(wall_clock_s, 4),
                blocked=False,
                block_reason=None
            )
