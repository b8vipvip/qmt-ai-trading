param([string]$Root='.')
$ErrorActionPreference='Stop'
& (Join-Path $PSScriptRoot 'refresh_console_artifacts.ps1') -Root $Root
$base=Join-Path $Root 'artifacts/reports/console'
$manifest=@{generated_at=(Get-Date).ToString('s'); note='Legacy stage artifacts migrated only when matching unified names; formal API reads artifacts/reports/console only.'; migrated=@()}
$manifest|ConvertTo-Json -Depth 6|Set-Content -Encoding UTF8 (Join-Path $base 'migration_manifest.json')
Write-Host 'migration manifest generated'
