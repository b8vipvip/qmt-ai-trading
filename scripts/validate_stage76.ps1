$ErrorActionPreference = "Continue"
$LogDir = "validation_logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogPath = Join-Path $LogDir "stage76_validation_$Stamp.log"
$script:Failures = 0
function Write-Log { param([string]$Message) $Message | Tee-Object -FilePath $LogPath -Append }
function Run-Step { param([string]$Name, [string[]]$Command)
  Write-Log "=== $Name ==="
  Write-Log ("COMMAND: " + ($Command -join " "))
  & $Command[0] $Command[1..($Command.Count - 1)] 2>&1 | Tee-Object -FilePath $LogPath -Append
  $Code = $LASTEXITCODE
  Write-Log "EXIT_CODE: $Code"
  if ($Code -ne 0) { $script:Failures += 1 }
}
function Print-File { param([string]$Path)
  Write-Log "=== Print-File $Path ==="
  if (Test-Path $Path) { Get-Content -Encoding UTF8 -Path $Path | Tee-Object -FilePath $LogPath -Append } else { Write-Log "MISSING: $Path"; $script:Failures += 1 }
}
function Check-NoBackup { param([string]$Dir,[string]$Pattern,[string]$Label)
  Write-Log "=== Check-NoBackup $Label ==="
  $Found = Get-ChildItem -Path $Dir -Filter $Pattern -File -ErrorAction SilentlyContinue
  if ($Found) { $Found | ForEach-Object { Write-Log $_.FullName }; $script:Failures += 1 } else { Write-Log "No backup files found for $Label" }
}
function Clean-PythonCache {
  Write-Log "=== Clean-PythonCache ==="
  Get-ChildItem -Path . -Directory -Filter __pycache__ -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
  Get-ChildItem -Path . -File -Include *.pyc,*.pyo -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
}
Run-Step "compileall" @("py","-m","compileall","-q","qmt_ai_trading")
Run-Step "pytest stage68" @("py","-m","pytest","tests/test_local_console_refresh_stage68.py")
Run-Step "pytest stage69" @("py","-m","pytest","tests/test_local_console_grouping_stage69.py")
Run-Step "pytest stage70" @("py","-m","pytest","tests/test_local_console_drilldown_stage70.py")
Run-Step "pytest stage71" @("py","-m","pytest","tests/test_local_console_review_stage71.py")
Run-Step "pytest stage72" @("py","-m","pytest","tests/test_local_console_acceptance_stage72.py")
Run-Step "pytest stage73" @("py","-m","pytest","tests/test_local_console_help_stage73.py")
Run-Step "pytest stage74" @("py","-m","pytest","tests/test_local_console_demo_stage74.py")
Run-Step "pytest stage75" @("py","-m","pytest","tests/test_ui_productization_closure_stage75.py")
Run-Step "pytest stage76" @("py","-m","pytest","tests/test_stage76_roadmap_review.py")
Run-Step "generate stage76" @("py","scripts/run_stage76_roadmap_review.py","--repo-root",".","--output-dir","stage76_roadmap_review","--closure-dir","local_console_closure_stage75","--demo-dir","local_console_demo_stage74","--help-dir","local_console_help_stage73","--acceptance-dir","local_console_acceptance_stage72","--review-dir","local_console_review_stage71","--output","stage76_roadmap_review/stage76_roadmap_review_report.md","--json-output","stage76_roadmap_review/stage76_roadmap_review_report.json","--completed-output","stage76_roadmap_review/completed_stage_summary.md","--completed-json-output","stage76_roadmap_review/completed_stage_summary.json","--ui-output","stage76_roadmap_review/ui_productization_recap.md","--ui-json-output","stage76_roadmap_review/ui_productization_recap.json","--architecture-output","stage76_roadmap_review/architecture_alignment_review.md","--architecture-json-output","stage76_roadmap_review/architecture_alignment_review.json","--safety-output","stage76_roadmap_review/safety_boundary_review.md","--safety-json-output","stage76_roadmap_review/safety_boundary_review.json","--data-output","stage76_roadmap_review/data_quality_gap_review.md","--data-json-output","stage76_roadmap_review/data_quality_gap_review.json","--trading-output","stage76_roadmap_review/trading_readiness_gap_review.md","--trading-json-output","stage76_roadmap_review/trading_readiness_gap_review.json","--ui-maturity-output","stage76_roadmap_review/ui_maturity_review.md","--ui-maturity-json-output","stage76_roadmap_review/ui_maturity_review.json","--blockers-output","stage76_roadmap_review/live_readiness_blockers.md","--blockers-json-output","stage76_roadmap_review/live_readiness_blockers.json","--next-output","stage76_roadmap_review/next_roadmap_plan.md","--next-json-output","stage76_roadmap_review/next_roadmap_plan.json","--stage77-output","stage76_roadmap_review/stage77_plan.md","--stage77-json-output","stage76_roadmap_review/stage77_plan.json")
Print-File "stage76_roadmap_review/stage76_roadmap_review_report.md"
Print-File "stage76_roadmap_review/completed_stage_summary.md"
Print-File "stage76_roadmap_review/ui_productization_recap.md"
Print-File "stage76_roadmap_review/architecture_alignment_review.md"
Print-File "stage76_roadmap_review/safety_boundary_review.md"
Print-File "stage76_roadmap_review/data_quality_gap_review.md"
Print-File "stage76_roadmap_review/trading_readiness_gap_review.md"
Print-File "stage76_roadmap_review/ui_maturity_review.md"
Print-File "stage76_roadmap_review/live_readiness_blockers.md"
Print-File "stage76_roadmap_review/next_roadmap_plan.md"
Print-File "stage76_roadmap_review/stage77_plan.md"
Run-Step "roadmap stage53 check" @("py","scripts/check_stage53_roadmap_plan.py")
Check-NoBackup "scripts" "validate_stage75.ps1.bak_stage75fix_*" "Stage75 validate"
Check-NoBackup "scripts" "validate_stage76.ps1.bak_stage76fix_*" "Stage76 validate"
Clean-PythonCache
Run-Step "sync scan" @("powershell","-ExecutionPolicy","Bypass","-File","./scripts/sync_all.ps1","-Mode","scan")
Run-Step "sync status" @("powershell","-ExecutionPolicy","Bypass","-File","./scripts/sync_all.ps1","-Mode","status")
Clean-PythonCache
if ($script:Failures -ne 0) { Write-Log "FAILED: $script:Failures"; exit 1 }
Write-Log "PASSED"
exit 0
