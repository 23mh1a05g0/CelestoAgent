"""Unit tests for concurrency orchestration and reporting."""
import os
import json
import pytest
from app.services.concurrency_service import ConcurrencyService


def test_concurrency_spec_generation(tmp_path):
    report_file = str(tmp_path / "concurrency.json")
    svc = ConcurrencyService(report_path=report_file)

    spec = svc.generate_concurrency_spec(
        concurrency_level=5,
        scheduling_mode="sequential_batch",
        completed_jobs=5,
        failed_jobs=0,
        wall_clock_s=25.0
    )

    assert spec["concurrency_level"] == 5
    assert spec["completed_jobs"] == 5
    assert spec["failed_jobs"] == 0
    assert "isolation_guarantee" in spec
    assert "hardware_microvm" in spec["isolation_guarantee"]
    assert os.path.exists(report_file)

    with open(report_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["concurrency_level"] == 5


def test_concurrency_batch_execution(tmp_path):
    report_file = str(tmp_path / "concurrency_batch.json")
    svc = ConcurrencyService(report_path=report_file)

    # Execute a small 2-job batch in simulated mode
    res = svc.execute_batch(
        num_jobs=2,
        command="uname -a",
        force_simulator=True
    )

    assert res["concurrency_level"] == 2
    assert res["completed_jobs"] == 2
    assert res["failed_jobs"] == 0
    assert len(res["jobs"]) == 2
    # Verify each job had an independent unique sandbox
    sbx_names = [j["sandbox_name"] for j in res["jobs"]]
    assert len(set(sbx_names)) == 2, "Sandboxes must be uniquely named and isolated per job"
