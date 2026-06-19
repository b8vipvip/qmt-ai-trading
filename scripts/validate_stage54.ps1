$ErrorActionPreference = "Continue"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$LogDir = Join-Path $RepoRoot "validation_logs"
if (-not (Test-Path -LiteralPath $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

$StartedAt = Get-Date
$Stamp = $StartedAt.ToString("yyyyMMdd_HHmmss")
$LogPath = Join-Path $LogDir "stage54_validation_$Stamp.log"

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

Write-Log "Stage54 validation started $($StartedAt.ToString('o'))"

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

Run-Command "py scripts\run_live_gap_clearance.py --repo-root . --output-dir live_gap_clearance_stage54 --output live_gap_clearance_stage54\live_gap_clearance.md --json-output live_gap_clearance_stage54\live_gap_clearance.json --remediation-output live_gap_clearance_stage54\evidence_remediation.md --remediation-json-output live_gap_clearance_stage54\evidence_remediation.json --human-output live_gap_clearance_stage54\human_closure_recheck.md --human-json-output live_gap_clearance_stage54\human_closure_recheck.json --plan-output live_gap_clearance_stage54\next_readonly_check_plan.md --plan-json-output live_gap_clearance_stage54\next_readonly_check_plan.json"

Print-File "live_gap_clearance_stage54\live_gap_clearance.md"
Print-File "live_gap_clearance_stage54\evidence_remediation.md"
Print-File "live_gap_clearance_stage54\human_closure_recheck.md"
Print-File "live_gap_clearance_stage54\next_readonly_check_plan.md"

Run-Command "py scripts\check_stage53_roadmap_plan.py"
Run-Command "py scripts\check_stage54_no_stage53_backup.py"

Run-Command "py scripts\warmup_etf_universe.py --lookback-days 40 --frequency 1d --provider mock --cache-root market_data_test_stage54"

Run-Command "py scripts\run_daily_pipeline.py --cache-root market_data_test_stage54 --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 2 --enable-live-gap-clearance --live-gap-clearance-output-dir live_gap_clearance_stage54"

Run-Command "py scripts\run_scheduled_daily_pipeline.py --warmup-universe --warmup-provider mock --universe-lookback-days 40 --warmup-frequency 1d --cache-root market_data_test_stage54 --data-source-mode cached_real_first --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 2 --enable-live-gap-clearance --live-gap-clearance-output-dir live_gap_clearance_stage54"

Run-Command "py scripts\register_daily_pipeline_task.py --warmup-universe --warmup-provider mock --universe-lookback-days 40 --warmup-frequency 1d --cache-root market_data --data-source-mode cached_real_first --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 2 --enable-live-gap-clearance --live-gap-clearance-output-dir live_gap_clearance --time 15:30"

Run-Command "powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode scan"
Run-Command "powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode status"

$FinishedAt = Get-Date

if ($script:HadError) {
    Write-Log "Stage54 validation finished $($FinishedAt.ToString('o')) EXIT_CODE=1"
    Write-Error "Stage54 validation failed. Log: $LogPath"
    exit 1
}

Write-Log "Stage54 validation finished $($FinishedAt.ToString('o')) EXIT_CODE=0"
exit 0
