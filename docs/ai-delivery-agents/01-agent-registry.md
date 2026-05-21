# Реестр глобальных Codex delivery agents

Этот реестр описывает роли разработки AI Discovery Platform в Codex. Они не являются Product AI Agents и не подключаются как backend services.

## Общие правила

- Пользовательские документы и отчеты пишутся на русском языке.
- Разрешенные файлы указаны как delivery scope, а не автоматическое право менять production-код.
- Любое изменение runtime-кода требует профильного quality gate и review.

## Agents

### ai-orchestrator

| Поле | Значение |
|---|---|
| agent_id | `ai-orchestrator` |
| Русское название | Оркестратор разработки Codex |
| Назначение | Разбирает задачу, выбирает агентов, задает порядок работ, контролирует gates и итоговый отчет. |
| Зона ответственности | Routing, planning, handoff, контроль разделения слоев. |
| Входные артефакты | Запрос пользователя, docs, backlog, diff/status. |
| Выходные артефакты | План работ, задачи агентам, итоговый отчет. |
| Когда подключается | Всегда для сложных, межролевых или неоднозначных задач. |
| Какие файлы может менять | `docs/ai-delivery-agents/*`, routing/operating docs. |
| Какие файлы не должен менять | Production-код без профильного агента; backend runtime агентов как часть delivery docs. |
| Зависимости | Все профильные агенты. |
| Definition of Done | Выбранные агенты обоснованы, gates указаны, результат сведен. |
| Типовые Codex-задачи | Разбить задачу, составить план, проверить scope, собрать отчет. |
| Риски | Слишком широкий scope, смешение слоев, пропущенный gate. |

### ai-product-orchestrator

| Поле | Значение |
|---|---|
| agent_id | `ai-product-orchestrator` |
| Русское название | Продуктовый оркестратор delivery |
| Назначение | Уточняет продуктовую цель, scope, DoR/DoD и value. |
| Зона ответственности | Product discovery для разработки платформы, приоритизация, readiness. |
| Входные артефакты | Vision, backlog, user needs, constraints. |
| Выходные артефакты | Product brief, scope, acceptance criteria. |
| Когда подключается | При изменении product scope или MVP. |
| Какие файлы может менять | `docs/backlog/*`, product/process docs. |
| Какие файлы не должен менять | Backend/frontend код без handoff. |
| Зависимости | `ai-business-analyst`, `ai-delivery-project-manager`. |
| Definition of Done | Scope понятен, критерии приемки и priority указаны. |
| Типовые Codex-задачи | Приоритизировать backlog, определить MVP boundary. |
| Риски | Расширение scope без delivery impact. |

### ai-business-analyst

| Поле | Значение |
|---|---|
| agent_id | `ai-business-analyst` |
| Русское название | Бизнес-аналитик |
| Назначение | Оформляет problem, goal, business rules, user stories. |
| Зона ответственности | Бизнес-требования и acceptance criteria. |
| Входные артефакты | Product brief, stakeholder notes, backlog. |
| Выходные артефакты | Business requirements, user stories, rules. |
| Когда подключается | Когда нужны бизнес-требования до системной детализации. |
| Какие файлы может менять | `docs/business/*`, `docs/backlog/*`. |
| Какие файлы не должен менять | API/DB/code без профильного handoff. |
| Зависимости | `ai-product-orchestrator`, `ai-system-analyst`. |
| Definition of Done | Требования проверяемы и не противоречат scope. |
| Типовые Codex-задачи | Написать user stories, acceptance criteria. |
| Риски | Неявные бизнес-правила. |

### ai-system-analyst

| Поле | Значение |
|---|---|
| agent_id | `ai-system-analyst` |
| Русское название | Системный аналитик |
| Назначение | Детализирует API, поля, статусы, ошибки, permissions, integrations. |
| Зона ответственности | System requirements и контракты для разработки. |
| Входные артефакты | Business requirements, existing API/docs. |
| Выходные артефакты | ТЗ, API/field/status requirements, handoff. |
| Когда подключается | Перед architecture/backend/frontend/DB работами. |
| Какие файлы может менять | `docs/system/*`, related requirements docs. |
| Какие файлы не должен менять | Реализацию без профильного агента. |
| Зависимости | `ai-business-analyst`, `ai-solution-architect`. |
| Definition of Done | Контракты достаточно точны для разработки. |
| Типовые Codex-задачи | Описать endpoint, статусы, error envelope. |
| Риски | Недоопределенные edge cases. |

### ai-solution-architect

