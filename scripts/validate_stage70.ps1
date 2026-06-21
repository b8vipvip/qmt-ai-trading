$ErrorActionPreference = "Continue"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RepoRoot
$LogDir = "validation_logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogPath = Join-Path $LogDir "stage70_validation_$Stamp.log"
$script:Failed = $false

function Write-LogLine {
    param([string]$Text)
    $Text | Tee-Object -FilePath $LogPath -Append
}

function Run-Logged {
    param([string]$FilePath, [string[]]$Arguments, [switch]$ContinueOnError)
    Write-LogLine "COMMAND: $FilePath $($Arguments -join ' ')"
    $stdout = Join-Path $LogDir "stage70_stdout_$Stamp.txt"
    $stderr = Join-Path $LogDir "stage70_stderr_$Stamp.txt"
    & $FilePath @Arguments 1> $stdout 2> $stderr
    $code = $LASTEXITCODE
    Write-LogLine "STDOUT:"
    Get-Content -Path $stdout | Tee-Object -FilePath $LogPath -Append
    Write-LogLine "STDERR:"
    Get-Content -Path $stderr | Tee-Object -FilePath $LogPath -Append
    Write-LogLine "EXIT_CODE: $code"
    if ($code -ne 0) {
        $script:Failed = $true
        if (-not $ContinueOnError) { Write-LogLine "FAILED COMMAND" }
    }
    return $code
}

function Print-File {
    param([string]$Path)
    Write-LogLine "PRINT_FILE: $Path"
    if (Test-Path $Path) { Get-Content -Path $Path | Tee-Object -FilePath $LogPath -Append } else { Write-LogLine "MISSING_FILE: $Path"; $script:Failed = $true }
}

function Check-NoBackup {
    param([string]$Directory, [string]$Pattern, [string]$Label)
    $items = Get-ChildItem -Path $Directory -Filter $Pattern -File -ErrorAction SilentlyContinue
    if ($items.Count -gt 0) { Write-LogLine "BACKUP_FOUND: $Label $Pattern"; $script:Failed = $true } else { Write-LogLine "NO_BACKUP_FOUND: $Label $Pattern" }
}

function Clean-PythonCache {
    Write-LogLine "Clean-PythonCache start"
    Get-ChildItem -Path . -Directory -Recurse -Filter __pycache__ -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -File -Recurse -Include *.pyc,*.pyo -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-LogLine "Clean-PythonCache done"
}

