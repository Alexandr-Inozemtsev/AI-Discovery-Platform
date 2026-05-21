$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..\..\..")
$sourceFolder = Join-Path $repoRoot "docs\ai-delivery-agents\codex-local-install\agents-toml"
$targetFolder = Join-Path $env:USERPROFILE ".codex\agents"

if (-not (Test-Path -LiteralPath $sourceFolder)) {
    Write-Error "Source folder not found: $sourceFolder"
    exit 1
}

New-Item -ItemType Directory -Force -Path $targetFolder | Out-Null

$sourceFiles = Get-ChildItem -LiteralPath $sourceFolder -Filter "*.toml" -File
$copied = 0
$backups = @()

foreach ($file in $sourceFiles) {
    $targetPath = Join-Path $targetFolder $file.Name

    if (Test-Path -LiteralPath $targetPath) {
        $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $backupPath = "$targetPath.bak-$timestamp"
        Copy-Item -LiteralPath $targetPath -Destination $backupPath -Force
        $backups += $backupPath
    }

    Copy-Item -LiteralPath $file.FullName -Destination $targetPath -Force
    $copied++
}

Write-Host "Codex delivery agents install package"
Write-Host "Repo root: $repoRoot"
Write-Host "Source path: $sourceFolder"
Write-Host "Target path: $targetFolder"
Write-Host "Files found: $($sourceFiles.Count)"
Write-Host "Files copied: $copied"

if ($backups.Count -gt 0) {
    Write-Host "Backups created:"
    foreach ($backup in $backups) {
        Write-Host "  $backup"
    }
}
else {
    Write-Host "Backups created: 0"
}

Write-Host "Done. Restart Codex or terminal if the agents are not visible immediately."

