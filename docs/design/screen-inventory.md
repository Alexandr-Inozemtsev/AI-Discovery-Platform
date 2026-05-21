# Screen inventory AI Discovery Platform

| Экран | Назначение | Ключевые блоки | Данные | Основные действия | AI-сценарии | Состояния |
|---|---|---|---|---|---|---|
| Home / Landing | Быстрый вход в проекты и текущий Discovery. | Последние проекты, completion, быстрые действия. | Projects, completion. | Открыть проект, создать проект. | Future recommendations. | empty, loading, error. |
| Projects list | Управление списком проектов. | Таблица/карточки проектов, actions. | ProjectRead. | Create, open, clone, archive/delete, export. | Нет. | loading, empty, error. |
| Project workspace | Основной рабочий контур Discovery. | Sidebar stages, top actions, editor area, AI actions. | Project, ArtifactRead, CompletionResponse. | Save, generate, validate, export. | Generate, ask, apply patch. | loading, stale, error, ready. |
| Context stage | Сбор контекста и источников знаний. | Manual context, source list, upload, links, extracted knowledge, readiness. | CONTEXT structured_content. | Upload, analyze, save, перейти к Problem. | ContextIngestionAgent analyze. | empty, metadata-only, indexing, ready, warning, error. |
| Problem stage | Формулировка проблемы. | Problem draft, AI questions, patch preview, source trace. | PROBLEM artifact, problem_handoff. | Generate, ask, apply patch, save. | Problem generation, clarifying questions. | draft, needs_clarification, ready, stale. |
| Goal stage | Формирование цели и SMART. | Goal options, recommended goal, KPI, SMART analysis. | GOAL artifact. | Generate, choose, edit, save. | Goal generation, KPI suggestions. | warning, ready, stale. |
| Business Effect | Бизнес-эффект инициативы. | Value, cost/risk effects, metrics. | BUSINESS_EFFECT artifact. | Generate, edit, validate. | Business effect generation. | empty, ready, stale. |
| AS IS | Текущее состояние процесса. | Process description, actors, systems, pain points. | AS_IS artifact. | Generate, edit. | AS IS generation. | empty, ready, stale. |
| TO BE | Целевое состояние. | Target process, changes, controls. | TO_BE artifact. | Generate, edit. | TO BE generation. | empty, ready, stale. |
| Use Cases | Сценарии использования. | Actors, scenarios, pre/post conditions. | USE_CASES artifact. | Generate, edit. | Use case generation. | empty, ready, stale. |
| Requirements | Функциональные и нефункциональные требования. | Requirement list, priority, acceptance. | FUNCTIONAL_REQUIREMENTS, NON_FUNCTIONAL_REQUIREMENTS. | Generate, edit, validate. | Requirements generation. | empty, ready, stale. |
| Risks | Риски и ограничения. | Risk list, severity, mitigation. | RISKS artifact. | Generate, edit. | Risk generation. | empty, warning, ready. |
| Final BT | Сборка финального БТ. | Completion, validation report, export. | FINAL_BT, artifacts, completion. | Generate, validate, export DOCX. | CriticAgent validation. | incomplete, ready, error. |
| LLM Settings | Настройка provider. | Provider, base URL, model, masked key, test. | LLM settings. | Save, test connection. | Runtime readiness. | mock, connected, error, timeout, unauthorized. |
| Future Sources Settings | Настройки источников знаний. | Allowlist, limits, parser mode. | Source settings. | Configure, test. | Corporate RAG/parser checks. | draft, ready, blocked. |
| Future Corporate RAG Settings | Настройка Corporate RAG. | Endpoint, auth mode, search scopes, mapping. | Corporate RAG config. | Configure, test, approve. | RAG retrieval test. | not_configured, connected, error. |
| Future Presentation/Export Center | Управление экспортами и презентациями. | DOCX, PPTX, management deck, export history. | Export manifest. | Export, download, regenerate. | Presentation assistant. | ready, stale, error. |

## Связанные документы

- [Design system](design-system.md)
- [Context screen spec](context-screen-spec.md)
- [Current OpenAPI contract](../api/openapi-contracts-current.md)

