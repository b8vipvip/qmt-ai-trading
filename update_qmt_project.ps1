# -*- coding: utf-8 -*-
[CmdletBinding()]
param([switch]$AutoPatchConfig)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$logsDir = Join-Path $root "logs"
New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$timestampLog = Join-Path $logsDir ("update_{0}.log" -f $stamp)
$latestLog = Join-Path $logsDir "update_latest.log"
$timestampSummary = Join-Path $logsDir ("update_{0}_summary.json" -f $stamp)
$latestSummary = Join-Path $logsDir "update_latest_summary.json"
Start-Transcript -Path $timestampLog -Force | Out-Null

$summary = [ordered]@{
    generated_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
    final_status = "更新失败"; code_pull = "未执行"; config_check = "未执行"; unit_tests = "未执行"
    python_compile = "未执行"; safety_scan = "未执行"; etf_backtest = "未执行"; etf_dry_run = "未执行"; daily_dry_run = "未执行"
    backup_dir = $null; failure_reason = $null; suggestion = $null; local_head = $null; remote_head = $null; branch = $null
}
$displayNames = [ordered]@{ code_pull="代码拉取"; config_check="配置检查"; unit_tests="单元测试"; python_compile="Python编译检查"; safety_scan="安全扫描"; etf_backtest="ETF回测"; etf_dry_run="ETF dry-run"; daily_dry_run="Daily dry-run"; backup_dir="备份目录" }
$codeUpdated = $false
$failureReason = $null
$suggestion = $null

