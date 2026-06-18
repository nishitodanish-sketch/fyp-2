
# ============================================================
#  run_snyk_scan.ps1  -  Full Snyk Static Analysis for FYP2
#  Covers:
#    1. Snyk Code  (SAST - source code vulnerability scan)
#    2. Snyk Open Source (dependency / SCA scan)
# ============================================================

$ProjectRoot = $PSScriptRoot
$Timestamp   = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportDir   = Join-Path $ProjectRoot "snyk_reports"

if (-not (Test-Path $ReportDir)) {
    New-Item -ItemType Directory -Path $ReportDir | Out-Null
}

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  SNYK STATIC SCAN  -  FYP2 Project" -ForegroundColor Cyan
Write-Host "  Time: $(Get-Date)" -ForegroundColor Cyan
Write-Host "  Reports saved to: $ReportDir" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# ──────────────────────────────────────────────────────────────
# STEP 1: Snyk Code (SAST - Code Scanning)
# ──────────────────────────────────────────────────────────────
Write-Host "[ STEP 1/2 ]  Snyk Code Scan (SAST) ..." -ForegroundColor Yellow
Write-Host "  Scanning Python source files for security issues..." -ForegroundColor Gray

$CodeJsonOut = Join-Path $ReportDir "snyk_code_${Timestamp}.json"
$CodeTextOut = Join-Path $ReportDir "snyk_code_${Timestamp}.txt"

# Run code scan - save JSON for processing + plain text for reading
snyk code test --sarif-file-output="$CodeJsonOut" 2>&1 | Tee-Object -FilePath $CodeTextOut

Write-Host ""
if (Test-Path $CodeJsonOut) {
    Write-Host "  [OK] Code scan SARIF saved: $CodeJsonOut" -ForegroundColor Green
} else {
    Write-Host "  [!]  Code scan SARIF not produced (may need Snyk Code enabled in dashboard)" -ForegroundColor Red
}
Write-Host "  [OK] Code scan text saved:  $CodeTextOut" -ForegroundColor Green

# ──────────────────────────────────────────────────────────────
# STEP 2: Snyk Open Source (Dependency / SCA Scan)
# ──────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[ STEP 2/2 ]  Snyk Open Source Dependency Scan ..." -ForegroundColor Yellow
Write-Host "  Scanning requirements.txt for vulnerable packages..." -ForegroundColor Gray

$DepJsonOut  = Join-Path $ReportDir "snyk_deps_${Timestamp}.json"
$DepTextOut  = Join-Path $ReportDir "snyk_deps_${Timestamp}.txt"

# Run dependency scan - JSON + text output
snyk test --file=requirements.txt --package-manager=pip --json-file-output="$DepJsonOut" 2>&1 | Tee-Object -FilePath $DepTextOut

Write-Host ""
if (Test-Path $DepJsonOut) {
    Write-Host "  [OK] Dependency scan JSON saved: $DepJsonOut" -ForegroundColor Green
} else {
    Write-Host "  [!]  Dependency scan JSON not produced" -ForegroundColor Red
}
Write-Host "  [OK] Dependency scan text saved:  $DepTextOut" -ForegroundColor Green

# ──────────────────────────────────────────────────────────────
# SUMMARY
# ──────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  SCAN COMPLETE - Report files:" -ForegroundColor Cyan
Write-Host "  Code (SARIF) : $CodeJsonOut" -ForegroundColor White
Write-Host "  Code (Text)  : $CodeTextOut" -ForegroundColor White
Write-Host "  Deps (JSON)  : $DepJsonOut"  -ForegroundColor White
Write-Host "  Deps (Text)  : $DepTextOut"  -ForegroundColor White
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  TIP: Upload SARIF to GitHub Security > Code Scanning" -ForegroundColor DarkGray
Write-Host "  TIP: View online at https://app.snyk.io" -ForegroundColor DarkGray
Write-Host ""
