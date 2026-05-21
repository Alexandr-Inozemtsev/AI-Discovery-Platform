# Management presentation source: AI Discovery Platform

Статус: source package для PowerPoint/Figma Slides.  
Аудитория: руководитель, C-level, руководитель ИТ, product leadership.  
Язык: русский.

## Slide 1. Титульный слайд

**Title:** AI Discovery Platform  
**Key message:** Управляемая платформа подготовки Discovery и БТ.  
**Bullets:**
- Единый workspace от контекста до финального БТ.
- AI-помощники по этапам Discovery.
- Traceability до источников и управляемая готовность.
**Suggested visual:** Темный титульный слайд с простой схемой Context -> Final BT.  
**Linked source docs:** [ТЗ](../system/tz-ai-discovery-platform-target.md), [C4 Context](../architecture/diagrams/01-c4-context.md)

## Slide 2. Проблема

**Title:** Discovery сейчас фрагментирован  
**Key message:** Контекст теряется, требования собираются вручную, а traceability до источников отсутствует.  
**Bullets:**
- Источники разбросаны по файлам, ссылкам, Confluence, Jira/Trello.
- Требования зависят от ручной консолидации.
- Сложно доказать, на чем основаны выводы AI/аналитика.
**Suggested visual:** Диаграмма разрозненных источников, сходящихся в ручной процесс.  
**Linked source docs:** [ТЗ](../system/tz-ai-discovery-platform-target.md)

## Slide 3. Цель платформы

**Title:** Единое рабочее пространство Discovery  
**Key message:** Платформа управляет переходом от контекста к проблеме, цели, требованиям и финальному БТ.  
**Bullets:**
- AI помогает на каждом этапе, но пользователь подтверждает результат.
- Артефакты версионируются.
- DOCX export формирует итоговый документ.
**Suggested visual:** Процессная лента Discovery stages.  
**Linked source docs:** [Artifact lifecycle](../architecture/diagrams/05-discovery-artifact-lifecycle.md)

## Slide 4. Ценность для руководства

**Title:** Управляемость, скорость и снижение риска  
**Key message:** Платформа ускоряет подготовку Discovery и делает качество требований измеримым.  
**Bullets:**
- Быстрее собрать и структурировать контекст.
- Меньше риска неполных требований.
- Прозрачность источников и readiness.
- Повторяемый процесс вместо ручной импровизации.
**Suggested visual:** Value/risk control matrix.  
**Linked source docs:** [Backlog traceability](../backlog/backlog-traceability-matrix.md)

## Slide 5. Как работает платформа

**Title:** Context -> Problem -> Goal -> Requirements -> Final BT  
**Key message:** Каждый этап использует предыдущий как source of truth и сохраняет evidence.  
**Bullets:**
- Context формирует extracted knowledge.
- Problem и Goal grounded на источниках.
- Requirements и Final BT собираются из подтвержденных artifacts.
**Suggested visual:** Lifecycle схема.  
**Linked source docs:** [Artifact lifecycle](../architecture/diagrams/05-discovery-artifact-lifecycle.md)

## Slide 6. Архитектура верхнего уровня

**Title:** Архитектура MVP и corporate target  
**Key message:** MVP уже имеет frontend/backend/runtime/export, corporate contour добавляет LLM/RAG/IAM/audit.  
**Bullets:**
- React/Vite frontend и FastAPI backend.
- Agent Runtime и LLM Gateway.
- SimpleRetriever и Corporate RAG target.
- DOCX Export Service.
**Suggested visual:** C4 Container.  
**Linked source docs:** [C4 Container](../architecture/diagrams/02-c4-container.md), [Agent Runtime Contract](../architecture/agent-runtime-contract.md)

## Slide 7. Работа с контекстом

**Title:** Контекст становится управляемым knowledge layer  
**Key message:** Файлы, ссылки и ручной контекст превращаются в chunks, source_trace, coverage и readiness.  
**Bullets:**
- Upload files и links.
- Text extraction и chunking.
- ContextIngestionAgent.
- Readiness для перехода к Problem.
**Suggested visual:** Context ingestion and RAG flow.  
**Linked source docs:** [Context/RAG diagram](../architecture/diagrams/04-context-ingestion-and-rag.md), [RAG design](../llm-rag/rag-and-retrieval-target-design.md)

