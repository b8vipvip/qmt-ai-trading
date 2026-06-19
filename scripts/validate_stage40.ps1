$ErrorActionPreference = "Continue"
$Root = "D:\AI\qmt"
Set-Location $Root

$LogDir = Join-Path $Root "validation_logs"
New-Item -ItemType Directory -Force $LogDir | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogPath = Join-Path $LogDir "stage40_validation_$Stamp.log"

function Write-Log {
    param([string]$Text)
    Write-Host $Text
    Add-Content -Path $LogPath -Value $Text -Encoding UTF8
}

function Run-Step {
    param(
        [string]$Name,
        [string]$Command
    )
    Write-Log ""
    Write-Log "========== $Name =========="
    Write-Log $Command
    $Output = cmd /c "$Command 2>&1"
    foreach ($Line in $Output) { Write-Log $Line }
    Write-Log "EXIT_CODE=$LASTEXITCODE"
}

Write-Log "STAGE=40"
Write-Log "VALIDATION_LOG=$LogPath"
Write-Log "ROOT=$Root"

Run-Step "Check redline files" "dir qmt_ai_trading\redline_review && dir scripts\run_redline_review.py && dir tests\test_redline_review_stage40.py && dir docs\stage40-redline-review.md"
Run-Step "Compile" "py -m compileall -q qmt_ai_trading"
Run-Step "Stage39 tests" "py -m pytest tests/test_final_authorization_stage39.py"
Run-Step "Stage40 tests" "py -m pytest tests/test_redline_review_stage40.py"
Run-Step "Run redline review" "py scripts\run_redline_review.py --output redline_review_stage40\redline_review.md --json-output redline_review_stage40\redline_review.json --repo-root ."
Run-Step "Show redline report" "type redline_review_stage40\redline_review.md"
Run-Step "Warmup universe" "py scripts\warmup_etf_universe.py --lookback-days 40 --frequency 1d --provider mock --cache-root market_data_test_stage40"
Run-Step "Daily pipeline redline" "py scripts\run_daily_pipeline.py --cache-root market_data_test_stage40 --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 2 --enable-redline-review --redline-review-output-dir redline_review_stage40"
Run-Step "Scheduled pipeline redline" "py scripts\run_scheduled_daily_pipeline.py --warmup-universe --warmup-provider mock --universe-lookback-days 40 --warmup-frequency 1d --cache-root market_data_test_stage40 --data-source-mode cached_real_first --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 2 --enable-redline-review --redline-review-output-dir redline_review_stage40"
Run-Step "Register preview redline" "py scripts\register_daily_pipeline_task.py --warmup-universe --warmup-provider mock --universe-lookback-days 40 --warmup-frequency 1d --cache-root market_data --data-source-mode cached_real_first --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 2 --enable-redline-review --redline-review-output-dir redline_review --time 15:30"
Run-Step "Privacy scan" "powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode scan"
Run-Step "Git status" "powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode status"

Write-Log ""
Write-Log "VALIDATION_LOG=$LogPath"
Write-Host "VALIDATION_LOG=$LogPath"
