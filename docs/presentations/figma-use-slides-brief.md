# Brief для figma-use-slides

## Назначение

Инструкция для `figma-use-slides`, чтобы сформировать презентацию для руководства по AI Discovery Platform на основе [management-platform-overview.md](management-platform-overview.md), архитектурных схем и delivery artifacts.

## Требования к презентации

- Язык: русский.
- Стиль: enterprise / consulting / product strategy.
- Аудитория: руководитель, C-level, руководитель ИТ.
- Не перегружать текстом.
- Использовать схемы из [docs/architecture/diagrams](../architecture/diagrams/README.md).
- Использовать roadmap/Gantt из [Gantt delivery plan](../ai-delivery-agents/07-gantt-delivery-plan.md).
- Использовать [backlog traceability matrix](../backlog/backlog-traceability-matrix.md).
- Показать value, architecture confidence, security awareness, roadmap.

## Слайды

1. AI Discovery Platform - титульный.
2. Почему это нужно.
3. Что делает платформа.
4. Сквозной процесс Discovery.
5. Архитектура решения.
6. Работа с контекстом и RAG.
7. Обработка ссылок и вложений.
8. Контроль качества и traceability.
9. Дорожная карта.
10. Риски и меры контроля.
11. Что нужно для пилота.
12. Решение, которое требуется от руководства.

## Visual brief по слайдам

| Слайд | Visual brief | Источник |
|---|---|---|
| 1 | Темный титул, короткая лента Context -> Final BT. | Management overview slide 1 |
| 2 | Разрозненные источники, сходящиеся в ручной процесс. | ТЗ |
| 3 | Workspace с этапами Discovery. | Artifact lifecycle |
| 4 | Value/risk control matrix. | Traceability matrix |
| 5 | C4 Container, упрощенный для руководства. | 02-c4-container |
| 6 | Context ingestion flow. | 04-context-ingestion-and-rag |
| 7 | Два сценария A/B: Corporate RAG и Universal Parser. | 06-link-processing |
| 8 | Human-in-the-loop + source_trace + versioning. | 03-agent-runtime-flow |
| 9 | Упрощенный Gantt v2. | 07-gantt-delivery-plan |
| 10 | Таблица risks/controls: LLM, auth, prompt injection, SSRF, audit. | Security requirements |
| 11 | Pilot readiness checklist. | Deployment diagram |
| 12 | Decision board: согласовать / подтвердить / запустить. | Backlog + Gantt |

## Формат результата

- Подготовить структуру слайдов.
- Подготовить текст слайдов.
- Подготовить visual brief по каждому слайду.
- Если `figma-use-slides` доступен в окружении, сформировать презентацию или экспортный пакет.
- Если недоступен, создать markdown-ready handoff для последующей генерации.

## Технические инструкции для Figma Slides

- Использовать skillNames: `figma-use-slides`.
- Все заголовки и подписи на русском.
- Не использовать перегруженные таблицы; длинные таблицы переводить в упрощенные схемы.
- Для Mermaid-схем использовать либо перерисованные блоки, либо сжатые версии как визуальные flow diagrams.
- На каждом слайде один главный тезис.
- Не утверждать, что Figma deck создан, если нет фактического результата из Figma tool.

