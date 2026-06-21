$ErrorActionPreference = "Stop"
$repoRoot = Join-Path $PSScriptRoot "qmt"
if (-not (Test-Path $repoRoot)) { $repoRoot = (Get-Location).Path }
$stage = Read-Host "请输入要验收的阶段号"
$logDir = Join-Path $repoRoot "validation_logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $repoRoot "validation_logs\stage${stage}_validation_${timestamp}.log"
$transcriptStarted = $false
try {
    try {
        Start-Transcript -Path $logPath -Force -Encoding UTF8 | Out-Null
        $transcriptStarted = $true
    } catch {
        "Start-Transcript failed, fallback logging enabled: $($_.Exception.Message)" | Tee-Object -FilePath $logPath -Encoding UTF8
    }
    Write-Host "验收日志路径: $logPath"
    Set-Location $repoRoot
    powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode pull
    $validateScript = ".\scripts\validate_stage${stage}.ps1"
    if (-not (Test-Path $validateScript)) { throw "找不到验收脚本: $validateScript" }
    powershell -ExecutionPolicy Bypass -File $validateScript
} catch {
    Write-Host "验收执行异常: $($_.Exception.Message)"
    if (-not $transcriptStarted) { "验收执行异常: $($_.Exception.Message)" | Out-File -FilePath $logPath -Append -Encoding UTF8 }
    throw
} finally {
    if ($transcriptStarted) { try { Stop-Transcript | Out-Null } catch {} }
    Write-Host "验收日志已保存到: $logPath"
}
