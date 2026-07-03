param(
  [string]$ApiBase = "http://127.0.0.1:8768/api/v1",
  [switch]$RequireApi
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$logDir = Join-Path $repoRoot "artifacts\reports\console\validation_logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir ("local_console_workbench_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))

function Write-Log {
  param([string]$Message)
  $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
  Write-Host $line
  Add-Content -Path $logFile -Value $line -Encoding UTF8
}

function Assert-Ok {
  param([bool]$Condition, [string]$Message)
  if (-not $Condition) { Write-Log "FAIL $Message"; throw $Message }
  Write-Log "OK $Message"
}

Write-Log "START local console workbench validation"

$requiredFiles = @(
  "local_console_app\index.html",
  "local_console_app\app.js",
  "local_console_app\task_params.js",
  "local_console_app\workbench.css",
  "local_console_app\workbench_overrides.js"
)
foreach ($file in $requiredFiles) { Assert-Ok (Test-Path $file) "required file exists: $file" }

$index = Get-Content "local_console_app\index.html" -Raw -Encoding UTF8
$override = Get-Content "local_console_app\workbench_overrides.js" -Raw -Encoding UTF8
$css = Get-Content "local_console_app\workbench.css" -Raw -Encoding UTF8

foreach ($text in @("workbench.css", "workbench_overrides.js", "Data Hub 数据源中心", "Agent 投研工作台", "Strategy Engine 策略工作台", "后端待接入", "order_preview_dry_run")) {
  Assert-Ok ($index.Contains($text) -or $override.Contains($text) -or $css.Contains($text)) "frontend contains: $text"
}

Assert-Ok ($css.Contains("capability-grid")) "workbench styles loaded"
Assert-Ok ($override.Contains("buildNav();show('overview')")) "workbench override rebuilds nav and initial page"

$apiOk = $false
try {
  $health = Invoke-RestMethod "$ApiBase/health" -TimeoutSec 5
  $apiOk = $true
  Write-Log "API health ok service=$($health.service)"
} catch {
  Write-Log "WARN API unavailable: $($_.Exception.Message)"
  if ($RequireApi) { throw }
}

if ($apiOk) {
  foreach ($ep in @("/console/bootstrap", "/datahub/status", "/research/candidates/latest", "/strategy/signals/latest", "/portfolio/status", "/tasks/catalog")) {
    $res = Invoke-RestMethod "$ApiBase$ep" -TimeoutSec 10
    Assert-Ok ($null -ne $res) "API endpoint reachable: $ep"
  }
  $catalog = Invoke-RestMethod "$ApiBase/tasks/catalog" -TimeoutSec 10
  $taskIds = @($catalog.tasks | ForEach-Object { $_.task_id })
  foreach ($taskId in @("xtdata_live_readonly_smoke", "factor_scan", "strategy_dry_run_signals", "risk_gate_dry_run", "paper_trading_dry_run", "human_approval_review_dry_run", "order_preview_dry_run")) {
    Assert-Ok ($taskIds -contains $taskId) "workflow task is whitelisted: $taskId"
  }
}

Write-Log "DONE local console workbench validation log=$logFile"
Write-Host "`n[OK] local console workbench validation passed"
Write-Host "[LOG] $logFile"
