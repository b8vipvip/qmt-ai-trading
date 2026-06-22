param([string]$Root='.')
$out=Join-Path $Root 'artifacts/reports/console_cleanup'; New-Item -ItemType Directory -Force -Path $out|Out-Null
$tracked=git -C $Root ls-files | Select-String -Pattern '(^|/)(local_console_.*stage\d+|market_data_test_stage\d+|agent_reports_stage\d+|monitoring_reports_stage\d+|dashboard_stage\d+|tests/test_.*stage\d+.*\.py|scripts/(validate_stage\d+\.ps1|run_.*stage\d+.*\.py|.*\.bak_.*))$'
$tracked | ForEach-Object {$_.Line} | Set-Content -Encoding UTF8 (Join-Path $out 'tracked_stage_files.txt')
Get-ChildItem -Path $Root -Force | Where-Object {$_.Name -match '^(local_console_.*stage\d+|market_data_test_stage\d+|agent_reports_stage\d+|monitoring_reports_stage\d+|dashboard_stage\d+)$'} | Select-Object -ExpandProperty Name | Set-Content -Encoding UTF8 (Join-Path $out 'worktree_stage_items.txt')
git -C $Root ls-files 'scripts/*.bak_*' | Set-Content -Encoding UTF8 (Join-Path $out 'tracked_backup_files.txt')
@('# Legacy cleanup dry-run plan','','Delete only after validate_console_unified.ps1 and sync_all.ps1 -Mode scan pass.','','See tracked_stage_files.txt and worktree_stage_items.txt.','Safety: .env/config.json/core modules are excluded.') | Set-Content -Encoding UTF8 (Join-Path $out 'delete_plan.md')
Write-Host "inventory written to $out"
