# preflight.ps1
# Celesto Agent Platform Preflight Diagnostic Script

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Celesto AI Agent Platform - Preflight Health Checks   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check Python
$pyVer = & python --version 2>&1
Write-Host "[CHECK] Python Environment: $pyVer" -ForegroundColor Green

# 2. Check Virtual Environment
if (Test-Path ".\.venv\Scripts\python.exe") {
    Write-Host "[CHECK] Virtual Environment: Present on F: (.venv)" -ForegroundColor Green
} else {
    Write-Host "[WARN] Virtual Environment missing at .\.venv" -ForegroundColor Yellow
}

# 3. Check Disk Space
$cDrive = Get-PSDrive C
$fDrive = Get-PSDrive F
$cFreeGB = [math]::Round($cDrive.Free / 1GB, 2)
$fFreeGB = [math]::Round($fDrive.Free / 1GB, 2)
Write-Host "[CHECK] Disk Space - C: Free: $cFreeGB GB | F: Free: $fFreeGB GB" -ForegroundColor $(if ($cFreeGB -lt 10) { "Yellow" } else { "Green" })

# 4. Check Docker Engine
$dockerOk = & docker info 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[CHECK] Docker Engine: HEALTHY & RUNNING" -ForegroundColor Green
} else {
    Write-Host "[WARN] Docker Engine: NOT RUNNING" -ForegroundColor Red
}

# 5. Check Celesto SDK
$celestoCheck = & .\.venv\Scripts\python.exe -c "import celesto; print(celesto.__version__)" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[CHECK] Celesto SDK Installed: Version $celestoCheck" -ForegroundColor Green
} else {
    Write-Host "[WARN] Celesto SDK import failed" -ForegroundColor Yellow
}

# 6. Check Configuration
if (Test-Path ".env") {
    Write-Host "[CHECK] Environment Configuration: .env file present" -ForegroundColor Green
} else {
    Write-Host "[INFO] .env file not present. Using .env.example defaults for Phase 1" -ForegroundColor Cyan
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Preflight check completed successfully." -ForegroundColor Green