function Write-Section($title) { Write-Host "`n========== $title ==========" }
function Write-Ok($message) { Write-Host "[OK] $message" -ForegroundColor Green }
function Write-Warn($message) { Write-Host "[WARN] $message" -ForegroundColor Yellow }
function Add-LocalExcludes {
    $excludeFile = Join-Path $root ".git/info/exclude"
    $patterns = @(
        "qmt_ai_research_pipeline.py", "update_qmt_project_old_broken.ps1", "patch_*.py", "fix_*.py", "test_ai_api.py", "*_local.py", "*.local.json",
        "config.json.bak_*", "config.json.bak_before_autopatch_*", "config.json.bak_allowed_stocks_*",
        "config.json.bak_risk_limit_*", "logs/", "signals/", "runs/", "shadow/", "reports/", "backtest_results/"
    )
    $existing = @()
    if (Test-Path $excludeFile) { $existing = @(Get-Content $excludeFile) }
    $missing = @($patterns | Where-Object { $existing -notcontains $_ })
    if ($missing.Count -gt 0) {
        Add-Content -Path $excludeFile -Value ($missing -join [Environment]::NewLine) -Encoding UTF8
        Write-Ok "已将 $($missing.Count) 条本地临时文件规则加入 .git/info/exclude"
    } else { Write-Ok "本地临时文件忽略规则已配置" }
}
function Invoke-Checked($description, $command, $arguments) {
    & $command @arguments
    if ($LASTEXITCODE -ne 0) {
        if ($summary.Contains($description)) { $summary[$description] = "失败" }
        throw "$description 失败（退出码 $LASTEXITCODE）"
    }
}
function Get-QmtPython {
    $configPath = Join-Path $root "config.json"
    if (Test-Path $configPath) {
        try {
            $configuredPython = (Get-Content -Raw -Path $configPath | ConvertFrom-Json).qmt_python_exe
            if ($configuredPython -and (Test-Path -LiteralPath $configuredPython -PathType Leaf)) {
                Write-Ok "使用 config.json 中的 QMT Python: $configuredPython"
                return $configuredPython
            }
            Write-Warn "config.json 中未配置可用的 qmt_python_exe，将使用 py"
        } catch {
            Write-Warn "读取 config.json 中的 qmt_python_exe 失败，将使用 py"
        }
    } else {
        Write-Warn "未找到 config.json，将使用 py"
    }
    return "py"
}
function Invoke-SafetyScan {
    $tracked = @(& git ls-files -- "*.py" "*.ps1" "*.json")
    if ($LASTEXITCODE -ne 0) { throw "无法获取安全扫描文件列表" }
    $files = @($tracked | Where-Object {
        $_ -notmatch '^(tests|docs|logs|signals|runs|shadow|reports|backtest_results|\.git|__pycache__)/' -and
        $_ -notmatch '(^|/)__pycache__/' -and
        $_ -notmatch '(^|/)(README\.md|\.env\.example|[^/]*\.example\.json|ai_providers[^/]*\.example\.json)$' -and
        $_ -notmatch '(^|/)(qmt_ai_research_pipeline\.py|update_qmt_project_old_broken\.ps1|patch_[^/]*\.py|fix_[^/]*\.py|test_[^/]*\.py)$' -and
        $_ -ne "update_qmt_project.ps1"
    })
    $violations = @()
    foreach ($file in $files) {
        $lineNumber = 0
        foreach ($line in Get-Content (Join-Path $root $file)) {
            $lineNumber++
            # 配置开关只允许按行首的真实赋值；说明文字和禁止词列表不会命中。
            $liveEnabled = $line -match '^\s*["'']?live_trading_enabled["'']?\s*[:=]\s*[Tt]rue\b'
            $apiKey = $line -match ('sk-' + '[A-Za-z0-9_-]{16,}')
            # 删除注释和引号字符串后再找函数调用，避免禁止词列表/诊断文字误报。
            $codeOnly = $line -replace '#.*$', ''
            $codeOnly = $codeOnly -replace '"(?:\\.|[^"\\])*"', '""'
            $codeOnly = $codeOnly -replace "'(?:\\.|[^'\\])*'", "''"
            $dangerousCall = $codeOnly -match '\b(order_stock|cancel_order_stock)\s*\('
            if ($liveEnabled -or $apiKey -or $dangerousCall) {
                $violations += "$file`:$lineNumber`: $($line.Trim())"
            }
        }
    }
    if ($violations.Count -gt 0) { throw "安全扫描发现真实源码中的危险内容：`n$($violations -join "`n")" }
}

try {
    Write-Section "初始化"
    Write-Ok "项目目录: $root"
    Add-LocalExcludes
    $branch = (& git branch --show-current).Trim(); $summary["branch"] = $branch
    if (-not $branch) { throw "当前处于 detached HEAD，无法安全更新" }
    Write-Ok "当前分支: $branch"
    $trackedChanges = @(& git status --porcelain --untracked-files=no)
    if ($trackedChanges.Count -gt 0) { throw "检测到未提交的已跟踪文件修改，已中止以避免覆盖用户修改" }

    $backupRoot = Join-Path (Split-Path -Parent $root) ("qmt_backup\" + (Get-Date -Format "yyyyMMdd_HHmmss"))
    $localFiles = @(".env", "config.json") | Where-Object { Test-Path (Join-Path $root $_) }
    if ($localFiles.Count -gt 0) {
        New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
        foreach ($file in $localFiles) { Copy-Item (Join-Path $root $file) (Join-Path $backupRoot $file) -Force }
        $summary["backup_dir"] = $backupRoot; Write-Ok "本地配置已备份: $backupRoot"
    }

    Write-Section "拉取远程代码"
    $localVersion = (& git rev-parse HEAD).Trim(); $summary["local_head"] = $localVersion; Write-Ok "本地版本: $localVersion"
    $summary["code_pull"] = "失败"
    Invoke-Checked "获取远程代码" "git" @("fetch", "origin", $branch)
    $remoteVersion = (& git rev-parse "origin/$branch").Trim(); $summary["remote_head"] = $remoteVersion; Write-Ok "远程版本: $remoteVersion"
    Invoke-Checked "拉取远程代码" "git" @("pull", "--ff-only", "origin", $branch)
    $codeUpdated = $localVersion -ne $remoteVersion
    $summary["local_head"] = (& git rev-parse HEAD).Trim()
    $summary["code_pull"] = if ($codeUpdated) { "成功" } else { "无需更新" }
    Write-Ok "代码已成功更新到最新 $branch"

    Write-Section "后置检查"
    $QmtPython = Get-QmtPython
    Invoke-Checked "config_check" $QmtPython @("qmt_check_config.py")
    $summary["config_check"] = "通过"; Write-Ok "配置检查通过"
    Invoke-Checked "unit_tests" $QmtPython @("-m", "unittest", "discover", "-s", "tests", "-v")
    $summary["unit_tests"] = "通过"; Write-Ok "单元测试通过"
    Invoke-Checked "python_compile" $QmtPython @("-m", "compileall", "-q", "ai_tools", "data_tools", "tests")
    $summary["python_compile"] = "通过"; Write-Ok "Python编译检查通过"
    Invoke-SafetyScan
    $summary["safety_scan"] = "通过"; Write-Ok "安全扫描通过"
} catch {
    $failureReason = $_.Exception.Message
    $suggestion = if ($codeUpdated) { "请根据上面的错误修复后重新运行更新脚本" } else { "请先处理本地修改、分支或网络问题后重试" }
    if ($codeUpdated) {
        Write-Warn "代码已经成功更新，但后置检查失败"
        Write-Warn "请根据下面的错误修复"
    } else { Write-Warn "代码未更新，更新流程失败" }
    Write-Warn $failureReason
} finally {
    $summary["failure_reason"] = $failureReason
    $summary["suggestion"] = $suggestion
    $summary["final_status"] = if ($failureReason) { if ($codeUpdated) { "代码已更新但后置检查失败" } else { "更新失败" } } else { "更新成功" }
    Write-Section "本次更新总结"
    foreach ($key in $displayNames.Keys) { Write-Host "$($displayNames[$key]): $($summary[$key])" }
    Write-Host "最终状态: $($summary.final_status)" -ForegroundColor $(if ($failureReason) { "Red" } else { "Green" })
    if ($failureReason) { Write-Host "失败原因: $failureReason"; Write-Host "建议处理: $suggestion" } else { Write-Ok "本次更新完成" }
    $json = $summary | ConvertTo-Json -Depth 4
    [System.IO.File]::WriteAllText($timestampSummary, $json, (New-Object System.Text.UTF8Encoding($false)))
    [System.IO.File]::WriteAllText($latestSummary, $json, (New-Object System.Text.UTF8Encoding($false)))
    Stop-Transcript | Out-Null
    Copy-Item -LiteralPath $timestampLog -Destination $latestLog -Force
}
if ($failureReason) { exit 1 }
