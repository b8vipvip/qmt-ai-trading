# Stage43 validation runner. Writes stdout/stderr and EXIT_CODE to validation_logs/.
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$LogDir = Join-Path $Root "validation_logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogPath = Join-Path $LogDir "stage43_validation_$Stamp.log"
function Invoke-LoggedCommand { param([string]$Command)
    Add-Content -Path $LogPath -Encoding UTF8 -Value "`n>>> $Command"
    $output = & powershell -NoProfile -Command $Command 2>&1
    $code = $LASTEXITCODE
    if ($null -ne $output) { Add-Content -Path $LogPath -Encoding UTF8 -Value ($output | Out-String) }
    Add-Content -Path $LogPath -Encoding UTF8 -Value "EXIT_CODE=$code"
    if ($code -ne 0) { throw "Command failed with EXIT_CODE=$code`: $Command" }
}
Add-Content -Path $LogPath -Encoding UTF8 -Value "Stage43 validation started $(Get-Date -Format o)"
$commands = @(
'py -m compileall -q qmt_ai_trading',
'py -m pytest tests/test_final_authorization_stage39.py',
'py -m pytest tests/test_redline_review_stage40.py',
'py -m pytest tests/test_live_gray_ledger_stage41.py',
'py -m pytest tests/test_live_gray_review_stage42.py',
'py -m pytest tests/test_live_signature_freeze_stage43.py',
'py scripts\run_live_signature_freeze.py --repo-root . --output-dir live_signature_freeze_stage43 --output live_signature_freeze_stage43\live_signature_freeze.md --json-output live_signature_freeze_stage43\live_signature_freeze.json --config-freeze-output live_signature_freeze_stage43\config_freeze.md --config-freeze-json-output live_signature_freeze_stage43\config_freeze.json',
'powershell -NoProfile -Command "Get-Content -Path live_signature_freeze_stage43\live_signature_freeze.md -Encoding UTF8"',
'powershell -NoProfile -Command "Get-Content -Path live_signature_freeze_stage43\config_freeze.md -Encoding UTF8"',
'py scripts\warmup_etf_universe.py --lookback-days 40 --frequency 1d --provider mock --cache-root market_data_test_stage43',
'py scripts\run_daily_pipeline.py --cache-root market_data_test_stage43 --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 2 --enable-live-signature-freeze --live-signature-freeze-output-dir live_signature_freeze_stage43',
'py scripts\run_scheduled_daily_pipeline.py --warmup-universe --warmup-provider mock --universe-lookback-days 40 --warmup-frequency 1d --cache-root market_data_test_stage43 --data-source-mode cached_real_first --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 2 --enable-live-signature-freeze --live-signature-freeze-output-dir live_signature_freeze_stage43',
'py scripts\register_daily_pipeline_task.py --warmup-universe --warmup-provider mock --universe-lookback-days 40 --warmup-frequency 1d --cache-root market_data --data-source-mode cached_real_first --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 2 --enable-live-signature-freeze --live-signature-freeze-output-dir live_signature_freeze --time 15:30',
'powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode scan',
'powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode status'
)
try { foreach ($cmd in $commands) { Invoke-LoggedCommand $cmd }; Add-Content -Path $LogPath -Encoding UTF8 -Value "Stage43 validation finished $(Get-Date -Format o) EXIT_CODE=0"; Write-Host "Stage43 validation passed. Log: $LogPath"; exit 0 } catch { Add-Content -Path $LogPath -Encoding UTF8 -Value "ERROR=$($_.Exception.Message)"; Add-Content -Path $LogPath -Encoding UTF8 -Value "Stage43 validation finished $(Get-Date -Format o) EXIT_CODE=1"; Write-Error "Stage43 validation failed. Log: $LogPath"; exit 1 }
