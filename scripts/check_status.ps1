# Quick status check script
Write-Host "=== DISK SPACE ===" -ForegroundColor Cyan
Get-PSDrive C, F | ForEach-Object {
    $used = [math]::Round($_.Used/1GB,2)
    $free = [math]::Round($_.Free/1GB,2)
    Write-Host "  $($_.Name): Used=$used GB, Free=$free GB"
}

Write-Host "`n=== DOCKER VHDX ===" -ForegroundColor Cyan
$vhdx = "C:\Users\MY PC\AppData\Local\Docker\wsl\disk\docker_data.vhdx"
if (Test-Path $vhdx) {
    $item = Get-Item $vhdx
    $sizeGB = [math]::Round($item.Length/1GB,2)
    Write-Host "  Location: $vhdx"
    Write-Host "  Size: $sizeGB GB"
} else {
    Write-Host "  VHDX not found at default location on C:"
    # Check if it moved to F:
    $vhdxF = "F:\Docker\data\docker_data.vhdx"
    if (Test-Path $vhdxF) {
        $item = Get-Item $vhdxF
        $sizeGB = [math]::Round($item.Length/1GB,2)
        Write-Host "  Found at: $vhdxF ($sizeGB GB)" -ForegroundColor Green
    }
}

Write-Host "`n=== DOCKER ENGINE ===" -ForegroundColor Cyan
try {
    docker version --format "{{.Server.Version}}" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Docker is running" -ForegroundColor Green
        docker system df
    } else {
        Write-Host "  Docker engine not responding" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  Docker command not available" -ForegroundColor Red
}

Write-Host "`n=== REPORTS ===" -ForegroundColor Cyan
$reports = @(
    "reports/problem.json", "reports/capabilities.json", "reports/lifecycle.json",
    "reports/reliability.json", "reports/postmortem.md", "reports/containment.json",
    "reports/failure_policy.json", "reports/failure_trace.jsonl", "reports/concurrency.json"
)
foreach ($r in $reports) {
    if (Test-Path $r) {
        $size = (Get-Item $r).Length
        Write-Host "  [OK] $r ($size bytes)" -ForegroundColor Green
    } else {
        Write-Host "  [MISSING] $r" -ForegroundColor Red
    }
}

Write-Host "`n=== TESTS ===" -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m pytest tests -v --tb=short 2>&1
