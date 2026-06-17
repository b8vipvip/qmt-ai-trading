param(
    [ValidateSet("sync", "push", "pull", "scan", "status")]
    [string]$Mode = "sync",

    [string]$Message = "chore: sync qmt-ai-trading updates",

    [string]$Branch = "main",

    [string]$Remote = "origin",

    [string]$RemoteUrl = "git@github.com:b8vipvip/qmt-ai-trading.git"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Log-Info {
    param([string]$Msg, [string]$CnMsg = "")
    $line = "[INFO] " + $Msg
    if (-not [string]::IsNullOrWhiteSpace($CnMsg)) {
        $line = $line + " / [信息] " + $CnMsg
    }
    Write-Host $line -ForegroundColor Cyan
}

function Log-Ok {
    param([string]$Msg, [string]$CnMsg = "")
    $line = "[OK] " + $Msg
    if (-not [string]::IsNullOrWhiteSpace($CnMsg)) {
        $line = $line + " / [成功] " + $CnMsg
    }
    Write-Host $line -ForegroundColor Green
}

function Log-Warn {
    param([string]$Msg, [string]$CnMsg = "")
    $line = "[WARN] " + $Msg
    if (-not [string]::IsNullOrWhiteSpace($CnMsg)) {
        $line = $line + " / [警告] " + $CnMsg
    }
    Write-Host $line -ForegroundColor Yellow
}

function Log-Bad {
    param([string]$Msg, [string]$CnMsg = "")
    $line = "[ERROR] " + $Msg
    if (-not [string]::IsNullOrWhiteSpace($CnMsg)) {
        $line = $line + " / [错误] " + $CnMsg
    }
    Write-Host $line -ForegroundColor Red
}

function Run-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$GitArgs,

        [switch]$AllowFail
    )

    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    try {
        $raw = & git @GitArgs 2>&1
        $code = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $oldPreference
    }

    $lines = @()
    foreach ($item in @($raw)) {
        if ($null -ne $item) {
            $lines += $item.ToString()
        }
    }

    $text = $lines -join "`n"

    if ($code -ne 0 -and -not $AllowFail) {
        Log-Bad ("git " + ($GitArgs -join " ") + " failed")
        foreach ($line in $lines) {
            Write-Host $line
        }
        throw "Git command failed"
    }

    return [pscustomobject]@{
        Code  = $code
        Lines = $lines
        Text  = $text
    }
}

function Ensure-GitRepo {
    $r = Run-Git -GitArgs @("rev-parse", "--is-inside-work-tree")
    if ($r.Text.Trim() -ne "true") {
        throw "Current directory is not a Git repository"
    }

    $root = (Run-Git -GitArgs @("rev-parse", "--show-toplevel")).Text.Trim()
    Set-Location $root
    Log-Info "Repository root: $root"
}

function Ensure-Remote {
    Log-Info "Checking remote URL..." "检查远程仓库地址..."

    $remoteCheck = Run-Git -GitArgs @("remote", "get-url", $Remote) -AllowFail

    if ($remoteCheck.Code -ne 0 -or [string]::IsNullOrWhiteSpace($remoteCheck.Text)) {
        Run-Git -GitArgs @("remote", "add", $Remote, $RemoteUrl) | Out-Null
        Log-Ok "Added remote: $RemoteUrl"
    }
    else {
        $url = $remoteCheck.Text.Trim()

        if ($url -ne $RemoteUrl) {
            Log-Warn "Remote URL is not expected. Updating remote URL."
            Log-Warn "Old: $url"
            Log-Warn "New: $RemoteUrl"
            Run-Git -GitArgs @("remote", "set-url", $Remote, $RemoteUrl) | Out-Null
        }
    }

    $finalUrl = (Run-Git -GitArgs @("remote", "get-url", $Remote)).Text.Trim()

    if ($finalUrl -notlike "git@github.com:*/*.git") {
        Log-Bad "Remote must use GitHub SSH URL. Current: $finalUrl"
        throw "SSH remote required"
    }

    Log-Ok "Remote uses SSH: $finalUrl"
}

function Ensure-Branch {
    $current = (Run-Git -GitArgs @("branch", "--show-current") -AllowFail).Text.Trim()

    if ([string]::IsNullOrWhiteSpace($current)) {
        Log-Warn "No branch detected. Creating branch: $Branch"
        Run-Git -GitArgs @("checkout", "-B", $Branch) | Out-Null
    }
    elseif ($current -ne $Branch) {
        Log-Warn "Current branch is [$current]. Renaming to [$Branch]."
        Run-Git -GitArgs @("branch", "-M", $Branch) | Out-Null
    }

    Log-Ok "Current branch: $Branch"
}