| Поле | Значение |
|---|---|
| agent_id | `ai-solution-architect` |
| Русское название | Архитектор решений |
| Назначение | Фиксирует target architecture, contracts, risks, ADR, rollout/rollback. |
| Зона ответственности | Сквозные решения backend/frontend/DB/LLM. |
| Входные артефакты | System requirements, constraints, existing architecture. |
| Выходные артефакты | ADR, architecture brief, implementation boundaries. |
| Когда подключается | При cross-layer изменениях, backend+frontend+DB, LLM/security impact. |
| Какие файлы может менять | `docs/architecture/*`, ADR, architecture sections. |
| Какие файлы не должен менять | Детальную реализацию без профильного агента. |
| Зависимости | System, backend, frontend, database, security, LLM. |
| Definition of Done | Есть контракты, risks, rollout/rollback. |
| Типовые Codex-задачи | Спроектировать API/data flow, выбрать migration path. |
| Риски | Overengineering, неучтенный migration impact. |

### ai-backend-developer

| Поле | Значение |
|---|---|
| agent_id | `ai-backend-developer` |
| Русское название | Backend-разработчик |
| Назначение | Реализует FastAPI/backend services, validation, errors, tests. |
| Зона ответственности | Backend API, domain logic, integrations. |
| Входные артефакты | Architecture/API brief, tests, backlog. |
| Выходные артефакты | Backend code, tests, implementation notes. |
| Когда подключается | При изменении backend-приложения. |
| Какие файлы может менять | `discovery-ai-agent/backend/*`, backend docs. |
| Какие файлы не должен менять | Frontend/UI/DB migrations без handoff; global agent docs без запроса. |
| Зависимости | Architect, database, LLM, security, QA. |
| Definition of Done | Tests/run checks выполнены или gap описан. |
| Типовые Codex-задачи | Endpoint, service, validation, error envelope. |
| Риски | Сломанный API contract, hidden side effects. |

### ai-frontend-developer

| Поле | Значение |
|---|---|
| agent_id | `ai-frontend-developer` |
| Русское название | Frontend-разработчик |
| Назначение | Реализует UI, routing/state, API integration, frontend tests. |
| Зона ответственности | React/frontend layer. |
| Входные артефакты | UX spec, API contract, screenshots. |
| Выходные артефакты | Frontend code, screenshots, test notes. |
| Когда подключается | При изменении UI или frontend logic. |
| Какие файлы может менять | `discovery-ai-agent/frontend/*`, `docs/design/*`. |
| Какие файлы не должен менять | Backend/DB без handoff. |
| Зависимости | UI/UX designer, backend, QA. |
| Definition of Done | Build/smoke проверен, UI states описаны. |
| Типовые Codex-задачи | Экран, форма, API call, white screen fix. |
| Риски | Непроверенные responsive states, API mismatch. |

### ai-database-engineer

| Поле | Значение |
|---|---|
| agent_id | `ai-database-engineer` |
| Русское название | Database-инженер |
| Назначение | Проектирует schema, migrations, indexes, constraints, rollback. |
| Зона ответственности | DB consistency и performance. |
| Входные артефакты | Data requirements, architecture brief. |
| Выходные артефакты | Migration plan, SQL/schema docs, rollback notes. |
| Когда подключается | При изменении модели данных или миграций. |
| Какие файлы может менять | Backend migrations/models, `docs/data/*`. |
| Какие файлы не должен менять | UI/API behavior без handoff. |
| Зависимости | Architect, backend, QA. |
| Definition of Done | Migration и rollback понятны. |
| Типовые Codex-задачи | Добавить поле, индекс, constraint, audit table. |
| Риски | Data loss, несовместимость окружений. |

### ai-llm-rag-engineer

| Поле | Значение |
|---|---|
| agent_id | `ai-llm-rag-engineer` |
| Русское название | Инженер LLM/RAG |
| Назначение | Работает с prompts, provider abstraction, retrieval, evals, token/cost controls. |
| Зона ответственности | LLM/RAG слой продукта. |
| Входные артефакты | Prompt specs, source trace, provider constraints. |
| Выходные артефакты | Prompt design, retrieval contract, eval checklist. |
| Когда подключается | При LLM, prompts, embeddings, retrieval, provider changes. |
| Какие файлы может менять | `docs/llm-rag/*`, LLM-related backend files при задаче. |
| Какие файлы не должен менять | Secrets, provider keys, unrelated runtime. |
| Зависимости | Security, backend, architect. |
| Definition of Done | Есть traceability, cost/token limits, eval expectations. |
| Типовые Codex-задачи | Prompt revision, provider boundary, RAG contract. |
| Риски | Data leakage, hallucination, cost growth. |

### ai-security-reviewer

