"""Unit tests for report generation and schema compliance."""
import os
import json
import pytest
from app.services.report_service import ReportService


def test_generate_all_reports(tmp_path):
    report_svc = ReportService(reports_dir=str(tmp_path))
    
    # 1. problem.json
    prob = report_svc.generate_problem_report()
    assert prob["title"]
    assert prob["challenge"]
    assert len(prob["problem_statement"]) > 20
    assert os.path.exists(tmp_path / "problem.json")

    # 2. capabilities.json
    caps = report_svc.generate_capabilities_report()
    assert len(caps["capabilities"]) == 2
    cap_names = [c["name"] for c in caps["capabilities"]]
    assert "safety_hooks" in cap_names
    assert "network_policy" in cap_names
    assert os.path.exists(tmp_path / "capabilities.json")

    # 3. containment.json
    cont = report_svc.generate_containment_report()
    assert cont["containment_test"] == "prompt_injection_exfil"
    assert cont["sandbox_network_mode"] == "off"
    assert cont["exfiltration_prevented"] is True
    assert os.path.exists(tmp_path / "containment.json")

    # 4. postmortem.md
    post = report_svc.generate_postmortem_markdown()
    assert "# Postmortem" in post
    assert "Snapshots vs Fresh Provisioning" in post
    assert os.path.exists(tmp_path / "postmortem.md")

    # 5. concurrency.json
    conc = report_svc.generate_concurrency_report()
    assert conc["concurrency_level"] == 5
    assert conc["completed_jobs"] == 5
    assert os.path.exists(tmp_path / "concurrency.json")


def test_validate_all_reports():
    # Test against the project reports directory
    validation = ReportService(reports_dir="reports").validate_all_reports()
    assert validation["reports_count"] == 9
    assert validation["all_passed"] is True
    for r_name, r_info in validation["details"].items():
        assert r_info["present"] is True, f"Report {r_name} missing"
        assert r_info["valid"] is True, f"Report {r_name} invalid or empty"

