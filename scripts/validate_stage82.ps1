$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$LogDir = Join-Path $RepoRoot 'validation_logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Log = Join-Path $LogDir ('stage82_validation_direct_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')

# 统一 UTF-8 with BOM，兼容 Windows PowerShell 5.1。
$Utf8WithBom = New-Object System.Text.UTF8Encoding($true)
[System.IO.File]::WriteAllText($Log, '', $Utf8WithBom)

function Write-ValidationLogLine {
    param([AllowEmptyString()][string]$Message = '')
    Write-Host $Message
    Add-Content -LiteralPath $Log -Value $Message -Encoding UTF8
}

function Run-Step {
    param([Parameter(Mandatory = $true)][string]$Command)

    Write-ValidationLogLine ("> " + $Command)

    # 不使用  / Out-File / > / >> 写日志。
    # Windows PowerShell 5.1 下这些写法容易写成 UTF-16LE，和 UTF-8 日志混写后出现 NUL 空字符。
    & cmd.exe /d /c $Command 2>&1 | ForEach-Object {
        $line = $_ | Out-String
        $line = $line.TrimEnd("`r", "`n")
        Write-ValidationLogLine $line
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $Command"
    }
}

function Get-HashIfExists {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return ''
    }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Restore-GeneratedStage82Outputs {
    # Stage82 输出是回测看板生成物。重复验收时这些文件可能因为 created_at 等字段变化而变 Dirty。
    # 验收只证明生成流程可跑；最终仓库必须保持干净，所以恢复已跟踪输出文件，删除临时 out/。
    Remove-Item -Recurse -Force (Join-Path $RepoRoot 'out') -ErrorAction SilentlyContinue

    $tracked = git ls-files -- local_console_backtest_stage82 2>$null
    if (-not [string]::IsNullOrWhiteSpace(($tracked | Out-String))) {
        git checkout -- local_console_backtest_stage82 2>$null
        git clean -fd -- local_console_backtest_stage82 2>$null
    }
}

$Runner = 'D:\AI\run_qmt_tasks.ps1'
$SyncAll = Join-Path $RepoRoot 'scripts\sync_all.ps1'

$RunnerHashBefore = Get-HashIfExists $Runner
$SyncAllHashBefore = Get-HashIfExists $SyncAll

Write-ValidationLogLine 'Stage82 validation: read-only checks; does not modify D:\AI\run_qmt_tasks.ps1; does not modify scripts\sync_all.ps1.'

if (Test-Path -LiteralPath $Runner) {
    $runnerText = Get-Content -LiteralPath $Runner -Raw -Encoding UTF8
    foreach ($marker in @('Read-Host', 'sync_all.ps1', 'validation_logs', '验收日志已保存到')) {
        if ($runnerText -notlike "*$marker*") {
            throw "run_qmt_tasks.ps1 logging marker missing: $marker"
        }
    }
    Write-ValidationLogLine 'run_qmt_tasks.ps1 checked read-only.'
} else {
    Write-ValidationLogLine 'run_qmt_tasks.ps1 missing; read-only check only.'
}

if (-not (Test-Path -LiteralPath $SyncAll)) {
    throw "sync_all.ps1 missing: $SyncAll"
}

# 清理上一次验收留下的临时产物，避免历史 Dirty 干扰本次验收。
Restore-GeneratedStage82Outputs

try {
    Run-Step 'py -m compileall -q qmt_ai_trading'

    $tests = @(
        'tests/test_console_api_stage77.py',
        'tests/test_console_frontend_stage77.py',
        'tests/test_ai_provider_stage78.py',
        'tests/test_console_ai_frontend_stage78.py',
        'tests/test_factor_research_stage79.py',
        'tests/test_console_factor_frontend_stage79.py',
        'tests/test_factor_strategy_stage80.py',
        'tests/test_console_strategy_frontend_stage80.py',
        'tests/test_run_qmt_tasks_logging_stage80.py',
        'tests/test_agent_research_stage81.py',
        'tests/test_console_agent_frontend_stage81.py',
        'tests/test_agent_safety_stage81.py',
        'tests/test_backtest_dashboard_stage82.py',
        'tests/test_console_backtest_frontend_stage82.py',
        'tests/test_backtest_dashboard_safety_stage82.py'
    )

    foreach ($t in $tests) {
        Run-Step "py -m pytest $t"
    }

    Run-Step 'py scripts\run_backtest_dashboard_stage82.py --repo-root . --output-dir local_console_backtest_stage82'

    # 关键：运行验证生成流程后，恢复可重复生成的输出目录，保证 status 不因为时间戳/报告刷新变 Dirty。
    Restore-GeneratedStage82Outputs

    Run-Step 'powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode scan'
    Run-Step 'powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode status'

    Write-ValidationLogLine 'Stage82 validation completed.'
}
finally {
    $RunnerHashAfter = Get-HashIfExists $Runner
    $SyncAllHashAfter = Get-HashIfExists $SyncAll

    if ($RunnerHashBefore -ne $RunnerHashAfter) {
        throw 'validate_stage82.ps1 不允许修改 D:\AI\run_qmt_tasks.ps1，但检测到该文件内容发生变化'
    }

    if ($SyncAllHashBefore -ne $SyncAllHashAfter) {
        throw 'validate_stage82.ps1 不允许修改 scripts\sync_all.ps1，但检测到该文件内容发生变化'
    }

    if (Test-Path -LiteralPath $Log) {
        $content = Get-Content -LiteralPath $Log -Raw -Encoding UTF8
        if ($content -like "*`0*") {
            throw 'validate_stage82.ps1 生成的内部日志仍包含 NUL 空字符'
        }
        [System.IO.File]::WriteAllText($Log, $content, $Utf8WithBom)
    }
}
