$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
python -m compileall qmt_ai_trading scripts
pytest tests/test_console_unified_frontend.py tests/test_console_unified_api.py tests/test_console_unified_safety.py tests/test_console_unified_no_stage_labels.py
$port=18768
$p = Start-Process -FilePath python -ArgumentList @('scripts/run_console_api.py','--host','127.0.0.1','--port',"$port") -PassThru -WindowStyle Hidden
try { Start-Sleep -Seconds 2; $h=Invoke-RestMethod "http://127.0.0.1:$port/api/v1/health"; if($h.service -ne 'unified_local_console'){ throw 'health service mismatch' }; $b=Invoke-RestMethod "http://127.0.0.1:$port/api/v1/console/bootstrap"; if(-not $b.read_only){ throw 'safety mismatch' } } finally { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
if(Test-Path scripts/sync_all.ps1){ powershell -ExecutionPolicy Bypass -File scripts/sync_all.ps1 -Mode scan } else { Write-Host 'sync_all.ps1 missing; privacy scan skipped' }
