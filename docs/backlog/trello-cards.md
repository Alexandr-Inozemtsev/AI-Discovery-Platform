# Trello-карточки AI Discovery Platform

> Важно: этот файл описывает карточки для глобального delivery-процесса разработки AI Discovery Platform. Ответственные `ai-*` агенты здесь являются глобальными Codex delivery agents, а не runtime-агентами продукта.

Дата: 2026-05-17

## Формат карточки

Каждая карточка ниже пригодна для ручного переноса в Trello. При автоматическом создании в Trello описание карточки должно содержать цель, описание, критерии приёмки, dependencies, ответственного агента, приоритет, labels и definition of done. Checklist отражает минимальный delivery scope.

## Карточки эпиков

### ЭПИК-01 Продуктовый фундамент и сквозной Discovery-процесс

Список: `01 Продуктовый backlog`
Labels: Продукт, MVP
Ответственный агент: ai-product-orchestrator
Приоритет: P0

Цель: оформить платформу как единое рабочее пространство Discovery.
Описание: пользователь должен вести проект от контекста до финального БТ с понятным прогрессом, readiness и следующими действиями.
Критерии приёмки: есть lifecycle проекта, статусы, этапы, dependencies и критерии перехода к разработке.
Dependencies: БТ, ТЗ, UI/UX, data model.
Definition of Done: flow описан, включён в roadmap и связан с карточками разработки.

Checklist:
- Описать lifecycle Discovery-проекта.
- Зафиксировать статусы и переходы.
- Связать этапы с artifacts.
- Описать DoR для передачи в разработку.

### ЭПИК-02 Источники контекста, извлечение текста и индексация знаний

Список: `02 Discovery / анализ`
Labels: Backend, Данные, MVP, Риск
Ответственный агент: ai-backend-developer
Приоритет: P0

Цель: сделать контекст проверяемым и пригодным для retrieval.
Описание: источники должны иметь статусы обработки, версии, chunks, ошибки и traceability.
Критерии приёмки: TXT/MD/CSV/DOCX/PDF/XLSX обрабатываются по правилам, ошибки видимы пользователю.
Dependencies: SimpleRetriever, security, data model.
Definition of Done: требования к sources/chunks/statuses включены в ТЗ и backlog.

Checklist:
- Описать `ContextSource`.
- Описать `SourceChunk`.
- Зафиксировать статусы обработки.
- Описать ограничения размера и форматов.

### ЭПИК-03 Runtime агентов и оркестрация

Список: `03 Архитектура / ADR`
Labels: Архитектура, Backend, MVP, Риск
Ответственный агент: ai-solution-architect
Приоритет: P0

Цель: стабилизировать agent runtime без замены платформы внешним framework.
Описание: все агенты должны работать через единый контракт запуска, результата и ошибок.
Критерии приёмки: trace id, prompt version, provider/model metadata, warnings/errors и fallback policy описаны.
Dependencies: ADR-002, LLM settings, audit log.
Definition of Done: runtime roadmap и контракт готовы к реализации.

Checklist:
- Описать `AgentContext`.
- Описать `AgentResult`.
- Описать `AgentRun`.
- Зафиксировать fallback policy.

### ЭПИК-04 SimpleRetriever и генерация с опорой на источники

Список: `03 Архитектура / ADR`
Labels: LLM/RAG, MVP, Риск
Ответственный агент: ai-llm-rag-engineer
Приоритет: P0

Цель: обеспечить retrieval без внешних зависимостей.
Описание: SimpleRetriever выбирает релевантные chunks и передаёт их агентам вместе с source trace.
Критерии приёмки: top-k hits, score, source metadata и ограничения данных описаны.
Dependencies: chunks, AgentRuntime, source_trace.
Definition of Done: contract и quality metrics готовы.

Checklist:
- Описать query input.
- Описать `RetrievalHit`.
- Описать scoring.
- Описать передачу trace в Problem/Goal/Requirements.

### ЭПИК-05 Этапы «Проблема», «Цель» и «Бизнес-эффект»

Список: `02 Discovery / анализ`
Labels: Продукт, Бизнес-анализ, MVP
Ответственный агент: ai-business-analyst
Приоритет: P0

Цель: сделать первые этапы Discovery связными и проверяемыми.
Описание: AI должен формировать проблему, цель и бизнес-эффект на основе контекста и уточнений пользователя.
Критерии приёмки: результат содержит evidence, assumptions, missing information и source trace.
Dependencies: Context, SimpleRetriever.
Definition of Done: структура артефактов описана и включена в ТЗ.

Checklist:
- Описать Problem artifact.
- Описать Goal artifact.
- Описать Business Effect artifact.
- Зафиксировать readiness gate.

### ЭПИК-06 Этапы AS IS, TO BE и Use Cases

Список: `02 Discovery / анализ`
Labels: Системный анализ, MMP
Ответственный агент: ai-system-analyst
Приоритет: P1

