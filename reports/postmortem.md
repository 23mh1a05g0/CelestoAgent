# Postmortem: Sandbox Reliability, Failure Recovery, and Containment

## Executive Summary
During evaluation of autonomous agent workloads in Celesto sandboxes, we tested failure scenarios including deliberate step-7 command failures and exfiltration attempts.

## Root Cause Analysis
- **Step 7 Failure**: Deliberately injected environment disruption testing agent recovery mechanisms.
- **Snapshots vs Fresh Provisioning**: Due to Cloud SDK architecture, microVM snapshotting is unavailable. A fresh-sandbox reprovisioning policy was implemented to guarantee clean state isolation.

## Corrective Actions & Containment
- All failed sandboxes are explicitly destroyed before a retry begins.
- Network isolation policy (`mode: off`) completely neutralizes data exfiltration payloads.
- Pre-execution command policy intercepts critical command patterns before execution.