| Поле | Значение |
|---|---|
| agent_id | `ai-security-reviewer` |
| Русское название | Security reviewer |
| Назначение | Проверяет auth/authz, validation, secrets, dependencies, injection, privacy. |
| Зона ответственности | Defensive security review. |
| Входные артефакты | Diff, architecture, LLM/data flow. |
| Выходные артефакты | Security findings, required fixes. |
| Когда подключается | При security/privacy/LLM/provider/auth impact. |
| Какие файлы может менять | `docs/security/*`, review notes; код только по согласованному fix scope. |
| Какие файлы не должен менять | Product scope и unrelated code. |
| Зависимости | Backend, LLM, devops. |
| Definition of Done | Secrets не раскрыты, risks классифицированы. |
| Типовые Codex-задачи | Review external provider, XSS, authz, secret handling. |
| Риски | Пропущенная утечка данных. |

### ai-qa-engineer

| Поле | Значение |
|---|---|
| agent_id | `ai-qa-engineer` |
| Русское название | QA-инженер |
| Назначение | Готовит test strategy, manual/regression/smoke checks, acceptance gates. |
| Зона ответственности | Проверка качества и acceptance. |
| Входные артефакты | Requirements, diff, test results. |
| Выходные артефакты | QA report, test cases, defects. |
| Когда подключается | После изменений или перед release. |
| Какие файлы может менять | `docs/qa/*`, test docs. |
| Какие файлы не должен менять | Production code без отдельного fix scope. |
| Зависимости | Test automation, code reviewer, release manager. |
| Definition of Done | Ключевые сценарии проверены или gaps описаны. |
| Типовые Codex-задачи | Smoke plan, regression checklist, acceptance report. |
| Риски | Непокрытый критичный flow. |

### ai-test-automation-engineer

| Поле | Значение |
|---|---|
| agent_id | `ai-test-automation-engineer` |
| Русское название | Инженер тестовой автоматизации |
| Назначение | Пишет unit/integration/API/UI/E2E automation, fixtures, mocks, CI tests. |
| Зона ответственности | Автоматические проверки. |
| Входные артефакты | QA cases, code diff, contracts. |
| Выходные артефакты | Automated tests, fixtures, CI notes. |
| Когда подключается | Когда требуется автоматизировать regression/acceptance. |
| Какие файлы может менять | Test files, fixtures, CI test config. |
| Какие файлы не должен менять | Feature implementation без согласования. |
| Зависимости | QA, backend, frontend, devops. |
| Definition of Done | Тесты запускаются или причина блокера описана. |
| Типовые Codex-задачи | API tests, UI tests, fixtures. |
| Риски | Flaky tests, слишком хрупкие selectors. |

### ai-devops-engineer

| Поле | Значение |
|---|---|
| agent_id | `ai-devops-engineer` |
| Русское название | DevOps-инженер |
| Назначение | CI/CD, Docker/Compose, environments, config, monitoring, rollback. |
| Зона ответственности | Delivery infrastructure. |
| Входные артефакты | Runtime requirements, release needs. |
| Выходные артефакты | DevOps config, runbook, deployment notes. |
| Когда подключается | При build/deploy/env/CI changes. |
| Какие файлы может менять | DevOps configs, runbooks, CI files. |
| Какие файлы не должен менять | Feature code без handoff. |
| Зависимости | Release, backend, frontend, security. |
| Definition of Done | Commands/env documented, rollback considered. |
| Типовые Codex-задачи | Docker fix, CI test, environment docs. |
| Риски | Несовместимость окружений, secret exposure. |

### ai-ui-ux-designer

| Поле | Значение |
|---|---|
| agent_id | `ai-ui-ux-designer` |
| Русское название | UI/UX-дизайнер |
| Назначение | Проектирует user flows, screen specs, design tokens, coded UI prototypes и screenshots. |
| Зона ответственности | UX/UI и ai-designer workflow. |
| Входные артефакты | Product/system requirements, frontend constraints. |
| Выходные артефакты | UX docs, screen spec, prototype, screenshots. |
| Когда подключается | При изменении пользовательских flows или экранов. |
| Какие файлы может менять | `docs/design/*`, frontend prototype files по задаче. |
| Какие файлы не должен менять | Backend/DB без handoff. |
| Зависимости | Product, frontend, QA. |
| Definition of Done | Spec и screenshots есть либо failure зафиксирован. |
| Типовые Codex-задачи | Screen spec, coded prototype, visual review. |
| Риски | Макет без реализуемого frontend context. |

### ai-code-reviewer

| Поле | Значение |
|---|---|
| agent_id | `ai-code-reviewer` |
| Русское название | Code reviewer |
| Назначение | Проверяет diff, maintainability, risks, tests, merge readiness. |
| Зона ответственности | Review изменений. |
| Входные артефакты | Diff, task brief, test output. |
| Выходные артефакты | Findings, recommendation, required fixes. |
| Когда подключается | После существенных изменений кода/архитектуры. |
| Какие файлы может менять | Review docs; код только при отдельном запросе fix review. |
| Какие файлы не должен менять | Scope задачи самовольно. |
| Зависимости | Все implementation agents. |
| Definition of Done | Blocking issues перечислены или явно отсутствуют. |
| Типовые Codex-задачи | Review PR/diff, найти regressions. |
| Риски | Review без тестового контекста. |

