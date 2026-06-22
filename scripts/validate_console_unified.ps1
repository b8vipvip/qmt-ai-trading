$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ValidationDir = "artifacts\reports\console_validation"
$LogDir = "validation_logs"
New-Item -ItemType Directory -Force $ValidationDir | Out-Null
New-Item -ItemType Directory -Force $LogDir | Out-Null

$LogPath = Join-Path $LogDir "console_unified_validation_$Stamp.log"
$JsonPath = Join-Path $ValidationDir "latest_validation.json"
$MdPath = Join-Path $ValidationDir "latest_validation.md"

$Steps = New-Object System.Collections.Generic.List[object]

function Write-Log {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Write-Host $line
    Add-Content -Path $LogPath -Value $line -Encoding UTF8
}

function Add-Step {
    param(
        [string]$Name,
        [bool]$Ok,
        [string]$Message
    )
    $Steps.Add([pscustomobject]@{
        name = $Name
        ok = $Ok
        message = $Message
        time = (Get-Date).ToString("s")
    }) | Out-Null
}

function Run-Native {
    param(
        [string]$Name,
        [scriptblock]$Block
    )

    Write-Log "== $Name =="
    try {
        & $Block 2>&1 | Tee-Object -FilePath $LogPath -Append
        if ($LASTEXITCODE -ne 0) {
            throw "$Name failed with exit code $LASTEXITCODE"
        }
        Add-Step $Name $true "PASS"
    } catch {
        Add-Step $Name $false $_.Exception.Message
        throw
    }
}

