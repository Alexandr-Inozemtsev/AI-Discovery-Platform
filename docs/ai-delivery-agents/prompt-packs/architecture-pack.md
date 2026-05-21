# Prompt pack: architecture

## Назначение
Архитектурные решения, ADR, runtime boundaries, API/data contracts.

## Каких агентов подключать
`ai-system-analyst`, `ai-solution-architect`, профильные implementation agents, `ai-security-reviewer` при risk/security impact.

## Последовательность работы
System requirements -> architecture decision -> contracts -> implementation handoff -> review.

## Шаблон Codex-запроса
```text
Ты ai-solution-architect. Опиши architecture decision, API/data/runtime boundaries, risks, rollout/rollback и handoff для профильных агентов.
```

## Expected output
ADR/architecture brief, contracts, dependencies, risks.

## Quality gate
Architecture gate, Security gate при необходимости.

