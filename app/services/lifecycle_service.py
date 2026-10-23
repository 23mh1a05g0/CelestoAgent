"""Sandbox lifecycle management and audit service."""
import json
import os
import time
import atexit
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class LifecycleService:
    """Tracks and manages sandbox lifecycles and exports reports/lifecycle.json."""

    VALID_STATES = {
        "created", "booting", "ready", "running",
        "paused", "stopped", "deleted", "failed"
    }

    def __init__(self, report_path: str = "reports/lifecycle.json"):
        self.report_path = report_path
        os.makedirs(os.path.dirname(self.report_path), exist_ok=True)
        self.history: List[Dict[str, Any]] = []
        self._active_sandboxes: Dict[str, Dict[str, Any]] = {}
        # Register process exit hook to alert or cleanup if needed
        atexit.register(self._process_exit_check)

    def record_transition(
        self,
        sandbox_name: str,
        from_state: str,
        to_state: str,
        duration_s: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Record a validated state transition."""
        entry = {
            "sandbox_name": sandbox_name,
            "timestamp": datetime.utcnow().isoformat(),
            "from_state": from_state,
            "to_state": to_state,
            "duration_s": round(duration_s, 4) if duration_s is not None else None,
            "metadata": metadata or {}
        }
        self.history.append(entry)

        if to_state in ("created", "booting", "ready", "running"):
            self._active_sandboxes[sandbox_name] = {
                "state": to_state,
                "updated_at": entry["timestamp"]
            }
        elif to_state in ("deleted", "failed", "stopped") and sandbox_name in self._active_sandboxes:
            self._active_sandboxes.pop(sandbox_name, None)

        logger.info(f"[Lifecycle] Sandbox '{sandbox_name}': {from_state} -> {to_state} ({duration_s}s)")
        return entry

    def get_active_sandboxes(self) -> Dict[str, Dict[str, Any]]:
        return dict(self._active_sandboxes)

    def _process_exit_check(self) -> None:
        if self._active_sandboxes:
            logger.warning(
                f"Process exiting with {len(self._active_sandboxes)} active sandbox tracking entries: "
                f"{list(self._active_sandboxes.keys())}"
            )

    def export_lifecycle_report(self) -> Dict[str, Any]:
        """Generate and save lifecycle.json."""
        report = {
            "supported_states": sorted(list(self.VALID_STATES)),
            "backend": "celesto_cloud_computer",
            "lifecycle_transitions_recorded": len(self.history),
            "active_sandboxes_count": len(self._active_sandboxes),
            "events": self.history[-100:],
            "generated_at": datetime.utcnow().isoformat()
        }
        with open(self.report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        return report


lifecycle_service = LifecycleService()
