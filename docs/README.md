# Документация AI Discovery Platform

Дата: 2026-05-17

## Назначение

Этот раздел содержит пакет документов для развития AI Discovery Platform до целевого промышленного вида. Документы написаны на русском языке и пригодны для передачи в разработку.

## Бизнес и системный анализ

- [Бизнес-требования на развитие AI Discovery Platform](business/bt-ai-discovery-platform-target.md)
- [Техническое задание на развитие AI Discovery Platform](system/tz-ai-discovery-platform-target.md)

## Архитектура

- [Индекс архитектурной документации](architecture/README.md)
- [ADR-002: Целевая архитектура развития AI Discovery Platform](architecture/adr-002-target-platform-evolution.md)
- [Целевая архитектура AI Discovery Platform](architecture/target-architecture.md)
- [Контракт SimpleRetriever](architecture/simple-retriever-contract.md)
- [Roadmap Agent Runtime](architecture/agent-runtime-roadmap.md)
- [ADR-001: Выбор open-source AI/RAG/agent framework](architecture/ADR-001-agent-and-rag-framework-selection.md)
- [Контракт Agent Runtime](architecture/agent-runtime-contract.md)
- [Архитектурные схемы](architecture/diagrams/README.md)
- [Текущий API contract](api/openapi-contracts-current.md)

## Backlog и roadmap

- [Продуктовый backlog AI Discovery Platform](backlog/product-backlog.md)
- [Roadmap развития AI Discovery Platform](backlog/roadmap.md)
- [Backend backlog](backlog/backend-backlog.md)
- [Frontend backlog](backlog/frontend-backlog.md)
- [Backlog traceability matrix](backlog/backlog-traceability-matrix.md)
- [Структура Trello-доски](backlog/trello-board-import.md)
- [Trello-карточки](backlog/trello-cards.md)
- [Gantt delivery plan](ai-delivery-agents/07-gantt-delivery-plan.md)

## LLM/RAG, данные, безопасность и качество

- [Целевая RAG/retrieval-архитектура](llm-rag/rag-and-retrieval-target-design.md)
- [Целевая модель данных](data/data-model-target.md)
- [Требования безопасности](security/security-requirements.md)
- [Каталог метрик](metrics/metrics-catalog.md)
- [Стратегия тестирования](qa/test-strategy.md)

## UX, эксплуатация и процессы

- [Целевая UX/UI-спецификация](design/ux-ui-target-spec.md)
- [Design documentation](design/README.md)
- [Design system](design/design-system.md)
- [Screen inventory](design/screen-inventory.md)
- [Context screen spec](design/context-screen-spec.md)
- [Операционная модель Trello](process/trello-operating-model.md)
- [Пользовательская инструкция](user-guide/user-guide.md)
- [Инструкция локального запуска](runbook/local-runbook.md)
- [Глоссарий](glossary.md)

## Presentations

- [Management platform overview](presentations/management-platform-overview.md)
- [Figma Slides brief](presentations/figma-use-slides-brief.md)
- [Visual style презентации](design/management-presentation-visual-style.md)

## Ограничения delivery

- Production-код не меняется на этапе ревизии и документации.
- Внешние dependencies не добавляются без ADR и license/dependency gate.
- API-контракты не меняются без отдельного ADR.
- LangGraph, LlamaIndex и Haystack подключаются только после стабилизации собственного runtime.
- Dify, Flowise и RAGFlow не используются как foundation платформы.
