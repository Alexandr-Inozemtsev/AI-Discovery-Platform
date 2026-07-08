$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel 2>$null)
if (-not $repoRoot) {
    Write-Error "Не удалось определить корень git repository."
    exit 1
}

Set-Location $repoRoot

$trackedFiles = git ls-files
if ($LASTEXITCODE -ne 0) {
    Write-Error "Не удалось выполнить git ls-files."
    exit 1
}

function Normalize-RepoPath {
    param([string]$Path)
    return ($Path -replace "\\", "/")
}

function Is-AllowedTemplate {
    param([string]$Path)

    $normalized = Normalize-RepoPath $Path
    $fileName = [System.IO.Path]::GetFileName($normalized)

    if ($fileName -eq ".env.example") {
        return $true
    }

    if ($normalized -like "docs/*/mcp.example.json" -or $normalized -like "docs/**/mcp.example.json") {
        return $true
    }

    # UI design tokens are not credentials or auth tokens.
    if ($normalized -in @(
        "discovery-ai-agent/frontend/src/ui/tokens.css",
        "discovery-ai-agent/frontend/src/ui/tokens.ts"
    )) {
        return $true
    }

    return $false
}

function Get-HygieneViolationReason {
    param([string]$Path)

    $normalized = Normalize-RepoPath $Path
    $fileName = [System.IO.Path]::GetFileName($normalized)

    if (Is-AllowedTemplate $normalized) {
        return $null
    }

    if ($normalized -match "(^|/)node_modules(/|$)") {
        return "tracked node_modules"
    }
    if ($normalized -match "(^|/)\.venv(/|$)") {
        return "tracked .venv"
    }
    if ($normalized -match "(^|/)venv(/|$)") {
        return "tracked venv"
    }
    if ($normalized -match "(^|/__pycache__)(/|$)" -or $normalized -match "(^|/)__pycache__(/|$)") {
        return "tracked __pycache__"
    }
    if ($normalized -match "\.pyc$") {
        return "tracked Python bytecode"
    }
    if ($fileName -eq ".env" -or ($fileName -like ".env.*" -and $fileName -ne ".env.example")) {
        return "tracked environment file"
    }
    if ($fileName -like "credentials*") {
        return "tracked credentials file"
    }
    if ($fileName -like "cookies*") {
        return "tracked cookies file"
    }
    if ($fileName -like "token*") {
        return "tracked token file"
    }
    if ($fileName -match "\.(key|pem|p12|pfx)$") {
        return "tracked key/certificate material"
    }

    return $null
}

$violations = @()
foreach ($file in $trackedFiles) {
    $reason = Get-HygieneViolationReason $file
    if ($reason) {
        $violations += [PSCustomObject]@{
            Reason = $reason
            Path = Normalize-RepoPath $file
        }
    }
}

if ($violations.Count -gt 0) {
    Write-Host "Repository hygiene check failed. Найдены tracked local/secrets артефакты:" -ForegroundColor Red
    $violations | Sort-Object Reason, Path | Format-Table -AutoSize
    Write-Host ""
    Write-Host "Исправление: удалите файлы из git index через git rm --cached, не удаляя локальные файлы с диска." -ForegroundColor Yellow
    exit 1
}

Write-Host "Repository hygiene check passed. Tracked local/secrets артефакты не найдены." -ForegroundColor Green
exit 0
