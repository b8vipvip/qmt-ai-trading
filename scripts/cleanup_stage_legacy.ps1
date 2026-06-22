param([switch]$Apply,[string]$Root='.')
& (Join-Path $PSScriptRoot 'audit_stage_legacy_inventory.ps1') -Root $Root
$plan=Get-Content (Join-Path $Root 'artifacts/reports/console_cleanup/tracked_stage_files.txt') -ErrorAction SilentlyContinue
if(-not $Apply){Write-Host 'DRY-RUN only. Re-run with --Apply to delete tracked legacy files after validation.'; $plan; exit 0}
foreach($p in $plan){ if($p -and (Test-Path (Join-Path $Root $p))){ Remove-Item -Recurse -Force (Join-Path $Root $p) }}
Write-Host 'Applied legacy cleanup plan.'