try {
    Run-Native "refresh artifacts" {
        powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\refresh_console_artifacts.ps1"
    }

    Run-Native "compileall" {
        py -m compileall qmt_ai_trading scripts
    }

    Write-Log "== pytest console unified =="
    $UnifiedTests = Get-ChildItem -Path "tests" -Filter "test_console_unified_*.py" -File |
        Sort-Object Name |
        ForEach-Object { $_.FullName }

    if (-not $UnifiedTests -or $UnifiedTests.Count -eq 0) {
        throw "No unified console tests found: tests/test_console_unified_*.py"
    }

    Write-Log ("Unified console tests: " + ($UnifiedTests.Count))
    py -m pytest @UnifiedTests -vv -ra --tb=short 2>&1 | Tee-Object -FilePath $LogPath -Append
    if ($LASTEXITCODE -ne 0) {
        Add-Step "pytest console unified" $false "pytest failed with exit code $LASTEXITCODE"
        throw "pytest failed with exit code $LASTEXITCODE"
    }
    Add-Step "pytest console unified" $true "PASS"

    Write-Log "== API smoke =="
    $Port = 18768
    $Server = Start-Process -FilePath "py" -ArgumentList @(
        "scripts\run_console_api.py",
        "--host", "127.0.0.1",
        "--port", "$Port"
    ) -PassThru -WindowStyle Hidden

    try {
        $base = "http://127.0.0.1:$Port"

        $ready = $false
        for ($i = 0; $i -lt 20; $i++) {
            try {
                $health = Invoke-RestMethod "$base/api/v1/health" -TimeoutSec 3
                if ($health.ok -and $health.service -eq "unified_local_console") {
                    $ready = $true
                    break
                }
            } catch {
                Start-Sleep -Milliseconds 500
            }
        }

        if (-not $ready) {
            throw "console api server not ready"
        }

        $routes = @(
            "/api/v1/health",
            "/api/v1/console/bootstrap",
            "/api/v1/workflow/status",
            "/api/v1/workflow/feature-matrix",
            "/api/v1/datahub/status",
            "/api/v1/datahub/symbols",
            "/api/v1/datahub/cache/status",
            "/api/v1/datahub/market/latest",
            "/api/v1/research/context",
            "/api/v1/research/factors/latest",
            "/api/v1/research/candidates/latest",
            "/api/v1/strategy/context",
            "/api/v1/strategy/signals/latest",
            "/api/v1/strategy/trade-intents/latest",
            "/api/v1/risk/context",
            "/api/v1/risk/decisions/latest",
            "/api/v1/risk/report/latest",
            "/api/v1/agents/context",
            "/api/v1/agents/report/latest",
            "/api/v1/backtest/shadow-replay/latest",
            "/api/v1/paper-trading/status",
            "/api/v1/paper-trading/orders/latest",
            "/api/v1/paper-trading/positions/latest",
            "/api/v1/paper-trading/pnl/latest",
            "/api/v1/monitoring/context",
            "/api/v1/monitoring/alerts/latest",
            "/api/v1/monitoring/circuit-breaker/latest",
            "/api/v1/approval/status",
            "/api/v1/approval/requests/latest",
            "/api/v1/account-readonly/status",
            "/api/v1/account-readonly/diagnostics",
            "/api/v1/account-readonly/asset",
            "/api/v1/account-readonly/positions",
            "/api/v1/safety/status",
            "/api/v1/live/status"
        )

        foreach ($route in $routes) {
            $res = Invoke-RestMethod "$base$route" -TimeoutSec 5

            if ($res.ok -ne $true) {
                throw "$route returned ok != true"
            }

            $json = $res | ConvertTo-Json -Depth 20
            if ($json -match "BACKEND_MISSING") {
                throw "$route returned BACKEND_MISSING"
            }
            if ($json -match '"real_order_submitted"\s*:\s*true') {
                throw "$route returned real_order_submitted=true"
            }
            if ($json -match '"order_submit_enabled"\s*:\s*true') {
                throw "$route returned order_submit_enabled=true"
            }
            if ($json -match '"order_cancel_enabled"\s*:\s*true') {
                throw "$route returned order_cancel_enabled=true"
            }

            Write-Log "$route OK"
        }

        Add-Step "api smoke" $true "PASS"
    } finally {
        Stop-Process -Id $Server.Id -Force -ErrorAction SilentlyContinue
    }

    Run-Native "sync scan" {
        powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\sync_all.ps1" -Mode scan
    }

    $Result = [pscustomobject]@{
        ok = $true
        status = "PASS"
        generated_at = (Get-Date).ToString("s")
        log_path = $LogPath
        steps = $Steps
        safety = @{
            read_only = $true
            dry_run = $true
            live_disabled = $true
            no_order_submitted = $true
            order_submit_enabled = $false
            order_cancel_enabled = $false
            real_order_submitted = $false
        }
    }

    $Result | ConvertTo-Json -Depth 8 | Set-Content -Path $JsonPath -Encoding UTF8

    @"
# Unified Console Validation

Status: PASS

Generated: $($Result.generated_at)

Log: $LogPath

## Safety

- read_only: true
- dry_run: true
- live_disabled: true
- no_order_submitted: true
- order_submit_enabled: false
- order_cancel_enabled: false
- real_order_submitted: false

## Steps

$($Steps | ForEach-Object { "- $($_.name): $($_.ok) - $($_.message)" } | Out-String)
"@ | Set-Content -Path $MdPath -Encoding UTF8

    Write-Log "Validation PASS"
    Write-Log "Report: $MdPath"
    Write-Log "JSON: $JsonPath"
    exit 0
} catch {
    $err = $_.Exception.Message
    Write-Log "Validation FAILED: $err"

    $Result = [pscustomobject]@{
        ok = $false
        status = "FAILED"
        error = $err
        generated_at = (Get-Date).ToString("s")
        log_path = $LogPath
        steps = $Steps
    }

    $Result | ConvertTo-Json -Depth 8 | Set-Content -Path $JsonPath -Encoding UTF8

    @"
# Unified Console Validation

Status: FAILED

Generated: $($Result.generated_at)

Error: $err

Log: $LogPath
"@ | Set-Content -Path $MdPath -Encoding UTF8

    exit 1
}
