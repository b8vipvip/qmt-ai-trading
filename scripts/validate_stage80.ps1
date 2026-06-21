$ErrorActionPreference = "Stop"

function Print-File([string]$Path) {
    Get-Content -LiteralPath $Path -Encoding UTF8 | Write-Host
}

function Check-NoBackup([string]$Dir, [string]$Pattern, [string]$Label, [string]$Kind) {
    if (Get-ChildItem -Path $Dir -Filter $Pattern -ErrorAction SilentlyContinue) {
        throw "$Label $Kind backup files found"
    }
}

function Clean-PythonCache {
    Get-ChildItem -Path . -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -Directory -Filter .pytest_cache | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

function Assert-RunTasksScriptReadOnlyReady {
    $parentRunScript = Join-Path (Split-Path -Parent (Get-Location)) "run_qmt_tasks.ps1"

    if (-not (Test-Path -LiteralPath $parentRunScript)) {
        throw "找不到总控脚本: $parentRunScript"
    }

    $runText = Get-Content -LiteralPath $parentRunScript -Raw -Encoding UTF8

    $requiredMarkers = @(
        "Read-Host",
        "sync_all.ps1",
        "validation_logs",
        'stage${stage}_validation_',
        'validate_stage${stage}.ps1',
        "Tee-Object",
        "验收日志已保存到"
    )

    foreach ($marker in $requiredMarkers) {
        if ($runText -notlike "*$marker*") {
            throw "run_qmt_tasks logging marker missing: $marker"
        }
    }

    $badMarkers = @("楠屾敹", "鏃ゅ織", "璇疯緭鍏", "�")
    foreach ($bad in $badMarkers) {
        if ($runText -like "*$bad*") {
            throw "run_qmt_tasks contains mojibake marker"
        }
    }

    return (Get-FileHash -LiteralPath $parentRunScript -Algorithm SHA256).Hash
}

function Assert-RunTasksScriptUnchanged([string]$BeforeHash) {
    $parentRunScript = Join-Path (Split-Path -Parent (Get-Location)) "run_qmt_tasks.ps1"
    $afterHash = (Get-FileHash -LiteralPath $parentRunScript -Algorithm SHA256).Hash
    if ($afterHash -ne $BeforeHash) {
        throw "validate_stage80.ps1 不允许修改 D:\AI\run_qmt_tasks.ps1，但检测到该文件内容发生变化"
    }
}

# 重要：Stage80 验收脚本只做只读检查，不再执行 install_run_qmt_tasks_logging.ps1，
# 避免验收过程中覆盖或修改 D:\AI\run_qmt_tasks.ps1。
$runTasksBeforeHash = Assert-RunTasksScriptReadOnlyReady

try {
    py -m compileall -q qmt_ai_trading

    py -m pytest tests/test_console_api_stage77.py
    py -m pytest tests/test_console_frontend_stage77.py
    py -m pytest tests/test_ai_provider_stage78.py
    py -m pytest tests/test_console_ai_frontend_stage78.py
    py -m pytest tests/test_factor_research_stage79.py
    py -m pytest tests/test_console_factor_frontend_stage79.py
    py -m pytest tests/test_factor_strategy_stage80.py
    py -m pytest tests/test_console_strategy_frontend_stage80.py
    py -m pytest tests/test_run_qmt_tasks_logging_stage80.py

    py scripts\run_factor_strategy_review.py --repo-root . --factor-dir local_console_factor_stage79 --output-dir local_console_strategy_stage80 --app-dir local_console_app_stage77

    Print-File local_console_strategy_stage80\factor_strategy_signals.md
    Print-File local_console_strategy_stage80\factor_trade_intents.md
    Print-File local_console_strategy_stage80\factor_risk_decisions.md
    Print-File local_console_strategy_stage80\factor_strategy_report.md
    Print-File local_console_strategy_stage80\frontend_strategy_contract.md
    Print-File local_console_strategy_stage80\next_agent_research_plan.md
    Print-File local_console_strategy_stage80\run_qmt_tasks_logging_fix_report.md

    py scripts\check_stage53_roadmap_plan.py

    Check-NoBackup scripts validate_stage79.ps1.bak_stage79fix_* Stage79 validate
    Check-NoBackup scripts validate_stage80.ps1.bak_stage80fix_* Stage80 validate

    Clean-PythonCache

    powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode scan
    powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode status
}
finally {
    Assert-RunTasksScriptUnchanged $runTasksBeforeHash
}
