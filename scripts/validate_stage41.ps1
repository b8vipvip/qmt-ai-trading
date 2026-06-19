$ErrorActionPreference = "Continue"
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $Utf8NoBom
[Console]::InputEncoding = $Utf8NoBom
$OutputEncoding = $Utf8NoBom
cmd /c chcp 65001 | Out-Null
$Root = if (Test-Path "D:\AI\qmt") { "D:\AI\qmt" } else { (Resolve-Path ".").Path }
Set-Location $Root
$LogDir = Join-Path $Root "validation_logs"
New-Item -ItemType Directory -Force $LogDir | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogPath = Join-Path $LogDir "stage41_validation_$Stamp.log"
function Write-Log { param([string]$Text) Write-Host $Text; Add-Content -Path $LogPath -Value $Text -Encoding UTF8 }
function Run-Step { param([string]$Name,[string]$Command) Write-Log ""; Write-Log "========== $Name =========="; Write-Log $Command; $Output = cmd /c "$Command 2>&1"; foreach ($Line in $Output) { Write-Log $Line }; Write-Log "EXIT_CODE=$LASTEXITCODE" }
Write-Log "STAGE=41"; Write-Log "VALIDATION_LOG=$LogPath"; Write-Log "ROOT=$Root"
Run-Step "Compile" "py -m compileall -q qmt_ai_trading"
Run-Step "Stage39 tests" "py -m pytest tests/test_final_authorization_stage39.py"
Run-Step "Stage40 tests" "py -m pytest tests/test_redline_review_stage40.py"
Run-Step "Stage41 tests" "py -m pytest tests/test_live_gray_ledger_stage41.py"
Run-Step "Run live gray ledger" "py scripts\run_live_gray_ledger.py --repo-root . --output-dir live_gray_ledger_stage41 --output live_gray_ledger_stage41\live_gray_ledger.md --json-output live_gray_ledger_stage41\live_gray_ledger.json"
Run-Step "Show live gray ledger" "powershell -NoProfile -Command ""Get-Content -Path live_gray_ledger_stage41\live_gray_ledger.md -Encoding UTF8"""
Run-Step "Warmup universe" "py scripts\warmup_etf_universe.py --lookback-days 40 --frequency 1d --provider mock --cache-root market_data_test_stage41"
Run-Step "Daily pipeline ledger" "py scripts\run_daily_pipeline.py --cache-root market_data_test_stage41 --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 2 --enable-live-gray-ledger --live-gray-ledger-output-dir live_gray_ledger_stage41"
Run-Step "Scheduled pipeline ledger" "py scripts\run_scheduled_daily_pipeline.py --warmup-universe --warmup-provider mock --universe-lookback-days 40 --warmup-frequency 1d --cache-root market_data_test_stage41 --data-source-mode cached_real_first --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 2 --enable-live-gray-ledger --live-gray-ledger-output-dir live_gray_ledger_stage41"
Run-Step "Register preview ledger" "py scripts\register_daily_pipeline_task.py --warmup-universe --warmup-provider mock --universe-lookback-days 40 --warmup-frequency 1d --cache-root market_data --data-source-mode cached_real_first --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 2 --enable-live-gray-ledger --live-gray-ledger-output-dir live_gray_ledger --time 15:30"
Run-Step "Privacy scan" "powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode scan"
Run-Step "Git status" "powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode status"
Write-Log ""; Write-Log "VALIDATION_LOG=$LogPath"; Write-Host "VALIDATION_LOG=$LogPath"
