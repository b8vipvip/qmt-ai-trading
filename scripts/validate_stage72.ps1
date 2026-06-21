$ErrorActionPreference = "Continue"
$LogDir = "validation_logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogPath = Join-Path $LogDir "stage72_validation_$Stamp.log"
$script:Failures = 0
function Write-Log { param([string]$Message) $Message | Tee-Object -FilePath $LogPath -Append }
function Run-Step { param([string]$Name,[string[]]$Command) Write-Log "=== $Name ==="; Write-Log ("COMMAND: " + ($Command -join " ")); & $Command[0] @($Command[1..($Command.Length-1)]) 2>&1 | Tee-Object -FilePath $LogPath -Append; $code=$LASTEXITCODE; Write-Log "EXIT_CODE=$code"; if($code -ne 0){$script:Failures += 1} }
function Print-File { param([string]$Path) Write-Log "=== PRINT $Path ==="; if(Test-Path $Path){ Get-Content -LiteralPath $Path -Encoding UTF8 | Tee-Object -FilePath $LogPath -Append } else { Write-Log "MISSING: $Path"; $script:Failures += 1 } }
function Check-NoBackup { param([string]$Dir,[string]$Pattern,[string]$Label) Write-Log "=== Check-NoBackup $Label ==="; $items=Get-ChildItem -Path $Dir -Filter $Pattern -ErrorAction SilentlyContinue; if($items){ $items | ForEach-Object { Write-Log $_.FullName }; $script:Failures += 1 } else { Write-Log "No backup files found for $Label" } }
function Clean-PythonCache { Write-Log "=== Clean-PythonCache ==="; Get-ChildItem -Path . -Directory -Recurse -Filter __pycache__ -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; Get-ChildItem -Path . -File -Recurse -Include *.pyc,*.pyo -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue; Write-Log "Python cache cleaned" }
Run-Step "compileall" @("py","-m","compileall","-q","qmt_ai_trading")
Run-Step "pytest stage68" @("py","-m","pytest","tests/test_local_console_refresh_stage68.py")
Run-Step "pytest stage69" @("py","-m","pytest","tests/test_local_console_grouping_stage69.py")
Run-Step "pytest stage70" @("py","-m","pytest","tests/test_local_console_drilldown_stage70.py")
Run-Step "pytest stage71" @("py","-m","pytest","tests/test_local_console_review_stage71.py")
Run-Step "pytest stage72" @("py","-m","pytest","tests/test_local_console_acceptance_stage72.py")
Run-Step "run stage72 acceptance" @("py","scripts/run_local_console_ui_acceptance.py","--repo-root",".","--output-dir","local_console_acceptance_stage72","--review-dir","local_console_review_stage71","--drilldown-dir","local_console_drilldown_stage70","--grouping-dir","local_console_grouping_stage69","--refresh-dir","local_console_refresh_stage68","--preview-dir","local_console_preview_stage67","--binding-dir","local_console_binding_stage66","--output","local_console_acceptance_stage72/local_console_ui_acceptance_report.md","--json-output","local_console_acceptance_stage72/local_console_ui_acceptance_report.json","--summary-output","local_console_acceptance_stage72/ui_acceptance_summary.md","--summary-json-output","local_console_acceptance_stage72/ui_acceptance_summary.json","--page-output","local_console_acceptance_stage72/page_inventory.md","--page-json-output","local_console_acceptance_stage72/page_inventory.json","--feature-output","local_console_acceptance_stage72/feature_inventory.md","--feature-json-output","local_console_acceptance_stage72/feature_inventory.json","--safety-output","local_console_acceptance_stage72/safety_checklist.md","--safety-json-output","local_console_acceptance_stage72/safety_checklist.json","--open-output","local_console_acceptance_stage72/open_items.md","--open-json-output","local_console_acceptance_stage72/open_items.json","--route-output","local_console_acceptance_stage72/route_coverage.md","--route-json-output","local_console_acceptance_stage72/route_coverage.json","--asset-output","local_console_acceptance_stage72/asset_coverage.md","--asset-json-output","local_console_acceptance_stage72/asset_coverage.json","--conclusion-output","local_console_acceptance_stage72/acceptance_conclusion_draft.md","--conclusion-json-output","local_console_acceptance_stage72/acceptance_conclusion_draft.json","--package-output","local_console_acceptance_stage72/acceptance_package_index.md","--package-json-output","local_console_acceptance_stage72/acceptance_package_index.json","--ui-safety-output","local_console_acceptance_stage72/ui_acceptance_safety_report.md","--ui-safety-json-output","local_console_acceptance_stage72/ui_acceptance_safety_report.json","--plan-output","local_console_acceptance_stage72/next_local_help_docs_plan.md","--plan-json-output","local_console_acceptance_stage72/next_local_help_docs_plan.json")
Print-File "local_console_acceptance_stage72/local_console_ui_acceptance_report.md"
Print-File "local_console_acceptance_stage72/ui_acceptance_summary.md"
Print-File "local_console_acceptance_stage72/page_inventory.md"
Print-File "local_console_acceptance_stage72/feature_inventory.md"
Print-File "local_console_acceptance_stage72/safety_checklist.md"
Print-File "local_console_acceptance_stage72/open_items.md"
Print-File "local_console_acceptance_stage72/route_coverage.md"
Print-File "local_console_acceptance_stage72/asset_coverage.md"
Print-File "local_console_acceptance_stage72/acceptance_conclusion_draft.md"
Print-File "local_console_acceptance_stage72/acceptance_package_index.md"
Print-File "local_console_acceptance_stage72/ui_acceptance_safety_report.md"
Print-File "local_console_acceptance_stage72/next_local_help_docs_plan.md"
Run-Step "roadmap plan" @("py","scripts/check_stage53_roadmap_plan.py")
Check-NoBackup "scripts" "validate_stage71.ps1.bak_stage71fix_*" "Stage71 validate"
Check-NoBackup "scripts" "validate_stage72.ps1.bak_stage72fix_*" "Stage72 validate"
Run-Step "daily stage72" @("py","scripts/run_daily_pipeline.py","--cache-root","market_data_test_stage72","--research-start","2026-03-21","--research-end","2026-06-18","--research-frequency","1d","--min-bars","40","--cached-strategy-top-n","2","--enable-local-console-ui-acceptance","--local-console-ui-acceptance-output-dir","local_console_acceptance_stage72")
Run-Step "scheduled stage72" @("py","scripts/run_scheduled_daily_pipeline.py","--warmup-universe","--warmup-provider","mock","--universe-lookback-days","90","--warmup-frequency","1d","--cache-root","market_data_test_stage72","--data-source-mode","cached_real_first","--research-start","2026-03-21","--research-end","2026-06-18","--research-frequency","1d","--min-bars","40","--cached-strategy-top-n","2","--enable-local-console-ui-acceptance","--local-console-ui-acceptance-output-dir","local_console_acceptance_stage72")
Run-Step "register preview" @("py","scripts/register_daily_pipeline_task.py","--enable-local-console-ui-acceptance","--local-console-ui-acceptance-output-dir","local_console_acceptance","--time","15:30")
Clean-PythonCache
Write-Log "sync_all.ps1 -Mode scan"
Run-Step "sync scan" @("powershell","-ExecutionPolicy","Bypass","-File","./scripts/sync_all.ps1","-Mode","scan")
Run-Step "sync status" @("powershell","-ExecutionPolicy","Bypass","-File","./scripts/sync_all.ps1","-Mode","status")
Write-Log "TOTAL_FAILURES=$script:Failures"
exit $script:Failures
