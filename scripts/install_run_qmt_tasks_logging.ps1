$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$aiRoot = Split-Path -Parent $repoRoot
$target = Join-Path $aiRoot "run_qmt_tasks.ps1"
$validationDir = Join-Path $repoRoot "validation_logs"
New-Item -ItemType Directory -Force -Path $validationDir | Out-Null
$script = @'
$ErrorActionPreference = "Stop"
$stage = Read-Host "请输入要验收的阶段号 stage"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Join-Path $scriptRoot "qmt"
$logDir = Join-Path $repoRoot "validation_logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $logDir ("stage${stage}_validation_${timestamp}.log")
$transcriptStarted = $false
$fallbackLines = New-Object System.Collections.Generic.List[string]
function Write-Logged([string]$Message) { Write-Host $Message; if (-not $transcriptStarted) { $fallbackLines.Add($Message) | Out-Null } }
try {
    try { Start-Transcript -Path $logPath -Force | Out-Null; $transcriptStarted = $true } catch { $fallbackLines.Add("Start-Transcript failed, fallback to UTF-8 Out-File: $($_.Exception.Message)") | Out-Null }
    Write-Logged "QMT AI Trading Stage $stage validation started"
    Set-Location $repoRoot
    powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode pull
    $validate = Join-Path $repoRoot ("scripts\validate_stage${stage}.ps1")
    if (-not (Test-Path -LiteralPath $validate)) { throw "validate script not found: $validate" }
    powershell -ExecutionPolicy Bypass -File $validate
}
finally {
    if ($transcriptStarted) { try { Stop-Transcript | Out-Null } catch { } }
    else { $fallbackLines | Out-File -FilePath $logPath -Encoding UTF8 -Force }
    try { $content = Get-Content -LiteralPath $logPath -Raw -ErrorAction SilentlyContinue; if ($null -ne $content) { Set-Content -LiteralPath $logPath -Value $content -Encoding UTF8 -Force } } catch { }
    Write-Host "验收日志已保存到: $logPath"
}
'@
Set-Content -LiteralPath $target -Value $script -Encoding UTF8 -Force
$report = @{
  ok = $true; target = $target; validation_logs = $validationDir;
  required_markers = @('run_qmt_tasks.ps1','validation_logs','stage${stage}_validation_','Start-Transcript','Stop-Transcript','try','finally','验收日志已保存到')
}
Write-Host "run_qmt_tasks.ps1 logging installed: $target"
Write-Host "validation_logs directory: $validationDir"
