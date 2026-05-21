# Prompt pack: Trello/backlog

## Назначение
Подготовка Trello-card descriptions, labels, checklists и manual import package.

## Каких агентов подключать
`ai-delivery-project-manager`, `ai-trello-analyst`, `ai-product-orchestrator`.

## Последовательность работы
Scope -> milestones/dependencies -> card structure -> manual import package -> sync status.

## Шаблон Codex-запроса
```text
Ты ai-trello-analyst. Подготовь Trello карточки на русском. Если Trello API не подключен, не утверждай, что доска создана; сделай manual import package с sync status.
```

## Expected output
Карточки с title, description, responsible agent, priority, labels, checklist, dependencies, acceptance criteria, DoD.

## Quality gate
Trello gate, Product gate.