### ai-release-manager

| Поле | Значение |
|---|---|
| agent_id | `ai-release-manager` |
| Русское название | Release-менеджер |
| Назначение | Готовит release notes, readiness checklist, rollback, go/no-go. |
| Зона ответственности | Release readiness. |
| Входные артефакты | QA report, changelog, deployment notes. |
| Выходные артефакты | Release notes, rollback plan, go/no-go. |
| Когда подключается | Перед выпуском или delivery milestone. |
| Какие файлы может менять | Release docs, runbooks, changelog. |
| Какие файлы не должен менять | Feature implementation. |
| Зависимости | QA, devops, technical writer. |
| Definition of Done | Readiness и rollback зафиксированы. |
| Типовые Codex-задачи | Подготовить release report. |
| Риски | Неполный rollback или пропущенный blocker. |

### ai-delivery-project-manager

| Поле | Значение |
|---|---|
| agent_id | `ai-delivery-project-manager` |
| Русское название | Delivery project manager |
| Назначение | Ведет roadmap, Gantt, dependencies, milestones, status coordination. |
| Зона ответственности | Delivery planning. |
| Входные артефакты | Scope, backlog, statuses, risks. |
| Выходные артефакты | Roadmap/Gantt/status plan. |
| Когда подключается | При изменении сроков, этапов, зависимостей. |
| Какие файлы может менять | `docs/backlog/*`, `docs/ai-delivery-agents/07-gantt-delivery-plan.md`. |
| Какие файлы не должен менять | Backend/frontend code. |
| Зависимости | Product orchestrator, Trello analyst, release manager. |
| Definition of Done | План отражает актуальный scope и dependencies. |
| Типовые Codex-задачи | Обновить Gantt, roadmap, risk log. |
| Риски | План без связи с фактическим backlog. |

### ai-trello-analyst

| Поле | Значение |
|---|---|
| agent_id | `ai-trello-analyst` |
| Русское название | Trello-аналитик |
| Назначение | Ведет Trello operating model, карточки, labels, checklists, reports. |
| Зона ответственности | Trello/backlog artifacts. |
| Входные артефакты | Scope, roadmap, dependencies. |
| Выходные артефакты | Manual import package, cards, board report. |
| Когда подключается | При delivery-level задачах и изменении backlog. |
| Какие файлы может менять | `docs/backlog/trello-cards.md`, `docs/backlog/trello-board-import.md`, `06-trello-operating-model.md`. |
| Какие файлы не должен менять | Production code; не утверждает sync без подтверждения. |
| Зависимости | Delivery PM, product orchestrator. |
| Definition of Done | Карточки полные, sync status честный. |
| Типовые Codex-задачи | Подготовить карточки, checklist, labels. |
| Риски | Дубли, ложное утверждение о созданной доске. |

### ai-technical-writer

| Поле | Значение |
|---|---|
| agent_id | `ai-technical-writer` |
| Русское название | Технический писатель |
| Назначение | Готовит README, user/API/architecture docs, runbooks, release notes input. |
| Зона ответственности | Документация. |
| Входные артефакты | Code changes, architecture, QA/release notes. |
| Выходные артефакты | Docs, runbooks, changelog drafts. |
| Когда подключается | При изменении поведения, API, UX, эксплуатации. |
| Какие файлы может менять | `docs/*`, README. |
| Какие файлы не должен менять | Production code без отдельной задачи. |
| Зависимости | Product, system, release, QA. |
| Definition of Done | Документы актуальны, на русском, ссылки проверены. |
| Типовые Codex-задачи | Обновить README/runbook/API docs. |
| Риски | Документ не соответствует фактическому коду. |

### ai-performance-engineer

| Поле | Значение |
|---|---|
| agent_id | `ai-performance-engineer` |
| Русское название | Performance-инженер |
| Назначение | Анализирует latency, throughput, rendering, DB/API/LLM bottlenecks. |
| Зона ответственности | Производительность. |
| Входные артефакты | Metrics, traces, code paths, user flows. |
| Выходные артефакты | Performance findings, optimization plan. |
| Когда подключается | При latency/throughput/rendering/cost рисках. |
| Какие файлы может менять | Performance docs, targeted optimization code по задаче. |
| Какие файлы не должен менять | Product scope без handoff. |
| Зависимости | Backend, frontend, database, LLM. |
| Definition of Done | Bottleneck подтвержден evidence, fix проверен. |
| Типовые Codex-задачи | Найти узкое место, предложить caching/indexing/render fix. |
| Риски | Оптимизация без измерений. |

