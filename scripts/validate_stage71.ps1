$ErrorActionPreference = "Continue"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RepoRoot
$LogDir = "validation_logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogPath = Join-Path $LogDir "stage71_validation_$Stamp.log"
$script:Failed = $false
function Write-LogLine { param([string]$Text) $Text | Tee-Object -FilePath $LogPath -Append }
function Run-Logged { param([string]$FilePath, [string[]]$Arguments, [switch]$ContinueOnError) Write-LogLine "COMMAND: $FilePath $($Arguments -join ' ')"; $stdout = Join-Path $LogDir "stage71_stdout_$Stamp.txt"; $stderr = Join-Path $LogDir "stage71_stderr_$Stamp.txt"; & $FilePath @Arguments 1> $stdout 2> $stderr; $code = $LASTEXITCODE; Write-LogLine "STDOUT:"; Get-Content -Path $stdout -Encoding UTF8 | Tee-Object -FilePath $LogPath -Append; Write-LogLine "STDERR:"; Get-Content -Path $stderr -Encoding UTF8 | Tee-Object -FilePath $LogPath -Append; Write-LogLine "EXIT_CODE: $code"; if ($code -ne 0) { $script:Failed = $true; if (-not $ContinueOnError) { Write-LogLine "FAILED COMMAND" } }; return $code }
function Print-File { param([string]$Path) Write-LogLine "PRINT_FILE: $Path"; if (Test-Path $Path) { Get-Content -Path $Path -Encoding UTF8 | Tee-Object -FilePath $LogPath -Append } else { Write-LogLine "MISSING_FILE: $Path"; $script:Failed = $true } }
function Check-NoBackup { param([string]$Directory, [string]$Pattern, [string]$Label) $items = Get-ChildItem -Path $Directory -Filter $Pattern -File -ErrorAction SilentlyContinue; if ($items.Count -gt 0) { Write-LogLine "BACKUP_FOUND: $Label $Pattern"; $script:Failed = $true } else { Write-LogLine "NO_BACKUP_FOUND: $Label $Pattern" } }
function Clean-PythonCache { Write-LogLine "Clean-PythonCache start"; Get-ChildItem -Path . -Directory -Recurse -Filter __pycache__ -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; Get-ChildItem -Path . -File -Recurse -Include *.pyc,*.pyo -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue; Write-LogLine "Clean-PythonCache done" }
Run-Logged py @("-m", "compileall", "-q", "qmt_ai_trading")
$tests = @("tests/test_local_console_drilldown_stage70.py", "tests/test_local_console_review_stage71.py")
foreach ($t in $tests) { Run-Logged py @("-m", "pytest", $t) }
Run-Logged py @("scripts\run_local_console_review_workbench.py", "--repo-root", ".", "--output-dir", "local_console_review_stage71", "--drilldown-dir", "local_console_drilldown_stage70", "--grouping-dir", "local_console_grouping_stage69", "--refresh-dir", "local_console_refresh_stage68", "--preview-dir", "local_console_preview_stage67", "--binding-dir", "local_console_binding_stage66", "--output", "local_console_review_stage71\local_console_review_workbench_report.md", "--json-output", "local_console_review_stage71\local_console_review_workbench_report.json", "--manifest-output", "local_console_review_stage71\review_manifest.md", "--manifest-json-output", "local_console_review_stage71\review_manifest.json", "--checklist-output", "local_console_review_stage71\review_checklist.md", "--checklist-json-output", "local_console_review_stage71\review_checklist.json", "--notes-output", "local_console_review_stage71\review_notes_template.md", "--notes-json-output", "local_console_review_stage71\review_notes_template.json", "--confirmation-output", "local_console_review_stage71\local_confirmation_checklist.md", "--confirmation-json-output", "local_console_review_stage71\local_confirmation_checklist.json", "--package-output", "local_console_review_stage71\review_package_index.md", "--package-json-output", "local_console_review_stage71\review_package_index.json", "--safety-output", "local_console_review_stage71\review_safety_report.md", "--safety-json-output", "local_console_review_stage71\review_safety_report.json", "--plan-output", "local_console_review_stage71\next_ui_acceptance_summary_plan.md", "--plan-json-output", "local_console_review_stage71\next_ui_acceptance_summary_plan.json") -ContinueOnError
Print-File "local_console_review_stage71\local_console_review_workbench_report.md"
Print-File "local_console_review_stage71\review_manifest.md"
Print-File "local_console_review_stage71\review_checklist.md"
Print-File "local_console_review_stage71\review_notes_template.md"
Print-File "local_console_review_stage71\local_confirmation_checklist.md"
Print-File "local_console_review_stage71\review_package_index.md"
Print-File "local_console_review_stage71\review_safety_report.md"
Print-File "local_console_review_stage71\next_ui_acceptance_summary_plan.md"
Run-Logged py @("scripts\check_stage53_roadmap_plan.py")
Check-NoBackup "scripts" "validate_stage70.ps1.bak_stage70fix_*" "Stage70 validate"
Check-NoBackup "scripts" "validate_stage71.ps1.bak_stage71fix_*" "Stage71 validate"
Run-Logged py @("scripts\run_daily_pipeline.py", "--cache-root", "market_data_test_stage71", "--research-start", "2026-03-21", "--research-end", "2026-06-18", "--research-frequency", "1d", "--min-bars", "40", "--cached-strategy-top-n", "2", "--enable-local-console-review-workbench", "--local-console-review-workbench-output-dir", "local_console_review_stage71")
Run-Logged py @("scripts\run_scheduled_daily_pipeline.py", "--warmup-universe", "--warmup-provider", "mock", "--universe-lookback-days", "90", "--warmup-frequency", "1d", "--cache-root", "market_data_test_stage71", "--data-source-mode", "cached_real_first", "--research-start", "2026-03-21", "--research-end", "2026-06-18", "--research-frequency", "1d", "--min-bars", "40", "--cached-strategy-top-n", "2", "--enable-local-console-review-workbench", "--local-console-review-workbench-output-dir", "local_console_review_stage71")
Run-Logged py @("scripts\register_daily_pipeline_task.py", "--enable-local-console-review-workbench", "--local-console-review-workbench-output-dir", "local_console_review", "--time", "15:30")
Clean-PythonCache
Run-Logged powershell @("-ExecutionPolicy", "Bypass", "-File", ".\scripts\sync_all.ps1", "-Mode", "scan")
Run-Logged powershell @("-ExecutionPolicy", "Bypass", "-File", ".\scripts\sync_all.ps1", "-Mode", "status")
if ($script:Failed) { Write-LogLine "STAGE71_VALIDATION_RESULT: FAIL"; exit 1 }
Write-LogLine "STAGE71_VALIDATION_RESULT: PASS"
exit 0
