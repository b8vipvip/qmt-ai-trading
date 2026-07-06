param(
    [ValidateSet('plan','archive','delete')]
    [string]$Mode = 'plan',

    [switch]$IncludeCaches,

    [string]$ArchiveRoot = 'artifacts\cleanup_archive'
)

$ErrorActionPreference = 'Stop'

function Write-Info($Message) { Write-Host $Message -ForegroundColor Cyan }
function Write-Ok($Message) { Write-Host $Message -ForegroundColor Green }
function Write-Warn($Message) { Write-Host $Message -ForegroundColor Yellow }
function Write-Bad($Message) { Write-Host $Message -ForegroundColor Red }

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $RepoRoot

Write-Info '========== qmt-ai-trading local workspace cleanup =========='
Write-Info "Repo root: $RepoRoot"
Write-Info "Mode:      $Mode"
Write-Host ''

Write-Info 'Canonical project layout:'
Write-Host '  Frontend workbench: local_console_app\'
Write-Host '  Backend API:        qmt_ai_trading\console_api\'
Write-Host '  API launcher:       scripts\run_console_api.py'
Write-Host '  Current artifacts:  artifacts\reports\console\'
Write-Host '  Main package:       qmt_ai_trading\'
Write-Host ''

$KeepNames = @(
    '.git', '.github', '.pytest_cache',
    'docs', 'scripts', 'tests',
    'qmt_ai_trading', 'local_console_app',
    'artifacts', 'market_data', 'reports', 'logs',
    'research', 'risk', 'strategies', 'signals',
    'shadow', 'shadow_replay', 'shadow_trading',
    'runs', 'backtest_results', 'data_tools', 'ai_tools',
    'qmt_gateway', 'gjzqqmt'
)

$KeepFiles = @(
    '.env', '.env.example', '.gitignore',
    'README.md', 'config.json', 'config.example.json',
    'ai_providers.example.json', 'qmt量化文档.txt'
)

function Show-PostCleanupGitHint {
    Write-Host ''
    Write-Warn 'Post-cleanup Git note:'
    Write-Host '  1) Cleanup archive is local backup and ignored by Git.'
    Write-Host '  2) Runtime account/report files should not be committed.'
    Write-Host '  3) If status is clean after pull, no commit is needed locally.'
    Write-Host ''
    Write-Host 'Suggested check commands:'
    Write-Host '  git status --short'
    Write-Host '  powershell -ExecutionPolicy Bypass -File .\scripts\validate_local_console_workbench.ps1 -RequireApi'
}

function Is-LegacyStageDirectory($Name) {
    if ($KeepNames -contains $Name) { return $false }
    if ($Name -eq 'local_console_app') { return $false }
    if ($Name -match '(^|_)stage\d+($|_)') { return $true }
    if ($Name -match '^stage\d+_') { return $true }
    if ($Name -match '^local_console_.*_stage\d+$') { return $true }
    if ($Name -match '^local_runtime_.*_stage\d+$') { return $true }
    return $false
}

function Is-LocalRuntimeDirectory($Name) {
    if ($Name -eq 'qmt_data_quality_reports') { return $true }
    if ($Name -eq 'validation_logs') { return $true }
    return $false
}

function Is-LegacyRootFile($Name) {
    if ($KeepFiles -contains $Name) { return $false }
    if ($Name -match '^config\.json\.bak_') { return $true }
    if ($Name -match '^fix_.*\.py$') { return $true }
    if ($Name -match '^patch_.*\.py$') { return $true }
    if ($Name -eq 'update_qmt_project_old_broken.ps1') { return $true }
    return $false
}

$DirCandidates = @(Get-ChildItem -LiteralPath $RepoRoot -Directory | Where-Object { (Is-LegacyStageDirectory $_.Name) -or (Is-LocalRuntimeDirectory $_.Name) })
$FileCandidates = @(Get-ChildItem -LiteralPath $RepoRoot -File | Where-Object { Is-LegacyRootFile $_.Name })

if ($IncludeCaches) {
    $cacheNames = @('.pytest_cache')
    $extraCaches = @(Get-ChildItem -LiteralPath $RepoRoot -Directory | Where-Object { $cacheNames -contains $_.Name })
    $DirCandidates += $extraCaches

    $nestedPyCaches = @(Get-ChildItem -LiteralPath $RepoRoot -Directory -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq '__pycache__' })
    $DirCandidates += $nestedPyCaches
}

$Candidates = @($DirCandidates + $FileCandidates | Sort-Object FullName -Unique)

if (-not $Candidates.Count) {
    Write-Ok 'No cleanup candidates found.'
    Show-PostCleanupGitHint
    exit 0
}

Write-Warn "Cleanup candidates: $($Candidates.Count)"
$Candidates | ForEach-Object {
    $kind = if ($_.PSIsContainer) { 'DIR ' } else { 'FILE' }
    $rel = Resolve-Path -LiteralPath $_.FullName -Relative
    Write-Host ("  [{0}] {1}" -f $kind, $rel)
}
Write-Host ''

if ($Mode -eq 'plan') {
    Write-Ok 'PLAN only. No file was changed.'
    Write-Host 'Next step after manual review:'
    Write-Host '  powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_local_workspace.ps1 -Mode archive -IncludeCaches'
    Show-PostCleanupGitHint
    exit 0
}

if ($Mode -eq 'archive') {
    $Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $ArchiveDir = Join-Path $RepoRoot (Join-Path $ArchiveRoot $Stamp)
    New-Item -ItemType Directory -Force -Path $ArchiveDir | Out-Null

    $manifest = @()
    foreach ($item in $Candidates) {
        $relative = Resolve-Path -LiteralPath $item.FullName -Relative
        $safeName = $relative.TrimStart('.\').Replace('\', '__').Replace(':', '')
        $target = Join-Path $ArchiveDir $safeName
        Move-Item -LiteralPath $item.FullName -Destination $target -Force
        $manifest += [pscustomobject]@{
            original = $relative
            archived_to = (Resolve-Path -LiteralPath $target -Relative)
            type = if ($item.PSIsContainer) { 'directory' } else { 'file' }
        }
        Write-Ok "ARCHIVED $relative"
    }

    $manifestPath = Join-Path $ArchiveDir 'cleanup_manifest.json'
    $manifest | ConvertTo-Json -Depth 5 | Set-Content -Path $manifestPath -Encoding UTF8
    Write-Ok "Archive done: $ArchiveDir"
    Write-Ok "Manifest:     $manifestPath"
    Write-Warn 'Run the console again after archive. If everything is normal, you can later delete the archive folder manually.'
    Show-PostCleanupGitHint
    exit 0
}

if ($Mode -eq 'delete') {
    Write-Bad 'DELETE mode selected. This removes candidates permanently.'
    Write-Warn 'Press Ctrl+C within 8 seconds to cancel...'
    Start-Sleep -Seconds 8

    foreach ($item in $Candidates) {
        $relative = Resolve-Path -LiteralPath $item.FullName -Relative
        Remove-Item -LiteralPath $item.FullName -Recurse -Force
        Write-Ok "DELETED $relative"
    }

    Write-Ok 'Delete done.'
    Show-PostCleanupGitHint
}