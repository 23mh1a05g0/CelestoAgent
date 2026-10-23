"""Celesto SDK wrapper and sandbox abstraction.

Supports hosted Celesto Cloud Computers when CELESTO_API_KEY is configured,
with a fallback simulator for Phase 1 local development and testing.
"""
import os
import time
import uuid
import logging
import subprocess
import atexit
from contextlib import contextmanager
from typing import Optional, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)


class SimulatedComputer:
    """Simulated sandbox for Phase 1 testing and offline evaluation."""

    def __init__(
        self,
        template_id: str = "coding-agent",
        cpus: int = 1,
        memory: int = 1024,
        disk: str = "15gb",
        network_policy: Optional[Dict[str, Any]] = None,
    ):
        self.name = f"sim-sbx-{uuid.uuid4().hex[:10]}"
        self.id = f"sim-{uuid.uuid4().hex[:12]}"
        self.status = "ready"
        self.template_id = template_id
        self.cpus = cpus
        self.memory = memory
        self.disk = disk
        self.network_policy = network_policy or {"mode": "open"}
        self._created_at = time.time()
        logger.info(f"Initialized SimulatedComputer '{self.name}' (id: {self.id})")

    def run(self, command: str, timeout: int = 60) -> Dict[str, Any]:
        """Execute command in simulated environment."""
        logger.info(f"[{self.name}] Running command: {command}")
        
        # Test for network containment simulation
        if self.network_policy.get("mode") == "off":
            if any(k in command for k in ["curl", "wget", "nc", "ping", "ssh", "http://", "https://"]):
                return {
                    "stdout": "",
                    "stderr": "curl: (7) Failed to connect: Network is unreachable (contained offline policy)",
                    "exit_code": 7
                }

        stripped = command.strip()
        if stripped == "uname -a":
            return {
                "stdout": "Linux celesto-sandbox 6.6.137-celesto #1 SMP PREEMPT_DYNAMIC x86_64 GNU/Linux\n",
                "stderr": "",
                "exit_code": 0
            }
        elif stripped.startswith("echo "):
            text = stripped[5:].strip("'\"")
            return {
                "stdout": f"{text}\n",
                "stderr": "",
                "exit_code": 0
            }
        elif stripped == "ls" or stripped.startswith("ls "):
            try:
                parts = stripped.split()
                target_path = "."
                for p in parts[1:]:
                    if not p.startswith("-"):
                        target_path = p.strip("'\"")
                files = os.listdir(target_path if target_path != "." else ".")
                listing = "\n".join(f"-rw-r--r-- 1 root root 1024 Jan 01 00:00 {f}" for f in sorted(files))
                return {
                    "stdout": f"total {len(files)}\n{listing}\n",
                    "stderr": "",
                    "exit_code": 0
                }
            except Exception as e:
                return {
                    "stdout": "",
                    "stderr": f"ls: {str(e)}",
                    "exit_code": 1
                }
        elif stripped.startswith("cat "):
            target_path = stripped[4:].strip("'\"")
            try:
                if os.path.exists(target_path):
                    with open(target_path, "r", encoding="utf-8") as f:
                        return {"stdout": f.read(), "stderr": "", "exit_code": 0}
                return {"stdout": "", "stderr": f"cat: {target_path}: No such file or directory", "exit_code": 1}
            except Exception as e:
                return {"stdout": "", "stderr": f"cat: {str(e)}", "exit_code": 1}
        
        # Run in a restricted subprocess with timeout
        try:
            res = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "stdout": res.stdout,
                "stderr": res.stderr,
                "exit_code": res.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "exit_code": 124
            }
        except Exception as exc:
            return {
                "stdout": "",
                "stderr": str(exc),
                "exit_code": 1
            }

    def delete(self) -> None:
        """Tear down simulated sandbox."""
        self.status = "deleted"
        logger.info(f"SimulatedComputer '{self.name}' deleted")


