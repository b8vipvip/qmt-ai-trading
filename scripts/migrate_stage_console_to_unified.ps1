$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Map = @{
  'local_console_workflow_stage91'='artifacts/reports/console/workflow'; 'local_console_datahub_stage88'='artifacts/reports/console/datahub'; 'local_console_research_stage88'='artifacts/reports/console/research'; 'local_console_strategy_stage88'='artifacts/reports/console/strategy'; 'local_console_risk_stage88'='artifacts/reports/console/risk'; 'local_console_agent_stage81'='artifacts/reports/console/agent'; 'local_console_paper_stage89'='artifacts/reports/console/paper'; 'local_console_monitoring_stage83'='artifacts/reports/console/monitoring'; 'local_console_account_stage91'='artifacts/reports/console/account_readonly'; 'local_console_xtdata_live_stage87'='artifacts/reports/console/market'; 'local_console_market_stage84'='artifacts/reports/console/market'
}
$manifest=@()
foreach($src in $Map.Keys){ if(Test-Path $src){ New-Item -ItemType Directory -Force -Path $Map[$src] | Out-Null; Get-ChildItem $src -File -Include *.json,*.md -Recurse | ForEach-Object { $dest=Join-Path $Map[$src] $_.Name; Copy-Item $_.FullName $dest -Force; $manifest += [pscustomobject]@{source=$_.FullName; destination=$dest; status='COPIED'} } } else { $manifest += [pscustomobject]@{source=$src; destination=$Map[$src]; status='SOURCE_MISSING'} } }
New-Item -ItemType Directory -Force -Path 'artifacts/reports/console' | Out-Null
$manifest | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 'artifacts/reports/console/migration_manifest.json'
Write-Host "Unified console migration complete: artifacts/reports/console/migration_manifest.json"
