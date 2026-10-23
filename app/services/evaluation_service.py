"""Evaluation harness for running 20 sandbox evaluations and concurrency benchmarks."""
import statistics
import time
from typing import List, Dict, Any


def calculate_evaluation_metrics(runs_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate statistical metrics for evaluation runs, robust to empty, partial, and failed runs."""
    if not runs_data:
        return {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "success_rate": 0.0,
            "median_wall_clock_s": 0.0,
            "p90_wall_clock_s": 0.0,
            "mean_boot_to_ready_s": 0.0,
            "total_cost_usd": 0.0
        }

    total = len(runs_data)
    successes = sum(
        1 for r in runs_data 
        if r.get("status") == "completed" or r.get("success") is True
    )

    def _safe_float(val: Any) -> float:
        if val is None:
            return 0.0
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    wall_clocks = [_safe_float(r.get("wall_clock_s")) for r in runs_data]
    boots = [_safe_float(r.get("boot_to_ready_s")) for r in runs_data]
    costs = [_safe_float(r.get("cost_usd")) for r in runs_data]

    wall_clocks_sorted = sorted(wall_clocks)
    p90_idx = int(0.9 * len(wall_clocks_sorted))
    p90 = wall_clocks_sorted[min(p90_idx, len(wall_clocks_sorted) - 1)] if wall_clocks_sorted else 0.0
    median_val = statistics.median(wall_clocks) if wall_clocks else 0.0
    mean_boot = statistics.mean(boots) if boots else 0.0

    return {
        "total_runs": total,
        "successful_runs": successes,
        "failed_runs": total - successes,
        "success_rate": round(successes / total, 4) if total > 0 else 0.0,
        "median_wall_clock_s": round(median_val, 2),
        "p90_wall_clock_s": round(p90, 2),
        "mean_boot_to_ready_s": round(mean_boot, 2),
        "total_cost_usd": round(sum(costs), 5),
    }