function Ensure-GitIgnoreRules {
    Log-Info "Checking .gitignore..." "检查 .gitignore 规则..."

    $ignoreFile = ".gitignore"
    if (-not (Test-Path $ignoreFile)) {
        New-Item -ItemType File -Path $ignoreFile | Out-Null
    }

    $rules = @(
        "",
        "# qmt-ai-trading sensitive files",
        ".env",
        ".env.*",
        "!.env.example",
        "*.key",
        "*.pem",
        "*.p12",
        "*.pfx",
        "*.crt",
        "*.sqlite",
        "*.sqlite3",
        "*.db",
        "*.mdb",
        "*.kdbx",
        "id_rsa",
        "id_dsa",
        "id_ecdsa",
        "id_ed25519",
        "*password*",
        "*passwd*",
        "*secret*",
        "*token*",
        "*credential*",
        "data/*.db",
        "data/**/*.db",
        "data/*.sqlite",
        "data/**/*.sqlite",
        "instance/*.db",
        "instance/*.sqlite",
        "__pycache__/",
        "*.pyc",
        ".pytest_cache/",
        ".mypy_cache/"
    )

    $current = ""
    if (Test-Path $ignoreFile) {
        $current = Get-Content $ignoreFile -Raw -ErrorAction SilentlyContinue
    }

    $changed = $false

    foreach ($rule in $rules) {
        if ([string]::IsNullOrWhiteSpace($rule)) {
            continue
        }

        if ($current -notmatch [regex]::Escape($rule)) {
            Add-Content -Path $ignoreFile -Value $rule
            $changed = $true
        }
    }

    if ($changed) {
        Log-Ok ".gitignore updated" ".gitignore 已更新"
    }
    else {
        Log-Ok ".gitignore already contains sensitive rules" ".gitignore 已包含敏感文件规则"
    }
}

function Get-RepoStatus {
    $r = Run-Git -GitArgs @("status", "--porcelain") -AllowFail
    return @($r.Lines)
}

function Has-WorkingChanges {
    $status = Get-RepoStatus
    return ($status.Count -gt 0)
}

function Get-ChangedFiles {
    $set = New-Object "System.Collections.Generic.HashSet[string]"

    $a = Run-Git -GitArgs @("diff", "--name-only") -AllowFail
    $b = Run-Git -GitArgs @("diff", "--cached", "--name-only") -AllowFail
    $c = Run-Git -GitArgs @("ls-files", "--others", "--exclude-standard") -AllowFail

    foreach ($file in @($a.Lines + $b.Lines + $c.Lines)) {
        if (-not [string]::IsNullOrWhiteSpace($file)) {
            [void]$set.Add($file.Trim())
        }
    }

    return @($set)
}

function Test-PathIsSensitive {
    param([string]$File)

    $normalized = $File -replace "\\", "/"

    if ($normalized -match '^\.env\.example$') {
        return $false
    }

    $blockedPatterns = @(
        '(^|/)\.env($|[./])',
        '\.(pem|key|p12|pfx|sqlite|sqlite3|db|mdb|kdbx)$',
        '(^|/)(id_rsa|id_dsa|id_ecdsa|id_ed25519)$',
        '(?i)(password|passwd|secret|token|credential|private[_-]?key|api[_-]?key)'
    )

    foreach ($p in $blockedPatterns) {
        if ($normalized -match $p) {
            return $true
        }
    }

    return $false
}

