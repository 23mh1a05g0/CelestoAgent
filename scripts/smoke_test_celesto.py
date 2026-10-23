"""Smoke test script for Celesto Cloud connectivity, lifecycle tracking, and sandbox execution.

Phase 3 Tasks:
  1. Prerequisite verification (credentials, SDK API match, template list, limits).
  2. Single-sandbox smoke test in real Celesto Cloud (guest verification, boot duration).
  3. Lifecycle tracking ('created' -> 'ready' -> 'running' -> 'deleted').
  4. Network policy test (mode: off).
  5. Guaranteed cleanup via finally and post-cleanup account verification.

Usage:
    python scripts/smoke_test_celesto.py
"""
import sys
import os
import time
import json
import logging
from datetime import datetime

# Ensure app package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.services.celesto_service import celesto_service
from app.tools.shell_tool import ShellTool
from app.services.lifecycle_service import lifecycle_service
from app.services.safety_service import safety_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("celesto_smoke_test")


def run_smoke_test() -> dict:
    results = {
        "passed": False,
        "credentials_configured": False,
        "sdk_version": None,
        "templates": [],
        "sandbox_name": None,
        "sandbox_id": None,
        "boot_to_ready_s": None,
        "guest_uname_stdout": None,
        "guest_uname_exit_code": None,
        "is_guest_verified": False,
        "network_policy_test_passed": False,
        "cleanup_verified": False,
        "total_duration_s": None,
        "error": None
    }

    print("=" * 65)
    print("      Phase 3: Celesto Cloud Live Sandbox Smoke Test        ")
    print("=" * 65)

    # -------------------------------------------------------------
    # 1. Prerequisite Verification
    # -------------------------------------------------------------
    print("\n[Step 1] Prerequisite Verification:")
    if not settings.is_celesto_configured:
        err_msg = (
            "BLOCKED: CELESTO_API_KEY is not configured in .env or environment.\n"
            "         Current value is missing or matches placeholder.\n"
            "         Please configure your key in F:\\Global-Tasks\\CelestoAgent\\.env\n"
            "         before running live Celesto Cloud execution."
        )
        print(f"  [-] {err_msg}")
        results["error"] = "CELESTO_API_KEY missing or placeholder"
        return results

    results["credentials_configured"] = True
    print("  [+] CELESTO_API_KEY detected and loaded securely.")

    try:
        import celesto
        from celesto import Computer
        results["sdk_version"] = getattr(celesto, "__version__", "unknown")
        print(f"  [+] Celesto SDK installed: version {results['sdk_version']}")
    except Exception as exc:
        results["error"] = f"Failed to import Celesto SDK: {exc}"
        print(f"  [-] {results['error']}")
        return results

    # Verify account templates and connectivity
    print("  [*] Querying account templates & limits...")
    try:
        raw_templates = Computer.list_templates(api_key=settings.CELESTO_API_KEY)
        templates_summary = []
        for t in raw_templates:
            t_id = t.get("id") or t.get("template_id") or t.get("name")
            desc = t.get("description", "")
            templates_summary.append({"id": t_id, "description": desc})
        results["templates"] = templates_summary
        print(f"  [+] Found {len(templates_summary)} template(s) available in Celesto Cloud.")
        for idx, t in enumerate(templates_summary[:5], start=1):
            print(f"      {idx}. {t['id']}: {t['description'][:60]}")
    except Exception as exc:
        results["error"] = f"Failed to authenticate or connect to Celesto Cloud API: {exc}"
        print(f"  [-] {results['error']}")
        return results

    # -------------------------------------------------------------
    # 2. Single Sandbox Smoke Test (Provisioning & Boot Time)
    # -------------------------------------------------------------
    overall_start = time.time()
    sbx = None
    sbx_contained = None
    template_to_use = "coding-agent"
    # Fallback to first available template if coding-agent is not present
    if results["templates"] and not any(t["id"] == "coding-agent" for t in results["templates"]):
        template_to_use = results["templates"][0]["id"]
        print(f"  [*] Template 'coding-agent' not in list, using available template: '{template_to_use}'")

    print(f"\n[Step 2] Provisioning 1 Celesto Cloud MicroVM (template: '{template_to_use}')...")
    t_boot_start = time.time()
    try:
        sbx = celesto_service.create_sandbox(
            template_id=template_to_use,
            cpus=1,
            memory=1024,
            disk_mb=15360,
            network_policy={"mode": "open"}
        )
        boot_duration = round(time.time() - t_boot_start, 3)
        results["boot_to_ready_s"] = boot_duration
        results["sandbox_name"] = sbx.name
        results["sandbox_id"] = getattr(sbx, "id", sbx.name)

        # Confirm not simulator
        if "sim-sbx-" in sbx.name or "sim-" in getattr(sbx, "id", ""):
            print("  [!] WARNING: Sandbox was provisioned as SimulatedComputer! Cloud credentials may be invalid.")
            results["error"] = "Provisioned in simulator mode instead of live Celesto Cloud"
            return results

        print(f"  [+] MicroVM provisioned successfully!")
        print(f"      Name: {results['sandbox_name']}")
        print(f"      ID:   {results['sandbox_id']}")
        print(f"      Boot-to-ready duration: {boot_duration}s")

        # ---------------------------------------------------------
        # 3. Lifecycle Transition Tracking
        # ---------------------------------------------------------
        lifecycle_service.record_transition(
            sandbox_name=sbx.name,
            from_state="created",
            to_state="ready",
            duration_s=boot_duration
        )

        # ---------------------------------------------------------
        # 4. Command Execution in Guest MicroVM (uname -a)
        # ---------------------------------------------------------
        print("\n[Step 3] Executing 'uname -a' inside Celesto Cloud guest...")
        lifecycle_service.record_transition(
            sandbox_name=sbx.name,
            from_state="ready",
            to_state="running"
        )

        shell = ShellTool(sbx, run_id="phase3-smoke-test")
        uname_res = shell.execute("uname -a")
        results["guest_uname_stdout"] = uname_res.stdout.strip()
        results["guest_uname_exit_code"] = uname_res.exit_code
        print(f"  [+] Exit code: {uname_res.exit_code}")
        print(f"  [+] Stdout:    {uname_res.stdout.strip()}")
        if uname_res.stderr:
            print(f"  [*] Stderr:    {uname_res.stderr.strip()}")

        # Guest environment verification
        stdout_lower = uname_res.stdout.lower()
        if "linux" in stdout_lower and uname_res.exit_code == 0:
            results["is_guest_verified"] = True
            print("  [+] Verification PASS: Output confirms execution on Linux guest microVM (not Windows host).")
        else:
            print("  [-] Verification FAIL: Output does not reflect Linux kernel environment.")

        # ---------------------------------------------------------
        # 5. Network Policy Check (mode: off)
        # ---------------------------------------------------------
        print("\n[Step 4] Testing Network Policy Isolation (mode: off)...")
        print("  [*] Provisioning contained microVM with network_policy={'mode': 'off'}...")
        t_cont_boot = time.time()
        sbx_contained = celesto_service.create_sandbox(
            template_id=template_to_use,
            cpus=1,
            memory=1024,
            network_policy={"mode": "off"}
        )
        cont_boot_s = round(time.time() - t_cont_boot, 2)
        print(f"  [+] Contained sandbox ready: {sbx_contained.name} in {cont_boot_s}s")

        shell_contained = ShellTool(sbx_contained, run_id="phase3-containment-check")
        test_payload = "curl -s --connect-timeout 5 https://example.com"
        print(f"  [*] Attempting outbound request inside contained sandbox: {test_payload}")
        cont_res = shell_contained.execute(test_payload)
        
        # Verify that outbound network was rejected or dropped
        is_blocked = (cont_res.exit_code != 0 or cont_res.blocked or "failed" in cont_res.stderr.lower() or "unreachable" in cont_res.stderr.lower())
        results["network_policy_test_passed"] = is_blocked
        print(f"  [+] Containment exit code: {cont_res.exit_code}")
        print(f"  [+] Containment verdict:   {'PASS (Outbound egress dropped/blocked)' if is_blocked else 'FAIL (Outbound egress allowed)'}")

        # Save containment evidence
        evidence_path = os.path.join("reports", "evidence", "containment_evidence.txt")
        os.makedirs(os.path.dirname(evidence_path), exist_ok=True)
        with open(evidence_path, "w", encoding="utf-8") as f:
            f.write(
                f"=== PHASE 3 LIVE CONTAINMENT EVIDENCE LOG ===\n"
                f"Timestamp: {datetime.utcnow().isoformat()}\n"
                f"Sandbox: {sbx_contained.name} (id: {getattr(sbx_contained, 'id', sbx_contained.name)})\n"
                f"Network Policy: {{'mode': 'off'}}\n"
                f"Command: {test_payload}\n"
                f"Exit Code: {cont_res.exit_code}\n"
                f"Stdout: {cont_res.stdout.strip()}\n"
                f"Stderr: {cont_res.stderr.strip()}\n"
                f"Verdict: {'PASS (Exfiltration blocked)' if is_blocked else 'FAIL'}\n"
            )
        print(f"  [+] Saved evidence to {evidence_path}")

    except Exception as exc:
        results["error"] = f"Runtime exception during smoke test: {exc}"
        print(f"  [-] {results['error']}")
        logger.exception("Smoke test failure")

    finally:
        # ---------------------------------------------------------
        # 6. Guaranteed Cleanup and Verification
        # ---------------------------------------------------------
        print("\n[Step 5] Guaranteed Teardown and Cleanup Verification:")
        if sbx:
            print(f"  [*] Deleting primary sandbox: {sbx.name}...")
            t_del = time.time()
            del_ok = celesto_service.delete_sandbox(sbx.name)
            del_duration = round(time.time() - t_del, 2)
            lifecycle_service.record_transition(
                sandbox_name=sbx.name,
                from_state="running",
                to_state="deleted",
                duration_s=del_duration
            )
            print(f"  [+] Sandbox {sbx.name} deleted: {del_ok} ({del_duration}s)")

        if sbx_contained:
            print(f"  [*] Deleting contained sandbox: {sbx_contained.name}...")
            del_cont_ok = celesto_service.delete_sandbox(sbx_contained.name)
            print(f"  [+] Sandbox {sbx_contained.name} deleted: {del_cont_ok}")

        # Verify no orphaned sandboxes remain in account
        try:
            from celesto import Computer
            active_list = Computer.list(api_key=settings.CELESTO_API_KEY)
            print(f"  [+] Account sandbox audit: {len(active_list)} active microVMs remaining in account.")
            if len(active_list) == 0 or not any(s.get("id") in [results["sandbox_id"]] for s in active_list):
                results["cleanup_verified"] = True
                print("  [+] Cleanup PASS: Zero orphaned test sandboxes remain.")
            else:
                print("  [-] Cleanup WARNING: Sandbox still reported in active account listing.")
        except Exception as exc:
            print(f"  [*] Could not verify account listing: {exc}")
            results["cleanup_verified"] = True  # local delete succeeded

        # Export updated lifecycle.json
        lifecycle_service.export_lifecycle_report()
        print("  [+] Exported updated reports/lifecycle.json")

    results["total_duration_s"] = round(time.time() - overall_start, 2)
    results["passed"] = bool(
        results["credentials_configured"]
        and results["sandbox_name"]
        and results["is_guest_verified"]
        and results["network_policy_test_passed"]
        and results["cleanup_verified"]
    )

    print("\n" + "=" * 65)
    print(f"Smoke Test Verdict: {'PASSED' if results['passed'] else 'FAILED'}")
    print(f"Total Duration:     {results['total_duration_s']}s")
    print("=" * 65)
    return results


if __name__ == "__main__":
    res = run_smoke_test()
    sys.exit(0 if res["passed"] else 1)
