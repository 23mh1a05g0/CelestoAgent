# verify_submission.ps1
# Celesto Agent Submission Verification Script

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "    Celesto AI Agent Hackathon Submission Verifier       " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$allPassed = $true

# 1. Verify Mandatory Report Files
$mandatoryReports = @(
    "reports/problem.json",
    "reports/capabilities.json",
    "reports/lifecycle.json",
    "reports/reliability.json",
    "reports/postmortem.md",
    "reports/containment.json",
    "reports/failure_policy.json",
    "reports/failure_trace.jsonl",
    "reports/concurrency.json"
)

Write-Host "`n[1] Verifying Mandatory Report Files..." -ForegroundColor Cyan
foreach ($report in $mandatoryReports) {
    if (Test-Path $report) {
        Write-Host "  [PASS] $report" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] Missing required report: $report" -ForegroundColor Red
        $allPassed = $false
    }
}

# 2. Run Test Suite
Write-Host "`n[2] Executing Full Pytest Suite..." -ForegroundColor Cyan
$testOutput = & .\.venv\Scripts\python.exe -m pytest tests -v 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [PASS] Pytest suite executed cleanly (All tests passed)" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Pytest suite encountered failures" -ForegroundColor Red
    $allPassed = $false
}

# 3. Secret Leak Scanner
Write-Host "`n[3] Scanning for Accidental Secret Leaks..." -ForegroundColor Cyan
$leaksFound = $false
$trackedFiles = Get-ChildItem -Recurse -File -Exclude "*.pyc", "*.whl", "*.vhdx", ".venv"
foreach ($f in $trackedFiles) {
    if ($f.FullName -like "*\.git\*" -or $f.FullName -like "*\.venv\*" -or $f.Name -eq ".env") { continue }
    if ($content -match "sk-[a-zA-Z0-9]{20,}" -or $content -match "celesto_key_[a-zA-Z0-9]{16,}" -or $content -match "cel_[a-zA-Z0-9_\-]{20,}") {
        Write-Host "  [ALERT] Potential secret leaked in $($f.FullName)" -ForegroundColor Red
        $leaksFound = $true
        $allPassed = $false
    }
}
if (-not $leaksFound) {
    Write-Host "  [PASS] Clean scan - no exposed API secrets detected" -ForegroundColor Green
}

# Final Verdict
Write-Host "`n==========================================================" -ForegroundColor Cyan
if ($allPassed) {
    Write-Host "   SUBMISSION VERIFICATION: ALL GATES PASSED (OK)        " -ForegroundColor Green
} else {
    Write-Host "   SUBMISSION VERIFICATION: ISSUES DETECTED              " -ForegroundColor Yellow
}
Write-Host "==========================================================" -ForegroundColor Cyan
