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
  if (-not $Condition) {
    Write-Log "FAIL $Message"
    throw $Message
  }
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

foreach ($file in $requiredFiles) {
  Assert-Ok (Test-Path $file) "required file exists: $file"
}

$index = Get-Content "local_console_app\index.html" -Raw
$app = Get-Content "local_console_app\app.js" -Raw
$tasks = Get-Content "local_console_app\task_params.js" -Raw
$override = Get-Content "local_console_app\workbench_overrides.js" -Raw
$css = Get-Content "local_console_app\workbench.css" -Raw
$frontendText = "$index`n$app`n$tasks`n$override`n$css"

$mustContain = @(
  "workbench.css",
  "workbench_overrides.js",
  "datahub",
  "research",
  "agent",
  "strategy",
  "capability-grid",
  "capability-item",
  "order_preview_dry_run",
  "TASK_PARAM_PRESETS",
  "DRYRUN_WORKFLOW",
  "renderWorkflowPanel",
  "runDryRunWorkflow",
  "workflow-snapshot-grid",
  "task-history-panel",
  "refreshTaskHistory",
  "viewTaskLogs",
  "任务历史 / 日志中心",
  "can_submit_order=false",
  "buildNav();",
  "show('overview')"
)

foreach ($text in $mustContain) {
  Assert-Ok $frontendText.Contains($text) "frontend contains token: $text"
}

$dangerPatterns = @(
  "allow_order_submit: true",
  "allow_order_cancel: true",
  "order_submit_enabled: true",
  "order_cancel_enabled: true",
  "real_order_submitted: true",
  "live_trading_enabled: true"
)

foreach ($text in $dangerPatterns) {
  Assert-Ok (-not $frontendText.Contains($text)) "frontend does not enable dangerous flag: $text"
}

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
  $endpoints = @(
    "/console/bootstrap",
    "/workflow/status",
    "/workflow/feature-matrix",
    "/datahub/status",
    "/datahub/market/latest",
    "/research/candidates/latest",
    "/strategy/signals/latest",
    "/risk/decisions/latest",
    "/paper-trading/orders/latest",
    "/approval/requests/latest",
    "/portfolio/status",
    "/portfolio/order-preview/latest",
    "/tasks/catalog",
    "/tasks/history"
  )

  foreach ($ep in $endpoints) {
    $res = Invoke-RestMethod "$ApiBase$ep" -TimeoutSec 10
    Assert-Ok ($null -ne $res) "API endpoint reachable: $ep"
  }

  $history = Invoke-RestMethod "$ApiBase/tasks/history" -TimeoutSec 10
  Assert-Ok ($history.status -eq "READY") "task history endpoint reports READY"
  Assert-Ok ($null -ne $history.runs) "task history endpoint exposes runs array"

  $catalog = Invoke-RestMethod "$ApiBase/tasks/catalog" -TimeoutSec 10
  $taskIds = @($catalog.tasks | ForEach-Object { $_.task_id })
  $requiredTasks = @(
    "xtdata_live_readonly_smoke",
    "factor_scan",
    "strategy_dry_run_signals",
    "risk_gate_dry_run",
    "paper_trading_dry_run",
    "human_approval_review_dry_run",
    "order_preview_dry_run"
  )

  foreach ($taskId in $requiredTasks) {
    Assert-Ok ($taskIds -contains $taskId) "workflow task is whitelisted: $taskId"
  }

  $portfolio = Invoke-RestMethod "$ApiBase/portfolio/status" -TimeoutSec 10
  if ($null -ne $portfolio.can_submit_order) {
    Assert-Ok ($portfolio.can_submit_order -eq $false) "portfolio can_submit_order remains false"
  }
}

Write-Log "DONE local console workbench validation log=$logFile"
Write-Host ""
Write-Host "[OK] local console workbench validation passed"
Write-Host "[LOG] $logFile"
