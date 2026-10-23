"""Unit tests for recovery policy and trace logging."""
import os
import json
import pytest
from app.services.recovery_service import RecoveryService


def test_recovery_policy_spec_generation(tmp_path):
    spec_path = str(tmp_path / "failure_policy.json")
    trace_path = str(tmp_path / "failure_trace.jsonl")
    
    rec_service = RecoveryService(trace_file_path=trace_path)
    spec = rec_service.export_policy_spec(output_path=spec_path)
    
    assert spec["policy"] == "fresh"
    assert len(spec["rationale"]) >= 200
    assert spec["failure_trigger_step"] == 7
    assert os.path.exists(spec_path)


def test_execute_workflow_with_injected_failure(tmp_path):
    trace_path = str(tmp_path / "failure_trace.jsonl")
    rec_service = RecoveryService(trace_file_path=trace_path)
    
    steps = [
        {"name": f"step_{i}", "command": f"echo 'Executing step {i}'"}
        for i in range(1, 11)
    ]
    
    # Inject failure at step 7 on attempt 1, should recover on attempt 2
    res = rec_service.execute_workflow_with_recovery(
        run_id="test-rec-run-001",
        steps=steps,
        failure_step=7,
        force_simulator=True,
    )
    
    assert res["success"] is True
    assert res["attempts"] == 2
    assert os.path.exists(trace_path)
    
    with open(trace_path, "r", encoding="utf-8") as f:
        events = [json.loads(line) for line in f if line.strip()]
        
    event_names = [e["event"] for e in events]
    assert "step_failure_injected" in event_names
    assert "recovery_triggered" in event_names
    assert "workflow_completed" in event_names
