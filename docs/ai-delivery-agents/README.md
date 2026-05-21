# Контур глобальных Codex-агентов разработки

Эта папка описывает отдельный delivery-контур глобальных Codex-агентов разработки AI Discovery Platform.

Контур НЕ является runtime-контуром продуктовых AI-агентов внутри приложения. Он не описывает backend services, классы из `discovery-ai-agent/backend/app/agents`, endpoint-оркестрацию или продуктовый `AgentOrchestrator`.

Документы используются для управления разработкой: backlog, Trello, Gantt, quality gates, handoff, review, release readiness и координация задач в Codex. Каждый Codex-agent здесь является ролью или профилем исполнения задач через Codex, а не сервисом backend-приложения.

## Структура

- `00-agent-operating-model.md` - операционная модель подключения агентов.
- `01-agent-registry.md` - реестр глобальных Codex delivery agents.
- `02-agent-interaction-policy.md` - политики взаимодействия, handoff и review.
- `03-codex-orchestrator-prompt.md` - главный промпт для `ai-orchestrator`.
- `04-handoff-matrix.md` - матрица передачи результатов между ролями.
- `05-quality-gates.md` - обязательные gates качества.
- `06-trello-operating-model.md` - модель работы с Trello и manual import package.
- `07-gantt-delivery-plan.md` - draft Mermaid Gantt на 6-8 недель.
- `08-agent-task-routing.md` - маршрутизация типовых задач.
- `09-definition-of-done.md` - общий Definition of Done.
- `10-glossary-agent-layers.md` - глоссарий слоев AI-агентов.
- `agents/` - профили отдельных глобальных Codex-агентов.
- `prompt-packs/` - готовые prompt packs для типовых работ.
- `templates/` - шаблоны задач, handoff, review и Trello-карточек.

## Правило разделения

Product AI Agents создаются для пользователей продукта и живут в runtime приложения. Global Codex Delivery Agents используются владельцем проекта для разработки самой платформы. Любой документ или задача должны явно указывать, к какому слою относятся агенты.

