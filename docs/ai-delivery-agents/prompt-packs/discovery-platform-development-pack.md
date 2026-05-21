# Prompt pack: разработка AI Discovery Platform

## Назначение
Общий pack для задач разработки платформы, когда затронуты несколько слоев.

## Каких агентов подключать
`ai-orchestrator`, `ai-solution-architect`, профильные implementation agents, `ai-code-reviewer`, `ai-qa-engineer`, при delivery impact - `ai-delivery-project-manager` и `ai-trello-analyst`.

## Последовательность работы
1. Orchestrator классифицирует задачу.
2. Architect фиксирует cross-layer contracts.
3. Профильные агенты выполняют изменения.
4. Code reviewer проверяет diff.
5. QA проверяет acceptance.
6. Delivery PM/Trello analyst обновляют delivery artifacts.

## Шаблон Codex-запроса
```text
Ты ai-orchestrator. Разбери задачу разработки AI Discovery Platform, выбери агентов, не смешивай product AI agents и global Codex delivery agents, составь план, выполни применимые изменения и дай отчет на русском.
```

## Expected output
План, список агентов, измененные файлы, проверки, risks, backlog/Trello/Gantt impact.

## Quality gate
Product, Architecture, профильный implementation gate, Review, QA, Documentation.

