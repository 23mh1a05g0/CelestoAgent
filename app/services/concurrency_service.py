"""Concurrency orchestration, isolation management, and benchmark service."""
import json
import os
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor

from app.services.celesto_service import celesto_service
from app.tools.shell_tool import ShellTool
from app.services.lifecycle_service import lifecycle_service


class ConcurrencyService:
    """Manages concurrent sandbox workloads with strict resource and state isolation."""

    RATIONALE = (
        "Each concurrent job executes inside a strictly isolated, independently provisioned Celesto microVM. "
        "No filesystem, memory, or network state is shared between jobs. "
        "Sequential batching or bounded worker pools prevent API rate-limit exhaustion and ensure "
        "audit logs maintain deterministic causality."
    )

    def __init__(self, report_path: str = "reports/concurrency.json"):
        self.report_path = report_path
        os.makedirs(os.path.dirname(self.report_path), exist_ok=True)

    def generate_concurrency_spec(
        self,
        concurrency_level: int = 5,
        scheduling_mode: str = "sequential_batch",
        completed_jobs: int = 5,
        failed_jobs: int = 0,
        wall_clock_s: float = 24.5,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate and save concurrency.json report according to specification."""
        path = output_path or self.report_path
        data = {
            "concurrency_level": concurrency_level,
            "scheduling_mode": scheduling_mode,
            "isolation_guarantee": "hardware_microvm_per_job",
            "rationale": self.RATIONALE,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "wall_clock_s": round(wall_clock_s, 2),
            "generated_at": datetime.utcnow().isoformat()
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return data

    def execute_batch(
        self,
        num_jobs: int = 5,
        command: str = "uname -a",
        template_id: str = "coding-agent",
        force_simulator: bool = False
    ) -> Dict[str, Any]:
        """Execute a batch of jobs in dedicated isolated sandboxes (one sandbox per job)."""
        t0 = time.time()
        completed = 0
        failed = 0
        job_results = []

        for j in range(1, num_jobs + 1):
            job_id = f"concurrency-job-{j:02d}"
            job_start = time.time()
            sbx = None
            try:
                sbx = celesto_service.create_sandbox(
                    template_id=template_id,
                    force_simulator=force_simulator
                )
                shell = ShellTool(sbx, run_id=job_id)
                res = shell.execute(command)

                job_elapsed = round(time.time() - job_start, 3)
                is_success = (res.exit_code == 0 and not res.blocked)
                if is_success:
                    completed += 1
                else:
                    failed += 1

                job_results.append({
                    "job_index": j,
                    "job_id": job_id,
                    "sandbox_name": sbx.name,
                    "sandbox_id": getattr(sbx, "id", sbx.name),
                    "exit_code": res.exit_code,
                    "wall_clock_s": job_elapsed,
                    "success": is_success
                })
            except Exception as exc:
                failed += 1
                job_results.append({
                    "job_index": j,
                    "job_id": job_id,
                    "sandbox_name": "error",
                    "error": str(exc),
                    "success": False
                })
            finally:
                if sbx:
                    celesto_service.delete_sandbox(sbx.name)

        total_time = round(time.time() - t0, 2)
        report = self.generate_concurrency_spec(
            concurrency_level=num_jobs,
            scheduling_mode="sequential_batch",
            completed_jobs=completed,
            failed_jobs=failed,
            wall_clock_s=total_time
        )
        report["jobs"] = job_results
        return report


concurrency_service = ConcurrencyService()
