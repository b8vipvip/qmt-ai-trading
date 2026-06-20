$ErrorActionPreference = "Continue"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot
$LogDir = Join-Path $RepoRoot "validation_logs"
if (-not (Test-Path -LiteralPath $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$StartedAt = Get-Date
$Stamp = $StartedAt.ToString("yyyyMMdd_HHmmss")
$LogPath = Join-Path $LogDir "stage68_validation_$Stamp.log"
$script:HadError = $false
function Write-Log { param([string]$Message) $Message | Tee-Object -FilePath $LogPath -Append }
function Run-Command { param([string]$CommandLine) Write-Log ""; Write-Log (">>> " + $CommandLine); $output=$null; $exitCode=0; try { $output=cmd /c $CommandLine 2>&1; $exitCode=$LASTEXITCODE; if ($null -eq $exitCode) { if ($?) { $exitCode=0 } else { $exitCode=1 } } } catch { $output=$_ | Out-String; $exitCode=1 }; if ($null -ne $output) { foreach ($line in $output) { Write-Log ([string]$line) } }; Write-Log ""; Write-Log "EXIT_CODE=$exitCode"; if ($exitCode -ne 0) { $script:HadError=$true }; return $exitCode }
function Print-File { param([string]$Path) Write-Log ""; Write-Log ">>> print file $Path"; if (Test-Path -LiteralPath $Path) { try { Get-Content -LiteralPath $Path -Encoding UTF8 | Tee-Object -FilePath $LogPath -Append; Write-Log ""; Write-Log "EXIT_CODE=0" } catch { Write-Log ($_ | Out-String); Write-Log ""; Write-Log "EXIT_CODE=1"; $script:HadError=$true } } else { Write-Log "SKIPPED: report file not generated ($Path)"; Write-Log ""; Write-Log "EXIT_CODE=1"; $script:HadError=$true } }
function Check-NoBackup { param([string]$Dir,[string]$Filter,[string]$Label) Write-Log ""; Write-Log ">>> check no backup: $Dir $Filter"; $found=Get-ChildItem -Path $Dir -Filter $Filter -ErrorAction SilentlyContinue; if ($found) { Write-Log "$Label backup files still exist:"; foreach ($item in $found) { Write-Log ("- " + $item.FullName) }; Write-Log ""; Write-Log "EXIT_CODE=1"; $script:HadError=$true } else { Write-Log "$Label backup files cleaned."; Write-Log ""; Write-Log "EXIT_CODE=0" } }
function Clean-PythonCache { Write-Log ""; Write-Log ">>> clean python cache artifacts"; Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; Get-ChildItem -Path . -Recurse -File -Include "*.pyc", "*.pyo" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue; Write-Log "Python cache artifacts cleaned."; Write-Log "EXIT_CODE=0" }
Write-Log "Stage68 validation started $($StartedAt.ToString('o'))"
Run-Command "py -m compileall -q qmt_ai_trading"
$tests = @("tests/test_final_authorization_stage39.py","tests/test_redline_review_stage40.py","tests/test_live_gray_ledger_stage41.py","tests/test_live_gray_review_stage42.py","tests/test_live_signature_freeze_stage43.py","tests/test_live_env_snapshot_stage44.py","tests/test_live_runbook_stage45.py","tests/test_live_signoff_stage46.py","tests/test_live_final_review_stage47.py","tests/test_live_archive_stage48.py","tests/test_live_consistency_stage49.py","tests/test_live_final_archive_stage50.py","tests/test_live_archive_lock_stage51.py","tests/test_live_lock_consistency_stage52.py","tests/test_live_archive_verification_stage53.py","tests/test_live_gap_clearance_stage54.py","tests/test_qmt_dryrun_calibration_stage55.py","tests/test_real_cache_quality_stage56.py","tests/test_live_gray_candidate_stage57.py","tests/test_live_gray_final_approval_stage58.py","tests/test_live_gray_readonly_seal_stage59.py","tests/test_pre_gray_final_review_stage60.py","tests/test_api_gateway_stage61.py","tests/test_local_console_stage62.py","tests/test_local_console_detail_stage63.py","tests/test_local_console_dashboard_stage64.py","tests/test_local_console_shell_stage65.py","tests/test_local_console_binding_stage66.py","tests/test_local_console_preview_stage67.py","tests/test_local_console_refresh_stage68.py")
foreach ($t in $tests) { Run-Command "py -m pytest $t" }
$reviewCommand = "py scripts/run_local_console_refresh_review.py --repo-root . --output-dir local_console_refresh_stage68 --binding-dir local_console_binding_stage66 --preview-dir local_console_preview_stage67 --output local_console_refresh_stage68/local_console_refresh_report.md --json-output local_console_refresh_stage68/local_console_refresh_report.json --route-output local_console_refresh_stage68/navigation_route_map.md --route-json-output local_console_refresh_stage68/navigation_route_map.json --manifest-output local_console_refresh_stage68/refresh_manifest.md --manifest-json-output local_console_refresh_stage68/refresh_manifest.json --state-output local_console_refresh_stage68/ui_state_placeholders.md --state-json-output local_console_refresh_stage68/ui_state_placeholders.json --safety-output local_console_refresh_stage68/frontend_safety_report.md --safety-json-output local_console_refresh_stage68/frontend_safety_report.json --plan-output local_console_refresh_stage68/next_console_grouping_filter_plan.md --plan-json-output local_console_refresh_stage68/next_console_grouping_filter_plan.json"
Run-Command $reviewCommand
Print-File "local_console_refresh_stage68/local_console_refresh_report.md"
Print-File "local_console_refresh_stage68/navigation_route_map.md"
Print-File "local_console_refresh_stage68/refresh_manifest.md"
Print-File "local_console_refresh_stage68/ui_state_placeholders.md"
Print-File "local_console_refresh_stage68/frontend_safety_report.md"
Print-File "local_console_refresh_stage68/next_console_grouping_filter_plan.md"
Run-Command "py scripts/check_stage53_roadmap_plan.py"
Check-NoBackup "scripts" "validate_stage67.ps1.bak_stage67fix_*" "Stage67 validate"
Check-NoBackup "scripts" "validate_stage68.ps1.bak_stage68fix_*" "Stage68 validate"
Run-Command "py scripts/run_daily_pipeline.py --cache-root market_data_test_stage68 --research-start 2026-03-21 --research-end 2026-06-18 --research-frequency 1d --min-bars 40 --cached-strategy-top-n 2 --enable-local-console-refresh-review --local-console-refresh-review-output-dir local_console_refresh_stage68"
Run-Command "py scripts/run_scheduled_daily_pipeline.py --warmup-universe --warmup-provider mock --universe-lookback-days 90 --warmup-frequency 1d --cache-root market_data_test_stage68 --data-source-mode cached_real_first --research-start 2026-03-21 --research-end 2026-06-18 --research-frequency 1d --min-bars 40 --cached-strategy-top-n 2 --enable-local-console-refresh-review --local-console-refresh-review-output-dir local_console_refresh_stage68"
Run-Command "py scripts/register_daily_pipeline_task.py --warmup-universe --warmup-provider mock --universe-lookback-days 90 --warmup-frequency 1d --cache-root market_data --data-source-mode cached_real_first --research-start 2026-03-21 --research-end 2026-06-18 --research-frequency 1d --min-bars 40 --cached-strategy-top-n 2 --enable-local-console-refresh-review --local-console-refresh-review-output-dir local_console_refresh --time 15:30"
Clean-PythonCache
Run-Command "powershell -ExecutionPolicy Bypass -File ./scripts/sync_all.ps1 -Mode scan"
Run-Command "powershell -ExecutionPolicy Bypass -File ./scripts/sync_all.ps1 -Mode status"
if ($script:HadError) { Write-Log "Stage68 validation FAILED"; exit 1 }
Write-Log "Stage68 validation PASSED"
exit 0
