# =========================================================================
# Reality Reconstruction Engine (RRE 2.0) - Presentation Showcase Setup
# =========================================================================
Write-Host "[RRE 2.0] Initializing Presentation Showcase Case (SEC-2026-SHOWCASE)..." -ForegroundColor Cyan

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path "$RepoRoot\.venv\Scripts\python.exe") {
    & "$RepoRoot\.venv\Scripts\python.exe" "testing\run_presentation_case.py"
} else {
    python "testing\run_presentation_case.py"
}

Write-Host "`n[RRE 2.0] Presentation Showcase Case Ready!" -ForegroundColor Green
