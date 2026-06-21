$ErrorActionPreference = "Continue"
$LogDir = "validation_logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogPath = Join-Path $LogDir "stage75_validation_$Stamp.log"
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
Run-Step "generate stage75" @("py","scripts\run_ui_productization_closure.py","--repo-root",".","--output-dir","local_console_closure_stage75","--demo-dir","local_console_demo_stage74","--help-dir","local_console_help_stage73","--acceptance-dir","local_console_acceptance_stage72","--review-dir","local_console_review_stage71","--drilldown-dir","local_console_drilldown_stage70","--grouping-dir","local_console_grouping_stage69","--refresh-dir","local_console_refresh_stage68","--output","local_console_closure_stage75\ui_productization_closure_report.md","--json-output","local_console_closure_stage75\ui_productization_closure_report.json","--stage-output","local_console_closure_stage75\stage_overview.md","--stage-json-output","local_console_closure_stage75\stage_overview.json","--matrix-output","local_console_closure_stage75\capability_matrix.md","--matrix-json-output","local_console_closure_stage75\capability_matrix.json","--safety-output","local_console_closure_stage75\safety_boundary_table.md","--safety-json-output","local_console_closure_stage75\safety_boundary_table.json","--demo-output","local_console_closure_stage75\readonly_demo_entry.md","--demo-json-output","local_console_closure_stage75\readonly_demo_entry.json","--route-output","local_console_closure_stage75\route_coverage_summary.md","--route-json-output","local_console_closure_stage75\route_coverage_summary.json","--asset-output","local_console_closure_stage75\asset_coverage_summary.md","--asset-json-output","local_console_closure_stage75\asset_coverage_summary.json","--risk-output","local_console_closure_stage75\risk_limitation_summary.md","--risk-json-output","local_console_closure_stage75\risk_limitation_summary.json","--conclusion-output","local_console_closure_stage75\final_acceptance_conclusion_draft.md","--conclusion-json-output","local_console_closure_stage75\final_acceptance_conclusion_draft.json","--future-output","local_console_closure_stage75\future_roadmap_recommendation.md","--future-json-output","local_console_closure_stage75\future_roadmap_recommendation.json","--closure-safety-output","local_console_closure_stage75\closure_safety_report.md","--closure-safety-json-output","local_console_closure_stage75\closure_safety_report.json")
Print-File "local_console_closure_stage75\ui_productization_closure_report.md"
Print-File "local_console_closure_stage75\stage_overview.md"
Print-File "local_console_closure_stage75\capability_matrix.md"
Print-File "local_console_closure_stage75\safety_boundary_table.md"
Print-File "local_console_closure_stage75\readonly_demo_entry.md"
Print-File "local_console_closure_stage75\route_coverage_summary.md"
Print-File "local_console_closure_stage75\asset_coverage_summary.md"
Print-File "local_console_closure_stage75\risk_limitation_summary.md"
Print-File "local_console_closure_stage75\final_acceptance_conclusion_draft.md"
Print-File "local_console_closure_stage75\future_roadmap_recommendation.md"
Print-File "local_console_closure_stage75\closure_safety_report.md"
Run-Step "roadmap plan" @("py","scripts\check_stage53_roadmap_plan.py")
Check-NoBackup "scripts" "validate_stage74.ps1.bak_stage74fix_*" "Stage74 validate"
Check-NoBackup "scripts" "validate_stage75.ps1.bak_stage75fix_*" "Stage75 validate"
Run-Step "daily closure" @("py","scripts\run_daily_pipeline.py","--cache-root","market_data_test_stage75","--research-start","2026-03-21","--research-end","2026-06-18","--research-frequency","1d","--min-bars","40","--cached-strategy-top-n","2","--enable-ui-productization-closure","--ui-productization-closure-output-dir","local_console_closure_stage75")
Run-Step "scheduled closure" @("py","scripts\run_scheduled_daily_pipeline.py","--warmup-universe","--warmup-provider","mock","--universe-lookback-days","90","--warmup-frequency","1d","--cache-root","market_data_test_stage75","--data-source-mode","cached_real_first","--research-start","2026-03-21","--research-end","2026-06-18","--research-frequency","1d","--min-bars","40","--cached-strategy-top-n","2","--enable-ui-productization-closure","--ui-productization-closure-output-dir","local_console_closure_stage75")
Run-Step "register preview" @("py","scripts\register_daily_pipeline_task.py","--enable-ui-productization-closure","--ui-productization-closure-output-dir","local_console_closure","--time","15:30")
Clean-PythonCache
Run-Step "sync scan" @("powershell","-ExecutionPolicy","Bypass","-File",".\scripts\sync_all.ps1","-Mode","scan")
Run-Step "sync status" @("powershell","-ExecutionPolicy","Bypass","-File",".\scripts\sync_all.ps1","-Mode","status")
if ($script:Failures -ne 0) { exit 1 }
exit 0
