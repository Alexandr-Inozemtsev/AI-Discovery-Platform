# Gantt delivery plan

Статус: draft. План ориентировочный на 6-8 недель, начиная с 2026-05-21. Mermaid Gantt ниже не означает подключение к внешнему инструменту.

```mermaid
gantt
    title AI Discovery Platform Delivery Plan
    dateFormat YYYY-MM-DD
    axisFormat %d.%m

    section Delivery Governance
    Стабилизация MVP                         :active, mvp, 2026-05-21, 10d
    Оформление global Codex agents           :agents, 2026-05-21, 7d
    Agent operating model                    :model, after agents, 5d
    Trello operating model                   :trello, 2026-05-25, 5d
    Gantt/reporting                          :gantt, after trello, 5d

    section Product Runtime
    Backend stabilization                    :backend, 2026-05-28, 14d
    Database/audit                           :db, 2026-06-01, 10d
    LLM/RAG settings                         :llm, 2026-06-04, 10d
    Security review                          :security, after llm, 7d

    section Frontend and Quality
    Frontend stabilization                   :frontend, 2026-06-03, 14d
    QA automation                            :qaauto, 2026-06-10, 14d
    DOCX/export                              :docx, 2026-06-12, 8d
    Release readiness                        :release, 2026-06-24, 7d
```

## Правила обновления

- Если меняются сроки, dependencies или release scope, обновляет `ai-delivery-project-manager`.
- Если меняется Trello/backlog scope, `ai-trello-analyst` синхронизирует Markdown package.
- Если план используется только как Mermaid-файл, нельзя утверждать, что он подключен к внешнему Gantt-инструменту.

## Delivery notes

- `BE-01-01` относится к блоку `Backend stabilization`; даты Gantt не изменялись, так как задача фиксирует текущий API contract без изменения сроков.
