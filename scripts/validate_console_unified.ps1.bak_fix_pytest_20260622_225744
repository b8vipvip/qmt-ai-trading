param([string]$HostName='127.0.0.1',[int]$Port=18768)
$ErrorActionPreference='Continue'
$ts=Get-Date -Format 'yyyyMMdd_HHmmss'
New-Item -ItemType Directory -Force -Path 'validation_logs','artifacts/reports/console_validation'|Out-Null
$log="validation_logs/console_unified_validation_$ts.log"
$jsonOut='artifacts/reports/console_validation/latest_validation.json'
$mdOut='artifacts/reports/console_validation/latest_validation.md'
$results=@()
function Step($name,$cmd){
  Write-Host "== $name == $cmd"; $out=Invoke-Expression "$cmd 2>&1"; $code=$LASTEXITCODE; $out|Tee-Object -FilePath $log -Append; $results += @{name=$name; command=$cmd; exit_code=$code}; return $code
}
Step 'refresh artifacts' 'pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/refresh_console_artifacts.ps1'
Step 'compileall' 'py -m compileall qmt_ai_trading scripts'
Step 'pytest console unified' 'py -m pytest tests/test_console_unified_*.py'
$proc=Start-Process -FilePath 'py' -ArgumentList @('scripts/run_console_api.py','--host',$HostName,'--port',"$Port") -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 2
$apis=@('/api/v1/health','/api/v1/console/bootstrap','/api/v1/workflow/status','/api/v1/workflow/feature-matrix','/api/v1/datahub/status','/api/v1/datahub/symbols','/api/v1/datahub/cache/status','/api/v1/datahub/market/latest','/api/v1/research/context','/api/v1/research/factors/latest','/api/v1/research/candidates/latest','/api/v1/strategy/context','/api/v1/strategy/signals/latest','/api/v1/strategy/trade-intents/latest','/api/v1/risk/context','/api/v1/risk/decisions/latest','/api/v1/risk/report/latest','/api/v1/agents/context','/api/v1/agents/report/latest','/api/v1/backtest/shadow-replay/latest','/api/v1/paper-trading/status','/api/v1/paper-trading/orders/latest','/api/v1/paper-trading/positions/latest','/api/v1/paper-trading/pnl/latest','/api/v1/monitoring/context','/api/v1/monitoring/alerts/latest','/api/v1/monitoring/circuit-breaker/latest','/api/v1/approval/status','/api/v1/approval/requests/latest','/api/v1/account-readonly/status','/api/v1/account-readonly/diagnostics','/api/v1/account-readonly/asset','/api/v1/account-readonly/positions','/api/v1/safety/status','/api/v1/live/status')
$apiOk=$true
foreach($a in $apis){try{$r=Invoke-RestMethod "http://${HostName}:$Port$a"; if(($r|ConvertTo-Json -Depth 20) -match 'BACKEND_MISSING'){ $apiOk=$false }; foreach($k in 'read_only','dry_run','live_disabled','no_order_submitted','requires_human_approval'){ if(-not ($r.PSObject.Properties.Name -contains $k)){ $apiOk=$false } }; "$a OK"|Tee-Object -FilePath $log -Append}catch{$apiOk=$false; "$a FAIL $_"|Tee-Object -FilePath $log -Append}}
Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
$frontendOk=(Test-Path local_console_app/index.html) -and (Test-Path local_console_app/app.js) -and (Test-Path local_console_app/style.css) -and ((Get-Content local_console_app/app.js -Raw) -match '刷新') -and ((Get-Content local_console_app/app.js -Raw) -notmatch 'local_console_')
$serverOk=((Get-Content qmt_ai_trading/console_api/api_server.py -Raw) -notmatch 'local_console_')
Step 'sync scan' 'pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/sync_all.ps1 -Mode scan'
$summary=@{generated_at=(Get-Date).ToString('s'); api_smoke=$apiOk; frontend=$frontendOk; no_runtime_stage_dependency=$serverOk; safety='read_only dry_run live_disabled no_order_submitted account_masked requires_human_approval'; results=$results}
$summary|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 $jsonOut
@('# Console unified validation','',"- API smoke: $apiOk","- Frontend interactive files: $frontendOk","- No runtime stage dependency in api_server.py: $serverOk","- Log: $log")|Set-Content -Encoding UTF8 $mdOut
if($apiOk -and $frontendOk -and $serverOk){exit 0}else{exit 1}