function Scan-Privacy {
    Log-Info "Running privacy scan..." "正在执行隐私扫描..."

    $files = Get-ChangedFiles

    if ($files.Count -eq 0) {
        Log-Ok "No changed files to scan" "没有需要扫描的变更文件"
        return
    }

    $contentPatterns = @(
        'sk-[A-Za-z0-9_-]{20,}',
        'github_pat_[A-Za-z0-9_]{20,}',
        'ghp_[A-Za-z0-9]{20,}',
        'AKIA[0-9A-Z]{16}',
        '-----BEGIN [A-Z ]*PRIVATE KEY-----',
        '(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|refresh[_-]?token|authorization|bearer|password|passwd|db[_-]?pass|database[_-]?url)\s*[:=]\s*[''"]?[^''"\r\n ]{8,}',
        '(?i)(postgres|mysql|redis|mongodb)://[^ \r\n]+:[^ \r\n]+@'
    )

    $textExts = @(
        ".py", ".ps1", ".js", ".ts", ".json", ".yaml", ".yml",
        ".toml", ".ini", ".cfg", ".md", ".txt", ".html", ".css",
        ".vue", ".sh", ".bat", ".cmd", ".sql", ".example", ".gitignore"
    )

    $blockedItems = New-Object "System.Collections.Generic.List[string]"

    foreach ($file in $files) {
        if (Test-PathIsSensitive -File $file) {
            $blockedItems.Add("Sensitive file path: $file")
            continue
        }

        if (-not (Test-Path $file)) {
            continue
        }

        $item = Get-Item $file -ErrorAction SilentlyContinue

        if ($null -eq $item) {
            continue
        }

        if ($item.PSIsContainer) {
            continue
        }

        if ($item.Length -gt 2097152) {
            Log-Warn "Skip large file content scan: $file"
            continue
        }

        $ext = [System.IO.Path]::GetExtension($file).ToLowerInvariant()
        $base = [System.IO.Path]::GetFileName($file).ToLowerInvariant()

        if (($textExts -notcontains $ext) -and ($base -ne ".gitignore")) {
            continue
        }

        try {
            $content = Get-Content -Path $file -Raw -ErrorAction Stop
        }
        catch {
            Log-Warn "Cannot read file. Skip content scan: $file"
            continue
        }

        foreach ($p in $contentPatterns) {
            if ($content -match $p) {
                $blockedItems.Add("Possible secret in file: $file")
                break
            }
        }
    }

    if ($blockedItems.Count -gt 0) {
        Log-Bad "Privacy scan failed. Commit blocked." "隐私扫描失败，已阻止提交"
        Write-Host ""

        foreach ($item in $blockedItems) {
            Write-Host " - $item" -ForegroundColor Red
        }

        Write-Host ""
        Log-Warn "Move real keys, tokens, passwords, database files, and account files to local ignored files."
        throw "Privacy scan failed"
    }

    Log-Ok "Privacy scan passed" "隐私扫描通过"
}

function RemoteBranchExists {
    $r = Run-Git -GitArgs @("ls-remote", "--heads", $Remote, $Branch) -AllowFail
    return ($r.Code -eq 0 -and -not [string]::IsNullOrWhiteSpace($r.Text))
}

function Fetch-Remote {
    if (-not (RemoteBranchExists)) {
        Log-Warn "Remote branch does not exist yet. This may be the first push."
        return $false
    }

    Log-Info "Fetching remote branch..."
    Run-Git -GitArgs @("fetch", "--prune", $Remote, $Branch) | Out-Null
    Log-Ok "Fetch done"
    return $true
}

function Get-AheadBehind {
    if (-not (RemoteBranchExists)) {
        return [pscustomobject]@{
            Ahead = 1
            Behind = 0
            HasRemote = $false
        }
    }

    $remoteRef = "$Remote/$Branch"
    $result = Run-Git -GitArgs @("rev-list", "--left-right", "--count", "HEAD...$remoteRef") -AllowFail

    if ($result.Code -ne 0) {
        Log-Bad "Cannot compare local branch with remote branch."
        foreach ($line in $result.Lines) {
            Write-Host $line
        }
        throw "Compare failed"
    }

    $parts = $result.Text.Trim() -split "\s+"

    return [pscustomobject]@{
        Ahead = [int]$parts[0]
        Behind = [int]$parts[1]
        HasRemote = $true
    }
}

function Safe-Pull {
    $hasRemote = Fetch-Remote

    if (-not $hasRemote) {
        Log-Ok "Skip pull because remote branch does not exist"
        return
    }

    $ab = Get-AheadBehind

    if ($ab.Ahead -gt 0 -and $ab.Behind -gt 0) {
        Log-Bad "Local and remote branches have diverged."
        Write-Host "Ahead:  $($ab.Ahead)"
        Write-Host "Behind: $($ab.Behind)"
        Write-Host ""
        Write-Host "Manual fix recommended:"
        Write-Host "  git status"
        Write-Host "  git log --oneline --graph --decorate --all -20"
        Write-Host "  git pull --rebase origin main"
        throw "Branch diverged"
    }

    if ($ab.Behind -eq 0) {
        Log-Ok "No remote updates"
        return
    }

    Log-Warn "Remote has $($ab.Behind) new commit(s). Pulling safely..."

    $hadChanges = Has-WorkingChanges

    if ($hadChanges) {
        Log-Warn "Local changes detected. Scanning and stashing before pull..."
        Scan-Privacy
        Run-Git -GitArgs @("stash", "push", "-u", "-m", "qmt-ai-trading-auto-stash-before-pull") | Out-Null
    }

    try {
        Run-Git -GitArgs @("pull", "--ff-only", $Remote, $Branch) | Out-Null
        Log-Ok "Pull done"
    }
    finally {
        if ($hadChanges) {
            Log-Warn "Restoring local changes from stash..."
            $pop = Run-Git -GitArgs @("stash", "pop") -AllowFail

            if ($pop.Code -ne 0) {
                Log-Bad "stash pop failed. Please run git status and resolve conflicts."
                foreach ($line in $pop.Lines) {
                    Write-Host $line
                }
                throw "Stash pop failed"
            }

            Log-Ok "Local changes restored"
        }
    }
}

