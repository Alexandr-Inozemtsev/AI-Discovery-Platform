$expectedAgents = @(
    "ai-orchestrator.toml",
    "ai-product-orchestrator.toml",
    "ai-business-analyst.toml",
    "ai-system-analyst.toml",
    "ai-solution-architect.toml",
    "ai-backend-developer.toml",
    "ai-frontend-developer.toml",
    "ai-database-engineer.toml",
    "ai-llm-rag-engineer.toml",
    "ai-security-reviewer.toml",
    "ai-qa-engineer.toml",
    "ai-test-automation-engineer.toml",
    "ai-devops-engineer.toml",
    "ai-ui-ux-designer.toml",
    "ai-code-reviewer.toml",
    "ai-release-manager.toml",
    "ai-delivery-project-manager.toml",
    "ai-trello-analyst.toml",
    "ai-technical-writer.toml",
    "ai-performance-engineer.toml"
)

$targetFolder = Join-Path $env:USERPROFILE ".codex\agents"
$missing = @()

Write-Host "Checking Codex agents folder: $targetFolder"

if (-not (Test-Path -LiteralPath $targetFolder)) {
    Write-Host "MISSING folder: $targetFolder"
    exit 1
}

foreach ($agentFile in $expectedAgents) {
    $path = Join-Path $targetFolder $agentFile
    if (Test-Path -LiteralPath $path) {
        Write-Host "OK      $agentFile"
    }
    else {
        Write-Host "MISSING $agentFile"
        $missing += $agentFile
    }
}

if ($missing.Count -gt 0) {
    Write-Host "Missing files: $($missing.Count)"
    exit 1
}

Write-Host "All expected Codex delivery agent TOML files are present: $($expectedAgents.Count)"
exit 0

