# Stage53 validation runner. Writes stdout/stderr and EXIT_CODE to validation_logs/.
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$LogDir = Join-Path $Root "validation_logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogPath = Join-Path $LogDir "stage53_validation_$Stamp.log"
function Invoke-LoggedCommand { param([string]$Command, [switch]$ContinueOnFailure)
    Add-Content -Path $LogPath -Encoding UTF8 -Value "`n>>> $Command"
    $output = & powershell -NoProfile -Command $Command 2>&1
    $code = $LASTEXITCODE
    if ($null -ne $output) { Add-Content -Path $LogPath -Encoding UTF8 -Value ($output | Out-String) }
    Add-Content -Path $LogPath -Encoding UTF8 -Value "EXIT_CODE=$code"
    if ($code -ne 0) { if ($ContinueOnFailure) { $script:HadFailure = $true; return }; throw "Command failed with EXIT_CODE=$code`: $Command" }
}
$HadFailure = $false
Add-Content -Path $LogPath -Encoding UTF8 -Value "Stage53 validation started $(Get-Date -Format o)"
$commands = @(
'py -m compileall -q qmt_ai_trading',
'py -m pytest tests/test_final_authorization_stage39.py','py -m pytest tests/test_redline_review_stage40.py','py -m pytest tests/test_live_gray_ledger_stage41.py','py -m pytest tests/test_live_gray_review_stage42.py','py -m pytest tests/test_live_signature_freeze_stage43.py','py -m pytest tests/test_live_env_snapshot_stage44.py','py -m pytest tests/test_live_runbook_stage45.py','py -m pytest tests/test_live_signoff_stage46.py','py -m pytest tests/test_live_final_review_stage47.py','py -m pytest tests/test_live_archive_stage48.py','py -m pytest tests/test_live_consistency_stage49.py','py -m pytest tests/test_live_final_archive_stage50.py','py -m pytest tests/test_live_archive_lock_stage51.py','py -m pytest tests/test_live_lock_consistency_stage52.py','py -m pytest tests/test_live_archive_verification_stage53.py',
'py scripts/run_live_archive_verification.py --repo-root . --output-dir live_archive_verification_stage53 --output live_archive_verification_stage53/live_archive_verification.md --json-output live_archive_verification_stage53/live_archive_verification.json --locked-output live_archive_verification_stage53/locked_material_review.md --locked-json-output live_archive_verification_stage53/locked_material_review.json --human-output live_archive_verification_stage53/human_closure_recheck.md --human-json-output live_archive_verification_stage53/human_closure_recheck.json --plan-output live_archive_verification_stage53/next_readonly_check_plan.md --plan-json-output live_archive_verification_stage53/next_readonly_check_plan.json',
'if (Test-Path -LiteralPath ''live_archive_verification_stage53/live_archive_verification.md'') { Get-Content -LiteralPath ''live_archive_verification_stage53/live_archive_verification.md'' -Encoding UTF8 } else { Write-Output ''SKIPPED: live_archive_verification.md not generated'' }',
'if (Test-Path -LiteralPath ''live_archive_verification_stage53/locked_material_review.md'') { Get-Content -LiteralPath ''live_archive_verification_stage53/locked_material_review.md'' -Encoding UTF8 } else { Write-Output ''SKIPPED: locked_material_review.md not generated'' }',
'if (Test-Path -LiteralPath ''live_archive_verification_stage53/human_closure_recheck.md'') { Get-Content -LiteralPath ''live_archive_verification_stage53/human_closure_recheck.md'' -Encoding UTF8 } else { Write-Output ''SKIPPED: human_closure_recheck.md not generated'' }',
'if (Test-Path -LiteralPath ''live_archive_verification_stage53/next_readonly_check_plan.md'') { Get-Content -LiteralPath ''live_archive_verification_stage53/next_readonly_check_plan.md'' -Encoding UTF8 } else { Write-Output ''SKIPPED: next_readonly_check_plan.md not generated'' }',
'powershell -NoProfile -Command "Select-String -Path docs\qmt-ai-trading-project-roadmap.md -Pattern ''完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）'',''Stage61：API Gateway 基础层'',''Stage75：本地控制台封版 / 可选桌面化'',''UI 不能绕过 Risk Gate'',''UI 不能绕过 Human Approval'',''UI 不能自动 approve'',''UI 不直接访问 QMT''"',
'py scripts/warmup_etf_universe.py --lookback-days 40 --frequency 1d --provider mock --cache-root market_data_test_stage53',
'py scripts/run_daily_pipeline.py --cache-root market_data_test_stage53 --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 2 --enable-live-archive-verification --live-archive-verification-output-dir live_archive_verification_stage53',
'py scripts/run_scheduled_daily_pipeline.py --warmup-universe --warmup-provider mock --universe-lookback-days 40 --warmup-frequency 1d --cache-root market_data_test_stage53 --data-source-mode cached_real_first --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 2 --enable-live-archive-verification --live-archive-verification-output-dir live_archive_verification_stage53',
'py scripts/register_daily_pipeline_task.py --warmup-universe --warmup-provider mock --universe-lookback-days 40 --warmup-frequency 1d --cache-root market_data --data-source-mode cached_real_first --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 2 --enable-live-archive-verification --live-archive-verification-output-dir live_archive_verification --time 15:30',
'powershell -ExecutionPolicy Bypass -File ./scripts/sync_all.ps1 -Mode scan','powershell -ExecutionPolicy Bypass -File ./scripts/sync_all.ps1 -Mode status'
)
try { foreach ($cmd in $commands) { Invoke-LoggedCommand $cmd -ContinueOnFailure:($cmd -like 'py scripts/run_live_archive_verification.py*') }; if ($HadFailure) { throw "One or more continue-on-failure commands failed" }; Add-Content -Path $LogPath -Encoding UTF8 -Value "Stage53 validation finished $(Get-Date -Format o) EXIT_CODE=0"; Write-Host "Stage53 validation passed. Log: $LogPath"; exit 0 } catch { Add-Content -Path $LogPath -Encoding UTF8 -Value "ERROR=$($_.Exception.Message)"; Add-Content -Path $LogPath -Encoding UTF8 -Value "Stage53 validation finished $(Get-Date -Format o) EXIT_CODE=1"; Write-Error "Stage53 validation failed. Log: $LogPath"; exit 1 }