function Commit-LocalChanges {
    if (-not (Has-WorkingChanges)) {
        Log-Ok "No local changes to commit"
        return
    }

    Log-Info "Local changes detected. Running privacy scan before commit..."
    Scan-Privacy

    Log-Info "Running git add -A..."
    Run-Git -GitArgs @("add", "-A") | Out-Null

    Log-Info "Running privacy scan again after staging..."
    Scan-Privacy

    $staged = Run-Git -GitArgs @("diff", "--cached", "--name-only") -AllowFail

    if (@($staged.Lines).Count -eq 0) {
        Log-Ok "No staged changes to commit"
        return
    }

    Log-Info "Committing changes..."
    Run-Git -GitArgs @("commit", "-m", $Message) | Out-Null
    Log-Ok "Commit done"
}

function Push-Remote {
    Fetch-Remote | Out-Null

    $ab = Get-AheadBehind

    if ($ab.HasRemote -and $ab.Ahead -gt 0 -and $ab.Behind -gt 0) {
        Log-Bad "Local and remote branches diverged before push."
        Write-Host "Manual fix recommended:"
        Write-Host "  git pull --rebase origin main"
        throw "Branch diverged before push"
    }

    if ($ab.HasRemote -and $ab.Behind -gt 0) {
        Log-Warn "Remote has updates before push. Pulling first..."
        Safe-Pull
        Fetch-Remote | Out-Null
    }

    Log-Info "Pushing to GitHub..."
    Run-Git -GitArgs @("push", "-u", $Remote, $Branch) | Out-Null
    Log-Ok "Push done"
}

function Show-Status {
    Fetch-Remote | Out-Null

    $url = (Run-Git -GitArgs @("remote", "get-url", $Remote)).Text.Trim()
    $ab = Get-AheadBehind
    $dirty = Has-WorkingChanges

    Write-Host ""
    Write-Host "========== qmt-ai-trading git status ==========" -ForegroundColor Cyan
    Write-Host "Remote:    $Remote"
    Write-Host "URL:       $url"
    Write-Host "Branch:    $Branch"
    Write-Host "HasRemote: $($ab.HasRemote)"
    Write-Host "Ahead:     $($ab.Ahead)"
    Write-Host "Behind:    $($ab.Behind)"
    Write-Host "Dirty:     $dirty"
    Write-Host ""

    git status --short
}

function Main {
    Write-Host ""
    Write-Host "========== qmt-ai-trading GitHub sync ==========" -ForegroundColor Cyan
    Write-Host "Mode:   $Mode"
    Write-Host "Branch: $Branch"
    Write-Host ""

    Ensure-GitRepo
    Ensure-Remote
    Ensure-Branch
    Ensure-GitIgnoreRules

    switch ($Mode) {
        "status" {
            Show-Status
        }

        "scan" {
            Scan-Privacy
            Log-Ok "Scan mode done" "扫描模式完成"
        }

        "pull" {
            Safe-Pull
            Log-Ok "Pull mode done"
        }

        "push" {
            Commit-LocalChanges
            Push-Remote
            Log-Ok "Push mode done"
        }

        "sync" {
            Safe-Pull
            Commit-LocalChanges
            Push-Remote
            Log-Ok "Sync mode done"
        }
    }

    Write-Host ""
    Log-Ok "All done" "全部完成"
}

try {
    Main
}
catch {
    Write-Host ""
    Log-Bad $_.Exception.Message
    Write-Host ""
    Log-Warn "Stopped. No unsafe operation continued." "已中止，没有继续执行危险操作"
    exit 1
}
