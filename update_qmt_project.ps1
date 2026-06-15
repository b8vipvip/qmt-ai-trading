# Safety-check the runnable project sources without treating intentional examples
# in tests, documentation, or sample files as production violations.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

$excludedDirectories = @("tests", "docs", "doc", "examples", "example")
$sourceFiles = Get-ChildItem -Path $root -Recurse -File | Where-Object {
    $relative = $_.FullName.Substring($root.Length).TrimStart("\", "/")
    $parts = $relative -split "[\\/]"
    $isExcludedDirectory = @($parts | Where-Object { $excludedDirectories -contains $_ }).Count -gt 0
    $isExcludedFile = $_.Name -eq "README.md" -or $_.Name -like "*.example.*" -or $_.Name -eq "update_qmt_project.ps1"
    -not $isExcludedDirectory -and -not $isExcludedFile -and $_.Extension -in @(".py", ".ps1", ".json")
}

$forbiddenPatterns = @(
    ("order_" + "stock\s*\("),
    ("cancel_order_" + "stock\s*\("),
    ("live_trading_enabled\s*['""]?\s*[:=]\s*[Tt]rue"),
    ("sk-" + "[A-Za-z0-9_-]{16,}")
)

$violations = @()
foreach ($file in $sourceFiles) {
    foreach ($pattern in $forbiddenPatterns) {
        $matches = Select-String -Path $file.FullName -Pattern $pattern
        foreach ($match in $matches) {
            $violations += "{0}:{1}: {2}" -f $file.FullName, $match.LineNumber, $match.Line.Trim()
        }
    }
}

if ($violations.Count -gt 0) {
    Write-Error ("Safety scan failed:`n" + ($violations -join "`n"))
}

Write-Host "[OK] Safety scan passed"
