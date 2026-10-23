"""Unit tests for evaluation math and statistical calculations."""
import pytest
from app.services.evaluation_service import calculate_evaluation_metrics


def test_calculate_evaluation_metrics_empty():
    metrics = calculate_evaluation_metrics([])
    assert metrics["total_runs"] == 0
    assert metrics["success_rate"] == 0.0


def test_calculate_evaluation_metrics_normal():
    sample_runs = [
        {"status": "completed", "wall_clock_s": 10.0, "boot_to_ready_s": 2.0, "cost_usd": 0.001},
        {"status": "completed", "wall_clock_s": 12.0, "boot_to_ready_s": 2.5, "cost_usd": 0.0012},
        {"status": "completed", "wall_clock_s": 14.0, "boot_to_ready_s": 3.0, "cost_usd": 0.0014},
        {"status": "completed", "wall_clock_s": 16.0, "boot_to_ready_s": 2.2, "cost_usd": 0.0016},
        {"status": "failed", "wall_clock_s": 20.0, "boot_to_ready_s": 2.8, "cost_usd": 0.002},
    ]
    metrics = calculate_evaluation_metrics(sample_runs)
    assert metrics["total_runs"] == 5
    assert metrics["successful_runs"] == 4
    assert metrics["failed_runs"] == 1
    assert metrics["success_rate"] == 0.8
    assert metrics["median_wall_clock_s"] == 14.0
    assert metrics["mean_boot_to_ready_s"] == 2.5
    assert metrics["total_cost_usd"] == 0.0072


def test_calculate_evaluation_metrics_partial_and_none():
    partial_runs = [
        {"status": "completed", "wall_clock_s": 15.0, "boot_to_ready_s": 2.0, "cost_usd": 0.001},
        {"status": "failed", "wall_clock_s": None, "boot_to_ready_s": None, "cost_usd": None},
        {"status": "provisioning", "wall_clock_s": 5.0, "boot_to_ready_s": 2.5},
    ]
    metrics = calculate_evaluation_metrics(partial_runs)
    assert metrics["total_runs"] == 3
    assert metrics["successful_runs"] == 1
    assert metrics["failed_runs"] == 2
    assert metrics["success_rate"] == 0.3333
    assert metrics["total_cost_usd"] == 0.001

