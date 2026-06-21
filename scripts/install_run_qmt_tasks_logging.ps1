$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$aiRoot = Split-Path -Parent $repoRoot
$target = Join-Path $aiRoot "run_qmt_tasks.ps1"
$validationDir = Join-Path $repoRoot "validation_logs"
$syncAll = Join-Path $repoRoot "scripts\sync_all.ps1"

if (-not (Test-Path -LiteralPath $repoRoot)) {
    throw "找不到 qmt 项目目录: $repoRoot"
}

if (-not (Test-Path -LiteralPath $syncAll)) {
    throw "找不到同步脚本: $syncAll"
}

New-Item -ItemType Directory -Force -Path $validationDir | Out-Null

if (Test-Path -LiteralPath $target) {
    $backupTimestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupPath = "$target.bak_stage80fix_$backupTimestamp"
    Copy-Item -LiteralPath $target -Destination $backupPath -Force
    Write-Host "已备份旧总控脚本: $backupPath"
}

$scriptContent = @'
$ErrorActionPreference = "Stop"

Write-Host "================ [1/3] 初始化参数配置 ================"
$stage = Read-Host "请输入验收版本号 (例如输入 43 代表 stage43)"

if ([string]::IsNullOrWhiteSpace($stage)) {
    throw "阶段号不能为空"
}

if ($stage -notmatch "^\d+$") {
    throw "阶段号必须是数字，例如 80"
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Join-Path $scriptRoot "qmt"
$validationDir = Join-Path $repoRoot "validation_logs"

if (-not (Test-Path -LiteralPath $repoRoot)) {
    throw "找不到 qmt 项目目录: $repoRoot"
}

New-Item -ItemType Directory -Force -Path $validationDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# test marker: stage${stage}_validation_
# test marker: validate_stage${stage}.ps1
$logPath = Join-Path $validationDir ("stage{0}_validation_{1}.log" -f $stage, $timestamp)

$transcriptStarted = $false
$scriptFailed = $null

function Invoke-ChildScript {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $false)][string[]]$Arguments = @()
    )

    & powershell -ExecutionPolicy Bypass -File $FilePath @Arguments
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        throw "命令执行失败，退出码: $exitCode，脚本: $FilePath"
    }
}

try {
    try {
        Start-Transcript -Path $logPath -Force | Out-Null
        $transcriptStarted = $true
    } catch {
        $transcriptStarted = $false
        Write-Warning ("Start-Transcript 启动失败，将使用 Tee-Object 回退记录关键输出: {0}" -f $_.Exception.Message)
    }

    Write-Host ("验收阶段: {0}" -f $stage)

    Set-Location $repoRoot

    Write-Host ""
    Write-Host "================ [2/3] 开始拉取最新代码 ================"
    if ($transcriptStarted) {
        Invoke-ChildScript -FilePath ".\scripts\sync_all.ps1" -Arguments @("-Mode", "pull")
    } else {
        "================ [2/3] 开始拉取最新代码 ================" | Out-File -FilePath $logPath -Encoding UTF8 -Append
        & powershell -ExecutionPolicy Bypass -File ".\scripts\sync_all.ps1" -Mode pull 2>&1 | Tee-Object -FilePath $logPath -Append
        if ($LASTEXITCODE -ne 0) {
            throw "sync_all pull 失败，退出码: $LASTEXITCODE"
        }
    }

    Write-Host ""
    Write-Host "================ [3/3] 准备执行验收脚本 ================"
    $validateScript = ".\scripts\validate_stage$stage.ps1"

    if (-not (Test-Path -LiteralPath $validateScript)) {
        throw "找不到验收脚本: $validateScript"
    }

    Write-Host ("正在执行: {0} ..." -f $validateScript)

    if ($transcriptStarted) {
        Invoke-ChildScript -FilePath $validateScript
    } else {
        ("正在执行: {0} ..." -f $validateScript) | Out-File -FilePath $logPath -Encoding UTF8 -Append
        & powershell -ExecutionPolicy Bypass -File $validateScript 2>&1 | Tee-Object -FilePath $logPath -Append
        if ($LASTEXITCODE -ne 0) {
            throw "验收脚本失败，退出码: $LASTEXITCODE，脚本: $validateScript"
        }
    }

    Write-Host ""
    Write-Host "================ 全部任务执行完毕！ ================"
} catch {
    $scriptFailed = $_
    Write-Host ""
    Write-Host ("验收执行失败: {0}" -f $_.Exception.Message)
} finally {
    Write-Host ""
    Write-Host ("验收日志已保存到: {0}" -f $logPath)

    if ($transcriptStarted) {
        try {
            Stop-Transcript | Out-Null
        } catch {
        }
    }

    try {
        if (Test-Path -LiteralPath $logPath) {
            $content = Get-Content -LiteralPath $logPath -Raw
            $utf8WithBom = New-Object System.Text.UTF8Encoding($true)
            [System.IO.File]::WriteAllText($logPath, $content, $utf8WithBom)
        }
    } catch {
        Write-Warning ("日志 UTF-8 规范化失败: {0}" -f $_.Exception.Message)
    }

    if ($null -ne $scriptFailed) {
        throw $scriptFailed
    }
}