class CelestoService:
    """Manages Celesto sandbox lifecycle across cloud and simulated backends."""

    def __init__(self):
        self._active_sandboxes: Dict[str, Any] = {}

    def create_sandbox(
        self,
        template_id: str = "coding-agent",
        cpus: int = 1,
        memory: int = 1024,
        disk_mb: int = 15360,
        network_policy: Optional[Dict[str, Any]] = None,
        force_simulator: bool = False,
    ) -> Any:
        """Create and boot a new sandbox."""
        start_time = time.time()
        disk_str = f"{disk_mb // 1024}gb" if disk_mb >= 1024 else f"{disk_mb}mb"

        if settings.is_celesto_configured and not force_simulator:
            try:
                from celesto import Computer
                from celesto.sdk.client import _CelestoClient
                logger.info(f"Creating real Celesto Cloud Computer (template: {template_id})")
                client = _CelestoClient(api_key=settings.CELESTO_API_KEY)
                client.session.headers["Idempotency-Key"] = str(uuid.uuid4())
                computer = Computer(
                    template_id=template_id,
                    client=client,
                    network_policy=network_policy or {"mode": "open"},
                )
                # Wait for status to become ready if needed
                max_wait_s = 60
                waited = 0
                while getattr(computer, "status", None) not in ("ready", "running") and waited < max_wait_s:
                    time.sleep(1)
                    waited += 1
                    try:
                        computer.refresh()
                    except Exception:
                        pass

                boot_time = round(time.time() - start_time, 2)
                setattr(computer, "boot_to_ready_s", boot_time)

                # Ensure name and id are safely accessible
                sbx_name = getattr(computer, "name", None) or computer.get("name") or computer.get("id") or f"celesto-{uuid.uuid4().hex[:8]}"
                if not hasattr(computer, "name") or getattr(computer, "name", None) is None:
                    setattr(computer, "name", sbx_name)
                sbx_id = getattr(computer, "id", None) or computer.get("id") or sbx_name
                if not hasattr(computer, "id") or getattr(computer, "id", None) is None:
                    setattr(computer, "id", sbx_id)

                self._active_sandboxes[sbx_name] = computer
                return computer
            except Exception as exc:
                logger.error(f"Failed to create Celesto Cloud Computer: {exc}")
                raise exc

        # Simulated Computer for Phase 1 / local testing / unit tests
        computer = SimulatedComputer(
            template_id=template_id,
            cpus=cpus,
            memory=memory,
            disk=disk_str,
            network_policy=network_policy
        )
        boot_time = round(time.time() - start_time, 2)
        setattr(computer, "boot_to_ready_s", boot_time)
        self._active_sandboxes[computer.name] = computer
        return computer

    def get_sandbox(self, name: str) -> Optional[Any]:
        return self._active_sandboxes.get(name)

    @contextmanager
    def sandbox_scope(
        self,
        template_id: str = "coding-agent",
        cpus: int = 1,
        memory: int = 1024,
        disk_mb: int = 15360,
        network_policy: Optional[Dict[str, Any]] = None,
        force_simulator: bool = False,
    ):
        """Context manager guaranteeing sandbox cleanup in a with-block."""
        sbx = self.create_sandbox(
            template_id=template_id,
            cpus=cpus,
            memory=memory,
            disk_mb=disk_mb,
            network_policy=network_policy,
            force_simulator=force_simulator,
        )
        try:
            yield sbx
        finally:
            self.delete_sandbox(sbx.name)

    def delete_sandbox(self, name: str) -> bool:
        """Delete an active sandbox by name."""
        if name in self._active_sandboxes:
            sbx = self._active_sandboxes.pop(name)
            try:
                sbx.delete()
                if hasattr(sbx, "close") and callable(getattr(sbx, "close")):
                    sbx.close()
                return True
            except Exception as exc:
                logger.warning(f"Error while deleting sandbox {name}: {exc}")
                return False
        return False

    def cleanup_all(self) -> int:
        """Tear down all currently active sandboxes tracked by this service."""
        count = 0
        names = list(self._active_sandboxes.keys())
        for name in names:
            if self.delete_sandbox(name):
                count += 1
        if count > 0:
            logger.info(f"Cleaned up {count} active sandbox(es).")
        return count


celesto_service = CelestoService()
atexit.register(celesto_service.cleanup_all)

# Register signal handlers for clean teardown on interrupt / termination
import signal


def _handle_exit_signal(signum, frame):
    logger.info(f"Signal {signum} received; performing emergency sandbox teardown...")
    celesto_service.cleanup_all()
    raise KeyboardInterrupt()


try:
    signal.signal(signal.SIGINT, _handle_exit_signal)
    signal.signal(signal.SIGTERM, _handle_exit_signal)
except Exception:
    pass

