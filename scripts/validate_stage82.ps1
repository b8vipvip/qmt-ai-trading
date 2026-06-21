$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot
$logDir = Join-Path $RepoRoot 'validation_logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir ('stage82_validation_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
function Run-Step($cmd) {
  Add-Content -Path $log -Value ("> " + $cmd) -Encoding UTF8
  cmd /c $cmd 2>&1 | Tee-Object -FilePath $log -Append
  if ($LASTEXITCODE -ne 0) { throw "Command failed: $cmd" }
}
Add-Content -Path $log -Value 'Stage82 validation: read-only checks; does not modify D:\AI\run_qmt_tasks.ps1; does not modify scripts\sync_all.ps1.' -Encoding UTF8
$runner='D:\AI\run_qmt_tasks.ps1'
if (Test-Path $runner) { Select-String -Path $runner -Pattern 'QMT_TASK_LOGGING_INSTALLED' -SimpleMatch | Out-Null; Add-Content -Path $log -Value 'run_qmt_tasks.ps1 checked read-only.' -Encoding UTF8 } else { Add-Content -Path $log -Value 'run_qmt_tasks.ps1 missing; read-only check only.' -Encoding UTF8 }
Run-Step 'py -m compileall -q qmt_ai_trading'
$tests=@('tests/test_console_api_stage77.py','tests/test_console_frontend_stage77.py','tests/test_ai_provider_stage78.py','tests/test_console_ai_frontend_stage78.py','tests/test_factor_research_stage79.py','tests/test_console_factor_frontend_stage79.py','tests/test_factor_strategy_stage80.py','tests/test_console_strategy_frontend_stage80.py','tests/test_run_qmt_tasks_logging_stage80.py','tests/test_agent_research_stage81.py','tests/test_console_agent_frontend_stage81.py','tests/test_agent_safety_stage81.py','tests/test_backtest_dashboard_stage82.py','tests/test_console_backtest_frontend_stage82.py','tests/test_backtest_dashboard_safety_stage82.py')
foreach($t in $tests){ Run-Step "py -m pytest $t" }
Run-Step 'py scripts\run_backtest_dashboard_stage82.py --repo-root . --output-dir local_console_backtest_stage82'
Run-Step 'powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode scan'
Run-Step 'powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode status'
Add-Content -Path $log -Value 'Stage82 validation completed.' -Encoding UTF8
