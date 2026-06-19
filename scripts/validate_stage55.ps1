$ErrorActionPreference = "Continue"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$LogDir = Join-Path $RepoRoot "validation_logs"
if (-not (Test-Path -LiteralPath $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

$StartedAt = Get-Date
$Stamp = $StartedAt.ToString("yyyyMMdd_HHmmss")
$LogPath = Join-Path $LogDir "stage55_validation_$Stamp.log"

$script:HadError = $false

function Write-Log {
    param([string]$Message)
    $Message | Tee-Object -FilePath $LogPath -Append
}

function Run-Command {
    param([string]$Command)

    Write-Log ""
    Write-Log ">>> $Command"

    $output = $null
    $exitCode = 0

    try {
        $output = & powershell -NoProfile -ExecutionPolicy Bypass -Command $Command 2>&1
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) {
            if ($?) { $exitCode = 0 } else { $exitCode = 1 }
        }
    } catch {
        $output = $_ | Out-String
        $exitCode = 1
    }

    if ($null -ne $output) {
        foreach ($line in $output) {
            Write-Log ([string]$line)
        }
    }

    Write-Log ""
    Write-Log "EXIT_CODE=$exitCode"

    if ($exitCode -ne 0) {
        $script:HadError = $true
    }
}

function Print-File {
    param([string]$Path)

    Write-Log ""
    Write-Log ">>> print file $Path"

    if (Test-Path -LiteralPath $Path) {
        try {
            Get-Content -LiteralPath $Path -Encoding UTF8 | Tee-Object -FilePath $LogPath -Append
            Write-Log ""
            Write-Log "EXIT_CODE=0"
        } catch {
            Write-Log ($_ | Out-String)
            Write-Log ""
            Write-Log "EXIT_CODE=1"
            $script:HadError = $true
        }
    } else {
        Write-Log "SKIPPED: report file not generated ($Path)"
        Write-Log ""
        Write-Log "EXIT_CODE=1"
        $script:HadError = $true
    }
}

function Check-NoBackup {
    param(
        [string]$Dir,
        [string]$Filter,
        [string]$Label
    )

    Write-Log ""
    Write-Log ">>> check no backup: $Dir $Filter"

    $found = Get-ChildItem -Path $Dir -Filter $Filter -ErrorAction SilentlyContinue
    if ($found) {
        Write-Log "$Label backup files still exist:"
        foreach ($item in $found) {
            Write-Log ("- " + $item.FullName)
        }
        Write-Log ""
        Write-Log "EXIT_CODE=1"
        $script:HadError = $true
    } else {
        Write-Log "$Label backup files cleaned."
        Write-Log ""
        Write-Log "EXIT_CODE=0"
    }
}

Write-Log "Stage55 validation started $($StartedAt.ToString('o'))"

Run-Command "py -m compileall -q qmt_ai_trading"
Run-Command "py -m pytest tests/test_final_authorization_stage39.py"
Run-Command "py -m pytest tests/test_redline_review_stage40.py"
Run-Command "py -m pytest tests/test_live_gray_ledger_stage41.py"
Run-Command "py -m pytest tests/test_live_gray_review_stage42.py"
Run-Command "py -m pytest tests/test_live_signature_freeze_stage43.py"
Run-Command "py -m pytest tests/test_live_env_snapshot_stage44.py"
Run-Command "py -m pytest tests/test_live_runbook_stage45.py"
Run-Command "py -m pytest tests/test_live_signoff_stage46.py"
Run-Command "py -m pytest tests/test_live_final_review_stage47.py"
Run-Command "py -m pytest tests/test_live_archive_stage48.py"
Run-Command "py -m pytest tests/test_live_consistency_stage49.py"
Run-Command "py -m pytest tests/test_live_final_archive_stage50.py"
Run-Command "py -m pytest tests/test_live_archive_lock_stage51.py"
Run-Command "py -m pytest tests/test_live_lock_consistency_stage52.py"
Run-Command "py -m pytest tests/test_live_archive_verification_stage53.py"
Run-Command "py -m pytest tests/test_live_gap_clearance_stage54.py"
Run-Command "py -m pytest tests/test_qmt_dryrun_calibration_stage55.py"

Run-Command "py scripts\run_qmt_dryrun_calibration.py --repo-root . --output-dir qmt_dryrun_calibration_stage55 --gap-clearance-dir live_gap_clearance_stage54 --cache-root market_data_test_stage55 --provider mock --max-symbols 5 --max-days 90 --output qmt_dryrun_calibration_stage55\qmt_dryrun_calibration.md --json-output qmt_dryrun_calibration_stage55\qmt_dryrun_calibration.json --xtdata-output qmt_dryrun_calibration_stage55\xtdata_capability.md --xtdata-json-output qmt_dryrun_calibration_stage55\xtdata_capability.json --whitelist-output qmt_dryrun_calibration_stage55\etf_whitelist_calibration.md --whitelist-json-output qmt_dryrun_calibration_stage55\etf_whitelist_calibration.json --plan-output qmt_dryrun_calibration_stage55\next_real_cache_quality_plan.md --plan-json-output qmt_dryrun_calibration_stage55\next_real_cache_quality_plan.json"

Print-File "qmt_dryrun_calibration_stage55\qmt_dryrun_calibration.md"
Print-File "qmt_dryrun_calibration_stage55\xtdata_capability.md"
Print-File "qmt_dryrun_calibration_stage55\etf_whitelist_calibration.md"
Print-File "qmt_dryrun_calibration_stage55\next_real_cache_quality_plan.md"

Run-Command "py scripts\check_stage53_roadmap_plan.py"

Check-NoBackup "qmt_ai_trading\live_gap_clearance" "*.bak_stage54fix_*" "Stage54 collector"
Check-NoBackup "scripts" "validate_stage54.ps1.bak_stage54fix_*" "Stage54 validate"
Check-NoBackup "scripts" "validate_stage55.ps1.bak_stage55fix_*" "Stage55 validate"

Run-Command "py scripts\warmup_etf_universe.py --lookback-days 40 --frequency 1d --provider mock --cache-root market_data_test_stage55"

Run-Command "py scripts\run_daily_pipeline.py --cache-root market_data_test_stage55 --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 2 --enable-qmt-dryrun-calibration --qmt-dryrun-calibration-output-dir qmt_dryrun_calibration_stage55 --qmt-dryrun-calibration-provider mock"

Run-Command "py scripts\run_scheduled_daily_pipeline.py --warmup-universe --warmup-provider mock --universe-lookback-days 40 --warmup-frequency 1d --cache-root market_data_test_stage55 --data-source-mode cached_real_first --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 2 --enable-qmt-dryrun-calibration --qmt-dryrun-calibration-output-dir qmt_dryrun_calibration_stage55 --qmt-dryrun-calibration-provider mock"

Run-Command "py scripts\register_daily_pipeline_task.py --warmup-universe --warmup-provider mock --universe-lookback-days 40 --warmup-frequency 1d --cache-root market_data --data-source-mode cached_real_first --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 2 --enable-qmt-dryrun-calibration --qmt-dryrun-calibration-output-dir qmt_dryrun_calibration --qmt-dryrun-calibration-provider mock --time 15:30"

Run-Command "powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode scan"
Run-Command "powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode status"

$FinishedAt = Get-Date

if ($script:HadError) {
    Write-Log "Stage55 validation finished $($FinishedAt.ToString('o')) EXIT_CODE=1"
    Write-Error "Stage55 validation failed. Log: $LogPath"
    exit 1
}

Write-Log "Stage55 validation finished $($FinishedAt.ToString('o')) EXIT_CODE=0"
exit 0