Цель: расширить Discovery до описания процессов и сценариев.
Описание: AS IS, TO BE и Use Cases должны быть связаны с ролями, системами, исключениями и источниками.
Критерии приёмки: use cases содержат basic, alternative, negative flows и edge cases.
Dependencies: Problem, Goal, Business Effect.
Definition of Done: структура этапов готова к реализации.

Checklist:
- Описать AS IS.
- Описать TO BE.
- Описать Use Case template.
- Зафиксировать сравнение AS IS/TO BE.

### ЭПИК-07 Функциональные и нефункциональные требования

Список: `04 Готово к разработке`
Labels: Системный анализ, ТЗ, MVP
Ответственный агент: ai-system-analyst
Приоритет: P0

Цель: формировать требования для delivery.
Описание: требования должны иметь ID, приоритет, источник, риск, acceptance criteria и зависимости.
Критерии приёмки: FR и NFR разделены и связаны с use cases.
Dependencies: Use Cases, TO BE, security.
Definition of Done: требования экспортируются в финальный БТ.

Checklist:
- Описать поля requirement item.
- Описать статусы требований.
- Описать NFR categories.
- Описать проверку полноты.

### ЭПИК-08 Финальный БТ, DOCX-экспорт и шаблоны документов

Список: `04 Готово к разработке`
Labels: БТ, Документация, MVP
Ответственный агент: ai-technical-writer
Приоритет: P0

Цель: собрать формальный результат Discovery.
Описание: финальный БТ должен включать все этапы, источники, версии, риски и открытые вопросы.
Критерии приёмки: DOCX создаётся повторяемо, пустые разделы отмечены.
Dependencies: все Discovery stages.
Definition of Done: шаблон и правила экспорта описаны.

Checklist:
- Описать структуру БТ.
- Описать DOCX template.
- Описать приложение source trace.
- Описать validation report.

### ЭПИК-09 Настройки LLM, управление провайдерами и корпоративный режим

Список: `03 Архитектура / ADR`
Labels: LLM/RAG, Безопасность, MVP
Ответственный агент: ai-llm-rag-engineer
Приоритет: P0

Цель: контролировать LLM providers и режимы работы.
Описание: поддержать mock, OpenRouter и корпоративный OpenAI-compatible provider без раскрытия секретов.
Критерии приёмки: есть connection status, latency, actual model, masked key и понятные ошибки.
Dependencies: security, DevOps.
Definition of Done: data policy и fallback policy описаны.

Checklist:
- Описать LLM settings.
- Описать проверку подключения.
- Описать corporate mode.
- Описать запрет логирования ключей.

### ЭПИК-10 UI/UX платформы и единый UI Kit

Список: `04 Готово к разработке`
Labels: Frontend, MVP
Ответственный агент: ai-ui-ux-designer
Приоритет: P1

Цель: обеспечить единый рабочий UX.
Описание: интерфейс должен помогать аналитику проходить этапы без потери контекста и источников.
Критерии приёмки: описаны экраны, состояния, UI Kit, readiness/progress/source trace.
Dependencies: frontend backlog.
Definition of Done: UX spec готова к реализации.

Checklist:
- Описать Project Dashboard.
- Описать Context screen.
- Описать Discovery stages.
- Описать UI states.

### ЭПИК-11 Модель данных, версионирование и аудит

Список: `03 Архитектура / ADR`
Labels: Данные, MVP, Риск
Ответственный агент: ai-database-engineer
Приоритет: P0

Цель: обеспечить версионирование и аудит.
Описание: нужны отдельные сущности sources, chunks, artifact versions, audit events и LLM run log.
Критерии приёмки: migration backlog описан, обратная совместимость учтена.
Dependencies: backend, security, runtime.
Definition of Done: data model target готов.

Checklist:
- Описать текущие сущности.
- Описать целевые сущности.
- Описать миграции.
- Описать audit и rollback.

### ЭПИК-12 Безопасность, приватность и защита от prompt injection

Список: `03 Архитектура / ADR`
Labels: Безопасность, MVP, Риск
Ответственный агент: ai-security-reviewer
Приоритет: P0

Цель: снизить риски LLM и корпоративных данных.
Описание: определить требования к секретам, privacy, prompt injection, external connectors и access control.
Критерии приёмки: security requirements включены в ТЗ и QA.
Dependencies: LLM settings, audit.
Definition of Done: backlog security-задач сформирован.

Checklist:
- Описать secret policy.
- Описать data privacy.
- Описать prompt injection controls.
- Описать audit requirements.

### ЭПИК-13 Метрики продукта, аналитика и мониторинг качества AI

Список: `04 Готово к разработке`
Labels: Продукт, Данные, MMP
Ответственный агент: ai-data-metrics-engineer
Приоритет: P1

