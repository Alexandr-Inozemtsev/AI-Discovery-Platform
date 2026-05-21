# Prompt pack: release

## Назначение
Release readiness, changelog, deployment notes, rollback, go/no-go.

## Каких агентов подключать
`ai-release-manager`, `ai-qa-engineer`, `ai-devops-engineer`, `ai-technical-writer`, `ai-code-reviewer`.

## Последовательность работы
Review status -> QA report -> deployment notes -> release notes -> rollback -> go/no-go.

## Шаблон Codex-запроса
```text
Ты ai-release-manager. Подготовь release readiness report, release notes, rollback plan и go/no-go recommendation на русском языке.
```

## Expected output
Release notes, checklist, blockers, rollback, residual risks.

## Quality gate
Release gate, QA gate, Documentation gate, DevOps/Security gates при необходимости.

