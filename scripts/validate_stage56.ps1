$ErrorActionPreference = "Continue"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot
$LogDir = Join-Path $RepoRoot "validation_logs"
if (-not (Test-Path -LiteralPath $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$Stamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
$LogPath = Join-Path $LogDir "stage56_validation_$Stamp.log"
$script:HadError = $false
function Write-Log { param([string]$Message) $Message | Tee-Object -FilePath $LogPath -Append }
function Run-Command { param([string]$Command)
  Write-Log ""; Write-Log ">>> $Command"
  try { $output = & powershell -NoProfile -ExecutionPolicy Bypass -Command $Command 2>&1; $exitCode = $LASTEXITCODE; if ($null -eq $exitCode) { if ($?) { $exitCode=0 } else { $exitCode=1 } } }
  catch { $output = $_ | Out-String; $exitCode = 1 }
  if ($null -ne $output) { foreach ($line in $output) { Write-Log ([string]$line) } }
  Write-Log ""; Write-Log "EXIT_CODE=$exitCode"; if ($exitCode -ne 0) { $script:HadError=$true }
}
function Print-File { param([string]$Path) Write-Log ""; Write-Log ">>> print file $Path"; if (Test-Path -LiteralPath $Path) { Get-Content -LiteralPath $Path -Encoding UTF8 | Tee-Object -FilePath $LogPath -Append; Write-Log ""; Write-Log "EXIT_CODE=0" } else { Write-Log "MISSING: $Path"; Write-Log "EXIT_CODE=1"; $script:HadError=$true } }
Write-Log "Stage56 validation started $((Get-Date).ToString('o'))"
$tests = @('tests/test_final_authorization_stage39.py','tests/test_redline_review_stage40.py','tests/test_live_gray_ledger_stage41.py','tests/test_live_gray_review_stage42.py','tests/test_live_signature_freeze_stage43.py','tests/test_live_env_snapshot_stage44.py','tests/test_live_runbook_stage45.py','tests/test_live_signoff_stage46.py','tests/test_live_final_review_stage47.py','tests/test_live_archive_stage48.py','tests/test_live_consistency_stage49.py','tests/test_live_final_archive_stage50.py','tests/test_live_archive_lock_stage51.py','tests/test_live_lock_consistency_stage52.py','tests/test_live_archive_verification_stage53.py','tests/test_live_gap_clearance_stage54.py','tests/test_qmt_dryrun_calibration_stage55.py','tests/test_real_cache_quality_stage56.py')
Run-Command "py -m compileall -q qmt_ai_trading"
foreach ($t in $tests) { Run-Command "py -m pytest $t" }
Run-Command "py scripts\run_real_cache_quality.py --repo-root . --output-dir real_cache_quality_stage56 --qmt-dryrun-calibration-dir qmt_dryrun_calibration_stage55 --cache-root market_data_test_stage56 --provider mock --max-symbols 5 --min-days 40 --target-days 90 --output real_cache_quality_stage56\real_cache_quality.md --json-output real_cache_quality_stage56\real_cache_quality.json --gapfill-output real_cache_quality_stage56\long_sample_gap_fill.md --gapfill-json-output real_cache_quality_stage56\long_sample_gap_fill.json --field-output real_cache_quality_stage56\field_quality_review.md --field-json-output real_cache_quality_stage56\field_quality_review.json --plan-output real_cache_quality_stage56\next_backtest_attribution_plan.md --plan-json-output real_cache_quality_stage56\next_backtest_attribution_plan.json"
Print-File "real_cache_quality_stage56\real_cache_quality.md"; Print-File "real_cache_quality_stage56\long_sample_gap_fill.md"; Print-File "real_cache_quality_stage56\field_quality_review.md"; Print-File "real_cache_quality_stage56\next_backtest_attribution_plan.md"
Run-Command "py scripts\check_stage53_roadmap_plan.py"
Run-Command "powershell -NoProfile -Command \"if (Get-ChildItem -Path scripts -Filter 'validate_stage55.ps1.bak_stage55fix_*' -ErrorAction SilentlyContinue) { Write-Error 'Stage55 validate backup file still exists'; exit 1 } else { Write-Output 'Stage55 validate backup files cleaned.' }\""
Run-Command "py scripts\warmup_etf_universe.py --lookback-days 90 --frequency 1d --provider mock --cache-root market_data_test_stage56"
Run-Command "py scripts\run_daily_pipeline.py --cache-root market_data_test_stage56 --research-start 2026-03-21 --research-end 2026-06-18 --research-frequency 1d --min-bars 40 --cached-strategy-top-n 2 --enable-real-cache-quality --real-cache-quality-output-dir real_cache_quality_stage56 --real-cache-quality-provider mock"
Run-Command "py scripts\run_scheduled_daily_pipeline.py --warmup-universe --warmup-provider mock --universe-lookback-days 90 --warmup-frequency 1d --cache-root market_data_test_stage56 --data-source-mode cached_real_first --research-start 2026-03-21 --research-end 2026-06-18 --research-frequency 1d --min-bars 40 --cached-strategy-top-n 2 --enable-real-cache-quality --real-cache-quality-output-dir real_cache_quality_stage56 --real-cache-quality-provider mock"
Run-Command "py scripts\register_daily_pipeline_task.py --warmup-universe --warmup-provider mock --universe-lookback-days 90 --warmup-frequency 1d --cache-root market_data --data-source-mode cached_real_first --research-start 2026-03-21 --research-end 2026-06-18 --research-frequency 1d --min-bars 40 --cached-strategy-top-n 2 --enable-real-cache-quality --real-cache-quality-output-dir real_cache_quality --real-cache-quality-provider mock --time 15:30"
Run-Command "powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode scan"
Run-Command "powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode status"
if ($script:HadError) { Write-Log "Stage56 validation finished $((Get-Date).ToString('o')) EXIT_CODE=1"; Write-Error "Stage56 validation failed. Log: $LogPath"; exit 1 }
Write-Log "Stage56 validation finished $((Get-Date).ToString('o')) EXIT_CODE=0"; exit 0
