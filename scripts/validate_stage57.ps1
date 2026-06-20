$ErrorActionPreference = "Continue"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot
$LogDir = Join-Path $RepoRoot "validation_logs"
if (-not (Test-Path -LiteralPath $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$StartedAt = Get-Date
$Stamp = $StartedAt.ToString("yyyyMMdd_HHmmss")
$LogPath = Join-Path $LogDir "stage57_validation_$Stamp.log"
$script:HadError = $false
function Write-Log { param([string]$Message) $Message | Tee-Object -FilePath $LogPath -Append }
function Run-Command { param([string]$File, [string[]]$Arguments)
    Write-Log ""; Write-Log (">>> " + $File + " " + ($Arguments -join " "))
    $output = $null; $exitCode = 0
    try { $output = & $File @Arguments 2>&1; $exitCode = $LASTEXITCODE; if ($null -eq $exitCode) { if ($?) { $exitCode = 0 } else { $exitCode = 1 } } } catch { $output = $_ | Out-String; $exitCode = 1 }
    if ($null -ne $output) { foreach ($line in $output) { Write-Log ([string]$line) } }
    Write-Log ""; Write-Log "EXIT_CODE=$exitCode"
    if ($exitCode -ne 0) { $script:HadError = $true }
    return $exitCode
}
function Print-File { param([string]$Path)
    Write-Log ""; Write-Log ">>> print file $Path"
    if (Test-Path -LiteralPath $Path) { try { Get-Content -LiteralPath $Path -Encoding UTF8 | Tee-Object -FilePath $LogPath -Append; Write-Log ""; Write-Log "EXIT_CODE=0" } catch { Write-Log ($_ | Out-String); Write-Log ""; Write-Log "EXIT_CODE=1"; $script:HadError = $true } } else { Write-Log "SKIPPED: report file not generated ($Path)"; Write-Log ""; Write-Log "EXIT_CODE=1"; $script:HadError = $true }
}
function Check-NoBackup { param([string]$Dir,[string]$Filter,[string]$Label)
    Write-Log ""; Write-Log ">>> check no backup: $Dir $Filter"
    $found = Get-ChildItem -Path $Dir -Filter $Filter -ErrorAction SilentlyContinue
    if ($found) { Write-Log "$Label backup files still exist:"; foreach ($item in $found) { Write-Log ("- " + $item.FullName) }; Write-Log ""; Write-Log "EXIT_CODE=1"; $script:HadError = $true } else { Write-Log "$Label backup files cleaned."; Write-Log ""; Write-Log "EXIT_CODE=0" }
}
Write-Log "Stage57 validation started $($StartedAt.ToString('o'))"
Run-Command "py" @("-m","compileall","-q","qmt_ai_trading")
$tests = @("tests/test_final_authorization_stage39.py","tests/test_redline_review_stage40.py","tests/test_live_gray_ledger_stage41.py","tests/test_live_gray_review_stage42.py","tests/test_live_signature_freeze_stage43.py","tests/test_live_env_snapshot_stage44.py","tests/test_live_runbook_stage45.py","tests/test_live_signoff_stage46.py","tests/test_live_final_review_stage47.py","tests/test_live_archive_stage48.py","tests/test_live_consistency_stage49.py","tests/test_live_final_archive_stage50.py","tests/test_live_archive_lock_stage51.py","tests/test_live_lock_consistency_stage52.py","tests/test_live_archive_verification_stage53.py","tests/test_live_gap_clearance_stage54.py","tests/test_qmt_dryrun_calibration_stage55.py","tests/test_real_cache_quality_stage56.py","tests/test_live_gray_candidate_stage57.py")
foreach ($t in $tests) { Run-Command "py" @("-m","pytest",$t) }
$lgcArgs = @("scripts/run_live_gray_candidate.py","--repo-root",".","--output-dir","live_gray_candidate_stage57","--real-cache-quality-dir","real_cache_quality_stage56","--qmt-dryrun-calibration-dir","qmt_dryrun_calibration_stage55","--gray-total-capital-limit","1000","--single-trade-capital-limit","200","--daily-trade-capital-limit","300","--max-positions","2","--max-single-symbol-weight","0.20","--max-portfolio-exposure","0.50","--cash-reserve-ratio","0.50","--max-daily-loss-ratio","0.01","--max-total-drawdown-ratio","0.03","--max-orders-per-day","2","--cooldown-days-after-stop","3")
Run-Command "py" $lgcArgs
Print-File "live_gray_candidate_stage57/live_gray_candidate.md"
Print-File "live_gray_candidate_stage57/gray_risk_limits.md"
Print-File "live_gray_candidate_stage57/gray_approval_checklist.md"
Print-File "live_gray_candidate_stage57/gray_rollback_circuit_breaker.md"
Print-File "live_gray_candidate_stage57/next_gray_approval_package_plan.md"
Run-Command "py" @("scripts/check_stage53_roadmap_plan.py")
Check-NoBackup "scripts" "validate_stage56.ps1.bak_stage56fix_*" "Stage56 validate"
Check-NoBackup "scripts" "validate_stage57.ps1.bak_stage57fix_*" "Stage57 validate"
Run-Command "py" @("scripts/warmup_etf_universe.py","--lookback-days","90","--frequency","1d","--provider","mock","--cache-root","market_data_test_stage57")
Run-Command "py" @("scripts/run_daily_pipeline.py","--cache-root","market_data_test_stage57","--research-start","2026-03-21","--research-end","2026-06-18","--research-frequency","1d","--min-bars","40","--cached-strategy-top-n","2","--enable-live-gray-candidate","--live-gray-candidate-output-dir","live_gray_candidate_stage57")
Run-Command "py" @("scripts/run_scheduled_daily_pipeline.py","--warmup-universe","--warmup-provider","mock","--universe-lookback-days","90","--warmup-frequency","1d","--cache-root","market_data_test_stage57","--data-source-mode","cached_real_first","--research-start","2026-03-21","--research-end","2026-06-18","--research-frequency","1d","--min-bars","40","--cached-strategy-top-n","2","--enable-live-gray-candidate","--live-gray-candidate-output-dir","live_gray_candidate_stage57")
Run-Command "py" @("scripts/register_daily_pipeline_task.py","--warmup-universe","--warmup-provider","mock","--universe-lookback-days","90","--warmup-frequency","1d","--cache-root","market_data","--data-source-mode","cached_real_first","--research-start","2026-03-21","--research-end","2026-06-18","--research-frequency","1d","--min-bars","40","--cached-strategy-top-n","2","--enable-live-gray-candidate","--live-gray-candidate-output-dir","live_gray_candidate","--time","15:30")
Run-Command "powershell" @("-ExecutionPolicy","Bypass","-File","./scripts/sync_all.ps1","-Mode","scan")
Run-Command "powershell" @("-ExecutionPolicy","Bypass","-File","./scripts/sync_all.ps1","-Mode","status")
$FinishedAt = Get-Date
if ($script:HadError) { Write-Log "Stage57 validation finished $($FinishedAt.ToString('o')) EXIT_CODE=1"; Write-Error "Stage57 validation failed. Log: $LogPath"; exit 1 }
Write-Log "Stage57 validation finished $($FinishedAt.ToString('o')) EXIT_CODE=0"
exit 0