## Slide 8. Новый сценарий ссылок

**Title:** Issue #75: ссылки через Corporate RAG и Universal Parser  
**Key message:** Ссылки должны обрабатываться безопасно: сначала corporate RAG, затем controlled parser flow.  
**Bullets:**
- CorporateRagConnector возвращает chunks из корпоративного знания.
- UniversalLinkParser извлекает текст и вложения.
- SSRF protection, allowlist, size limits, no executable files.
**Suggested visual:** Два сценария A/B.  
**Linked source docs:** [Link processing diagram](../architecture/diagrams/06-link-processing-corporate-rag-and-parser.md)

## Slide 9. Human-in-the-loop

**Title:** AI предлагает, пользователь подтверждает  
**Key message:** Решения остаются под контролем пользователя, а изменения artifacts управляются версиями.  
**Bullets:**
- AI генерирует draft/patch.
- Пользователь применяет или редактирует.
- Downstream stages становятся stale при upstream changes.
- Validation проверяет готовность.
**Suggested visual:** Feedback loop AI -> user -> artifact -> validation.  
**Linked source docs:** [Agent Runtime Flow](../architecture/diagrams/03-agent-runtime-flow.md)

## Slide 10. Roadmap / Gantt

**Title:** Roadmap на 6-8 недель до pilot readiness  
**Key message:** План связывает architecture, context/RAG, security, UI, backend, QA и презентационные artifacts.  
**Bullets:**
- Architecture docs before implementation.
- Security before Universal Parser.
- Tests before release readiness.
- Management presentation как отдельный delivery artifact.
**Suggested visual:** Упрощенный Gantt v2.  
**Linked source docs:** [Gantt](../ai-delivery-agents/07-gantt-delivery-plan.md)

## Slide 11. Риски и контроль

**Title:** Ключевые риски управляемы через gates  
**Key message:** Главные риски известны: LLM readiness, права доступа, prompt injection, SSRF, audit.  
**Bullets:**
- Security gate для corporate provider/parser.
- Error envelope и API contract.
- Audit и access control для pilot.
- Provider settings без раскрытия secrets.
**Suggested visual:** Risk/control table 2x4.  
**Linked source docs:** [Quality gates](../ai-delivery-agents/05-quality-gates.md), [Security requirements](../security/security-requirements.md)

## Slide 12. Что уже сделано

**Title:** Есть рабочий MVP и документационный контур  
**Key message:** Платформа уже имеет базовые функции и backlog для hardening.  
**Bullets:**
- MVP приложение.
- Context stage и LLM settings.
- DOCX export.
- Базовые product agents.
- Architecture docs, backlog, Gantt.
**Suggested visual:** Checklist done/current.  
**Linked source docs:** [Architecture README](../architecture/README.md), [Trello cards](../backlog/trello-cards.md)

## Slide 13. Что нужно для пилота

**Title:** Условия corporate pilot  
**Key message:** Для пилота нужны корпоративные интеграции, безопасность и тестовые данные.  
**Bullets:**
- Corporate LLM.
- Corporate RAG API.
- Security approval.
- Роли/доступы.
- Test data и pilot team.
**Suggested visual:** Pilot readiness checklist.  
**Linked source docs:** [Deployment diagram](../architecture/diagrams/07-deployment-local-and-corporate.md)

## Slide 14. Решение / next steps

**Title:** Решения, которые нужны от руководства  
**Key message:** Нужно согласовать roadmap, corporate RAG contract, pilot use case и hardening backlog.  
**Bullets:**
- Подтвердить roadmap 6-8 недель.
- Согласовать corporate RAG contract.
- Выбрать pilot use case.
- Запустить hardening backlog.
**Suggested visual:** Decision board: approve / assign / launch.  
**Linked source docs:** [Backlog traceability](../backlog/backlog-traceability-matrix.md), [Gantt](../ai-delivery-agents/07-gantt-delivery-plan.md)