Run-Logged py @("-m", "compileall", "-q", "qmt_ai_trading")
$tests = @(
"tests/test_final_authorization_stage39.py","tests/test_redline_review_stage40.py","tests/test_live_gray_ledger_stage41.py","tests/test_live_gray_review_stage42.py","tests/test_live_signature_freeze_stage43.py","tests/test_live_env_snapshot_stage44.py","tests/test_live_runbook_stage45.py","tests/test_live_signoff_stage46.py","tests/test_live_final_review_stage47.py","tests/test_live_archive_stage48.py","tests/test_live_consistency_stage49.py","tests/test_live_final_archive_stage50.py","tests/test_live_archive_lock_stage51.py","tests/test_live_lock_consistency_stage52.py","tests/test_live_archive_verification_stage53.py","tests/test_live_gap_clearance_stage54.py","tests/test_qmt_dryrun_calibration_stage55.py","tests/test_real_cache_quality_stage56.py","tests/test_live_gray_candidate_stage57.py","tests/test_live_gray_final_approval_stage58.py","tests/test_live_gray_readonly_seal_stage59.py","tests/test_pre_gray_final_review_stage60.py","tests/test_api_gateway_stage61.py","tests/test_local_console_stage62.py","tests/test_local_console_detail_stage63.py","tests/test_local_console_dashboard_stage64.py","tests/test_local_console_shell_stage65.py","tests/test_local_console_binding_stage66.py","tests/test_local_console_preview_stage67.py","tests/test_local_console_refresh_stage68.py","tests/test_local_console_grouping_stage69.py","tests/test_local_console_drilldown_stage70.py")
foreach ($t in $tests) { Run-Logged py @("-m", "pytest", $t) }
Run-Logged py @("scripts\run_local_console_drilldown_review.py", "--repo-root", ".", "--output-dir", "local_console_drilldown_stage70", "--binding-dir", "local_console_binding_stage66", "--grouping-dir", "local_console_grouping_stage69", "--refresh-dir", "local_console_refresh_stage68", "--preview-dir", "local_console_preview_stage67", "--output", "local_console_drilldown_stage70\local_console_drilldown_report.md", "--json-output", "local_console_drilldown_stage70\local_console_drilldown_report.json", "--detail-output", "local_console_drilldown_stage70\report_detail_index.md", "--detail-json-output", "local_console_drilldown_stage70\report_detail_index.json", "--route-output", "local_console_drilldown_stage70\drilldown_route_map.md", "--route-json-output", "local_console_drilldown_stage70\drilldown_route_map.json", "--export-output", "local_console_drilldown_stage70\export_manifest.md", "--export-json-output", "local_console_drilldown_stage70\export_manifest.json", "--snapshot-output", "local_console_drilldown_stage70\export_snapshot.md", "--snapshot-json-output", "local_console_drilldown_stage70\export_snapshot.json", "--safety-output", "local_console_drilldown_stage70\export_safety_report.md", "--safety-json-output", "local_console_drilldown_stage70\export_safety_report.json", "--plan-output", "local_console_drilldown_stage70\next_manual_review_workbench_plan.md", "--plan-json-output", "local_console_drilldown_stage70\next_manual_review_workbench_plan.json") -ContinueOnError
Print-File "local_console_drilldown_stage70\local_console_drilldown_report.md"
Print-File "local_console_drilldown_stage70\report_detail_index.md"
Print-File "local_console_drilldown_stage70\drilldown_route_map.md"
Print-File "local_console_drilldown_stage70\export_manifest.md"
Print-File "local_console_drilldown_stage70\export_snapshot.md"
Print-File "local_console_drilldown_stage70\export_safety_report.md"
Print-File "local_console_drilldown_stage70\next_manual_review_workbench_plan.md"
Run-Logged py @("scripts\check_stage53_roadmap_plan.py")
Check-NoBackup "scripts" "validate_stage69.ps1.bak_stage69fix_*" "Stage69 validate"
Check-NoBackup "scripts" "validate_stage70.ps1.bak_stage70fix_*" "Stage70 validate"
Run-Logged py @("scripts\run_daily_pipeline.py", "--cache-root", "market_data_test_stage70", "--research-start", "2026-03-21", "--research-end", "2026-06-18", "--research-frequency", "1d", "--min-bars", "40", "--cached-strategy-top-n", "2", "--enable-local-console-drilldown-review", "--local-console-drilldown-review-output-dir", "local_console_drilldown_stage70")
Run-Logged py @("scripts\run_scheduled_daily_pipeline.py", "--warmup-universe", "--warmup-provider", "mock", "--universe-lookback-days", "90", "--warmup-frequency", "1d", "--cache-root", "market_data_test_stage70", "--data-source-mode", "cached_real_first", "--research-start", "2026-03-21", "--research-end", "2026-06-18", "--research-frequency", "1d", "--min-bars", "40", "--cached-strategy-top-n", "2", "--enable-local-console-drilldown-review", "--local-console-drilldown-review-output-dir", "local_console_drilldown_stage70")
Run-Logged py @("scripts\register_daily_pipeline_task.py", "--warmup-universe", "--warmup-provider", "mock", "--universe-lookback-days", "90", "--warmup-frequency", "1d", "--cache-root", "market_data", "--data-source-mode", "cached_real_first", "--research-start", "2026-03-21", "--research-end", "2026-06-18", "--research-frequency", "1d", "--min-bars", "40", "--cached-strategy-top-n", "2", "--enable-local-console-drilldown-review", "--local-console-drilldown-review-output-dir", "local_console_drilldown", "--time", "15:30")
Clean-PythonCache
Run-Logged powershell @("-ExecutionPolicy", "Bypass", "-File", ".\scripts\sync_all.ps1", "-Mode", "scan")
Run-Logged powershell @("-ExecutionPolicy", "Bypass", "-File", ".\scripts\sync_all.ps1", "-Mode", "status")
if ($script:Failed) { Write-LogLine "STAGE70_VALIDATION_RESULT: FAIL"; exit 1 }
Write-LogLine "STAGE70_VALIDATION_RESULT: PASS"
exit 0