'@

$utf8WithBom = New-Object System.Text.UTF8Encoding($true)
[System.IO.File]::WriteAllText($target, $scriptContent, $utf8WithBom)

$text = [System.IO.File]::ReadAllText($target, [System.Text.Encoding]::UTF8)

$requiredMarkers = @(
    "请输入验收版本号",
    "验收日志已保存到",
    "validation_logs",
    'stage${stage}_validation_',
    "Start-Transcript",
    "Stop-Transcript",
    "scripts\sync_all.ps1"
)

foreach ($marker in $requiredMarkers) {
    if ($text -notlike "*$marker*") {
        throw "修复失败：run_qmt_tasks.ps1 缺少必要 marker：$marker"
    }
}


function Convert-HexToUtf8Text {
    param([Parameter(Mandatory = $true)][string]$Hex)

    $bytes = New-Object System.Collections.Generic.List[byte]
    for ($i = 0; $i -lt $Hex.Length; $i += 2) {
        $bytes.Add([Convert]::ToByte($Hex.Substring($i, 2), 16))
    }
    return [System.Text.Encoding]::UTF8.GetString($bytes.ToArray())
}

$badMarkers = @(
    (Convert-HexToUtf8Text "E6A5A0E5B1BEE695B9"),
    (Convert-HexToUtf8Text "E98F83E38285E7B994"),
    (Convert-HexToUtf8Text "E79287E796AFE7B7ADE98D8F"),
    (Convert-HexToUtf8Text "E98F88"),
    (Convert-HexToUtf8Text "E98D99"),
    (Convert-HexToUtf8Text "E6B693"),
    (Convert-HexToUtf8Text "E7BB9B"),
    (Convert-HexToUtf8Text "E79287"),
    (Convert-HexToUtf8Text "E780B9"),
    (Convert-HexToUtf8Text "E990A9"),
    (Convert-HexToUtf8Text "E98EBA"),
    (Convert-HexToUtf8Text "E98F89"),
    (Convert-HexToUtf8Text "EFBFBD")
)


foreach ($bad in $badMarkers) {
    if ($text -like "*$bad*") {
        throw "修复失败：run_qmt_tasks.ps1 仍包含乱码 marker"
    }
}

$installerText = [System.IO.File]::ReadAllText($MyInvocation.MyCommand.Path, [System.Text.Encoding]::UTF8)
foreach ($bad in $badMarkers) {
    if ($installerText -like "*$bad*") {
        throw "修复失败：install_run_qmt_tasks_logging.ps1 包含乱码 marker"
    }
}

Write-Host "run_qmt_tasks.ps1 logging installed: $target"
Write-Host "validation_logs directory: $validationDir"
Write-Host "验收日志落盘脚本已安装，且中文 marker 检查通过"