Цель: измерять продуктовый эффект и качество AI.
Описание: нужны activation, adoption, retention, export conversion, readiness, retrieval hit rate, fallback rate и user edit rate.
Критерии приёмки: каталог метрик и event backlog готовы.
Dependencies: event tracking, audit, runtime.
Definition of Done: метрики имеют формулу, источник и владельца.

Checklist:
- Описать product metrics.
- Описать AI quality metrics.
- Описать события.
- Описать dashboard backlog.

### ЭПИК-14 Окружения, запуск, DevOps и CI/CD

Список: `04 Готово к разработке`
Labels: DevOps, MMP
Ответственный агент: ai-devops-engineer
Приоритет: P1

Цель: сделать запуск и поставку повторяемыми.
Описание: описать local/dev/test/stage/prod, Windows без Docker, Docker для dev/prod и CI/CD gates.
Критерии приёмки: runbook и pipeline backlog готовы.
Dependencies: QA, security.
Definition of Done: quality gates описаны.

Checklist:
- Описать local run.
- Описать Docker run.
- Описать CI/CD.
- Описать rollback.

### ЭПИК-15 QA, тестирование и валидация

Список: `07 QA / проверка`
Labels: QA, MVP
Ответственный агент: ai-qa-engineer
Приоритет: P0

Цель: обеспечить проверяемость платформы.
Описание: тесты должны покрывать extraction, ContextIngestionAgent, SimpleRetriever, Problem, LLM settings, DOCX export и frontend flows.
Критерии приёмки: test strategy и acceptance criteria готовы.
Dependencies: ТЗ, backend/frontend backlog.
Definition of Done: test pyramid и regression scope описаны.

Checklist:
- Описать unit tests.
- Описать integration tests.
- Описать E2E flows.
- Описать test data.

### ЭПИК-16 Документация и пользовательские инструкции

Список: `08 Готово`
Labels: Документация, MVP
Ответственный агент: ai-technical-writer
Приоритет: P0

Цель: подготовить документы для команды и пользователей.
Описание: нужны docs README, user guide, runbook, glossary и Trello operating model.
Критерии приёмки: документы имеют русские заголовки и ссылки друг на друга.
Dependencies: все профильные документы.
Definition of Done: документация готова для передачи в разработку.

Checklist:
- Создать docs README.
- Создать user guide.
- Создать runbook.
- Создать glossary.

### ЭПИК-17 Trello и операционная модель delivery-процесса

Список: `08 Готово`
Labels: Trello, MVP
Ответственный агент: ai-trello-analyst
Приоритет: P0

Цель: оформить Trello-доску под delivery.
Описание: списки, labels, карточки и checklists должны отражать процесс от backlog до QA и Done.
Критерии приёмки: доска создана автоматически или подготовлен manual import package.
Dependencies: product backlog.
Definition of Done: Trello report зафиксирован в финальном отчёте.

Checklist:
- Создать списки.
- Создать labels.
- Создать карточки эпиков.
- Добавить checklists.

### ЭПИК-18 Будущие RAG-адаптеры: LlamaIndex и Haystack

Список: `03 Архитектура / ADR`
Labels: LLM/RAG, Целевой контур
Ответственный агент: ai-llm-rag-engineer
Приоритет: P2

Цель: подготовить optional RAG adapters.
Описание: LlamaIndex/Haystack допускаются только после SimpleRetriever и через adapter boundary.
Критерии приёмки: есть PoC plan, license gate и rollback.
Dependencies: SimpleRetriever.
Definition of Done: отдельный ADR перед добавлением dependencies.

Checklist:
- Описать adapter interface.
- Описать критерии выбора.
- Описать PoC.
- Описать license gate.

### ЭПИК-19 Будущий workflow-адаптер: LangGraph для цепочки «Контекст -> Проблема»

Список: `03 Архитектура / ADR`
Labels: Архитектура, Целевой контур
Ответственный агент: ai-solution-architect
Приоритет: P2

Цель: оценить LangGraph как optional workflow adapter.
Описание: пилот допустим только после стабилизации runtime и только для Context -> Problem.
Критерии приёмки: PoC отключаем без миграции данных.
Dependencies: AgentRuntime, audit, rollback.
Definition of Done: отдельный ADR и test plan.

Checklist:
- Описать state machine.
- Описать human-in-the-loop.
- Описать rollback.
- Описать критерии отказа от adapter.

### ЭПИК-20 Коммерциализация, упаковка и готовность к монетизации

Список: `01 Продуктовый backlog`
Labels: Продукт, Целевой контур
Ответственный агент: ai-product-orchestrator
Приоритет: P2

Цель: подготовить платформу к пилотной и коммерческой эксплуатации.
Описание: нужны packaging, license review, support model, ограничения поставки и monetization readiness.
Критерии приёмки: checklist коммерческой готовности описан.
Dependencies: security, docs, DevOps, metrics.
Definition of Done: pilot package готов к обсуждению.

Checklist:
- Описать pilot package.
- Описать license checklist.
- Описать support model.
- Описать ограничения поставки.
