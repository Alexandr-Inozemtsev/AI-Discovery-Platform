# Экспертный review архитектуры Product AI Agents

Дата: 2026-05-22  
Статус: архитектурный review, production-код не менялся  
Область: Product AI Agents внутри backend AI Discovery Platform  
Важно: Global Codex Delivery Agents использованы только как роли review. Они не являются backend-сервисами продукта.

## Executive summary

Текущая модель Product AI Agents полезна как MVP-обвязка Discovery-этапов, но пока не является зрелой multi-agent architecture в строгом смысле. В backend есть общий `BaseAgent`, `AgentResult`, `AgentContext` и `AgentOrchestrator`, однако большинство stage agents сейчас являются тонкими wrappers вокруг stage-specific prompt и deterministic fallback.

Честный вывод:

- `ContextIngestionAgent` нужно оставить отдельным компонентом: у него отдельный JSON-контракт, нормализация источников, `source_trace`, `coverage`, `readiness` и `problem_handoff`.
- `CriticAgent` целесообразно оставить отдельным проверочным компонентом, но усилить контракт проверки.
- `ProblemAgent`, `GoalAgent`, `BusinessEffectAgent`, `UseCaseAgent` сейчас больше похожи на prompt templates для этапов, чем на самостоятельные архитектурные агенты.
- `RequirementsAgent` уже переиспользуется для `FUNCTIONAL_REQUIREMENTS`, `NON_FUNCTIONAL_REQUIREMENTS` и `FINAL_BT`, что фактически подтверждает движение к processor/template модели.
- Один универсальный `DiscoveryAgent` слишком груб для контроля качества, evidence и тестирования.
- Лучшая целевая модель: гибридная архитектура `Agent Runtime + ContextIngestionAgent + StageDraftProcessor + RequirementsProcessor + CriticAgent`.

Рекомендация: не делать срочный refactor в рамках текущего MVP, но зафиксировать целевое упрощение через ADR и backlog. При корпоративном внедрении описывать это как единый Agent Runtime с режимами генерации Discovery-артефактов, а не как набор независимых AI-сервисов.

## Scope review

Проверены фактические backend-компоненты:

- `discovery-ai-agent/backend/app/agents/orchestrator.py`;
- `discovery-ai-agent/backend/app/agents/base_agent.py`;
- `discovery-ai-agent/backend/app/agents/runtime/agent_result.py`;
- `discovery-ai-agent/backend/app/agents/runtime/agent_context.py`;
- `discovery-ai-agent/backend/app/agents/context_ingestion_agent.py`;
- `discovery-ai-agent/backend/app/agents/problem_agent.py`;
- `discovery-ai-agent/backend/app/agents/goal_agent.py`;
- `discovery-ai-agent/backend/app/agents/business_effect_agent.py`;
- `discovery-ai-agent/backend/app/agents/use_case_agent.py`;
- `discovery-ai-agent/backend/app/agents/requirements_agent.py`;
- `discovery-ai-agent/backend/app/agents/critic_agent.py`;
- `discovery-ai-agent/backend/app/api/discovery.py`;
- `discovery-ai-agent/backend/app/llm/*`;
- `docs/architecture/agent-runtime-contract.md`;
- `docs/architecture/simple-retriever-contract.md`;
- `docs/architecture/ADR-001-agent-and-rag-framework-selection.md`;
- `docs/llm-rag/rag-and-retrieval-target-design.md`;
- `docs/system/tz-ai-discovery-platform-target.md`;
- `docs/backlog/backend-backlog.md`;
- `docs/backlog/trello-cards.md`;
- `docs/ai-delivery-agents/07-gantt-delivery-plan.md`.

Не менялись:

- backend runtime код;
- Product AI Agents;
- frontend;
- модели БД;
- миграции;
- LLM settings;
- зависимости.

## Current state

### Agent registry

Фактический `AgentOrchestrator` регистрирует:

| Artifact type | Текущий класс | Наблюдение |
|---|---|---|
| `CONTEXT` | `ContextIngestionAgent` | Специализированный context ingestion workflow. |
| `PROBLEM` | `ProblemAgent` | Тонкий prompt/fallback wrapper для общего `/generate`. |
| `GOAL` | `GoalAgent` | Тонкий prompt/fallback wrapper для общего `/generate`; есть отдельный JSON-flow `/goal/generate` в API. |
| `BUSINESS_EFFECT` | `BusinessEffectAgent` | Тонкий prompt/fallback wrapper. |
| `USE_CASES` | `UseCaseAgent` | Тонкий prompt/fallback wrapper. |
| `FUNCTIONAL_REQUIREMENTS` | `RequirementsAgent` | Prompt/fallback wrapper для требований. |
| `NON_FUNCTIONAL_REQUIREMENTS` | `RequirementsAgent` | Уже переиспользует тот же класс. |
| `FINAL_BT` | `RequirementsAgent` | Уже переиспользует тот же класс. |

`CriticAgent` не зарегистрирован в `AgentOrchestrator`, но используется напрямую endpoint-ом `/api/projects/{project_id}/validate`.

### Runtime contract

`BaseAgent` задаёт общий контракт:

- `build_prompt`;
- `_deterministic_result`;
- `run_with_result`;
- fallback при ошибке LLM или пустом ответе;
- `run` как backward-compatible wrapper.

`AgentResult` уже содержит поля `ok`, `content`, `structured_content`, `raw_llm_response`, `used_fallback`, `warnings`, `errors`, `source_trace`, `metadata`, но downstream generation пока не использует их единообразно.

### API generation flows

В API сейчас есть несколько конкурирующих генерационных потоков:

- generic `/api/projects/{project_id}/generate/{artifact_type}` через `AgentOrchestrator`;
- специализированный `/problem/generate` с JSON prompt, `problem_handoff`, `source_trace`, versioning и structured content;
- специализированный `/goal/generate` с JSON prompt и своим response shape;
- `/stage/{artifact_type}/questions`, `/ask`, `/apply-patch` как stage assistance layer;
- `/validate` через `CriticAgent`.

Это не ошибка для MVP, но архитектурно это означает, что “агенты” пока не являются единым автономным слоем. Часть логики живёт в классах агентов, часть прямо в API.

## Agent-by-agent assessment

| Product AI Agent | Responsibility | Input contract | Output contract | Evidence / retrieval | Tests | Вывод |
|---|---|---|---|---|---|---|
| `ContextIngestionAgent` | Извлечь и нормализовать знания из ручного контекста, файлов и ссылок. | Payload `context_input`, `documents`, `links`, previous context. | Структурированный JSON: `extracted_knowledge`, `source_trace`, `coverage`, `readiness`, `problem_handoff`. | Использует chunks, source metadata, metadata-only detection. Retrieval как отдельный `SimpleRetriever` ещё не реализован. | Есть отдельные tests context ingestion. | Настоящий архитектурный компонент. Оставить отдельным. |
| `ProblemAgent` | Сгенерировать problem artifact для generic flow. | `project`, `existing_artifacts`. | Markdown/text через `content`; отдельный structured flow живёт в API `/problem/generate`. | Generic class почти не работает с evidence; specialized API использует `problem_handoff` и `source_trace`. | Есть только smoke через base runtime; специализированный flow частично покрыт context tests. | Текущий класс скорее prompt template. Целево перенести в `StageDraftProcessor` или problem stage template. |
| `GoalAgent` | Сгенерировать SMART goal для generic flow. | `project`, `existing_artifacts`. | Markdown/text; отдельный JSON-flow живёт в API `/goal/generate`. | Generic class не использует retrieval; specialized API учитывает `CONTEXT` и `PROBLEM`, но evidence не унифицирован. | Smoke test через base runtime. | Prompt wrapper. Целево stage template внутри processor. |
| `BusinessEffectAgent` | Сгенерировать бизнес-эффект. | `project`, `existing_artifacts`. | Markdown/text. | Evidence и structured contract отсутствуют. | Отдельных tests не найдено. | Prompt wrapper. Целево stage template. |
| `UseCaseAgent` | Сгенерировать use cases. | `project`, `existing_artifacts`. | Markdown/text. | Evidence и structured contract отсутствуют. | Отдельных tests не найдено. | Prompt wrapper. Целево stage template или отдельный processor только после появления строгого use case schema. |
| `RequirementsAgent` | Сгенерировать требования, NFR и Final BT в generic flow. | `project`, `existing_artifacts`. | Markdown/text. | Evidence и requirement-level trace отсутствуют. | Отдельных tests не найдено. | Уже агрегирует несколько artifact types. Целево нужен `RequirementsProcessor` со строгим schema/evidence, а не отдельные классы на каждый раздел. |
| `CriticAgent` | Проверить качество артефактов. | `project`, `existing_artifacts`. | Markdown validation report. | Не использует structured evidence; проверяет filled artifacts поверх текстов. | Отдельных tests не найдено. | Стоит оставить отдельным validator/critic component, но усилить contract и checks. |

## Architecture assessment

Текущая модель оправдана как простой MVP, потому что она явно отражает Discovery workflow и даёт понятную точку расширения. Но как корпоративная архитектура она избыточна в названиях и недостаточно строга в контрактах.

Ключевая проблема: классы `ProblemAgent`, `GoalAgent`, `BusinessEffectAgent`, `UseCaseAgent` не имеют уникального runtime lifecycle, отдельных tools, собственного storage contract, собственного retrieval policy или отдельной security boundary. Они отличаются главным образом prompt и fallback-текстом. Это лучше моделировать как stage processors или versioned prompt templates внутри единого Agent Runtime.

## Product assessment

Для пользователя и руководства ценность находится не в количестве “агентов”, а в управляемом Discovery-процессе:

- Контекст собран и проверен.
- Проблема сформулирована.
- Цель и эффект связаны с проблемой.
- Use cases и требования трассируются к источникам.
- Финальный БТ можно экспортировать.

В UI лучше показывать этапы Discovery, readiness, evidence и next actions, а не список внутренних backend-агентов. Слишком много “агентов” может создать ожидание автономной AI-команды и повысить недоверие со стороны ИБ и архитектуры.

Продуктовая рекомендация:

- показывать пользователю `Контекст`, `Проблема`, `Цель`, `Бизнес-эффект`, `Use Cases`, `Требования`, `Проверка`, `Экспорт`;
- не продавать каждый stage class как отдельного AI-агента;
- для руководства использовать формулировку “единый AI Runtime с управляемыми режимами генерации Discovery-артефактов”.

## System contract assessment

Минимальный целевой контракт для stage processors должен быть единым.

```python
class StageProcessorRequest:
    project_id: str
    artifact_type: str
    stage_type: str
    project_snapshot: dict
    input_artifacts: dict
    context_readiness: dict
    retrieval_result: dict | None
    user_answers: list[dict]
    prompt_version: str
    trace_id: str
```

```python
class StageProcessorResult:
    ok: bool
    artifact_type: str
    content: str
    structured_content: dict
    evidence: list[dict]
    assumptions: list[str]
    open_questions: list[str]
    warnings: list[str]
    errors: list[str]
    used_fallback: bool
    source_trace: list[dict]
    metadata: dict
```

Gaps текущей модели:

- нет единого JSON-контракта для всех downstream stages;
- `source_trace` есть для context/problem, но не унифицирован для Goal/BusinessEffect/UseCases/Requirements;
- нет prompt versioning;
- нет единого `AgentRun`/audit trail;
- нет stage-specific validation;
- generic и specialized generation имеют разные response shapes;
- retrieval evidence ещё target-state, а не фактическая реализация.

## Backend feasibility assessment

Текущие классы поддерживать недорого, но цена растёт при добавлении evidence, prompt versioning, tests и corporate controls. Если продолжить множить классы по каждому stage, появится дублирование:

- одинаковый LLM call lifecycle;
- одинаковая сборка контекста;
- одинаковый fallback;
- одинаковая обработка JSON parse errors;
- одинаковый audit/trace metadata;
- одинаковые QA checks.

Технически возможны четыре migration option:

| Option | Описание | Сложность | Риск |
|---|---|---:|---|
| Без изменений | Оставить классы, только улучшать contracts вокруг них. | Низкая | Накопление дублирования. |
| Shared prompt builder | Вынести сборку prompt/context/evidence в общий helper, классы оставить. | Низкая/средняя | Частично скрывает проблему, но не упрощает registry. |
| `StageDraftProcessor` | Один processor с stage policy и versioned templates для Problem/Goal/BusinessEffect/UseCases. | Средняя | Нужны contract tests и compatibility wrapper. |
| Полный refactor runtime | Сразу заменить генерацию на новый runtime/service layer. | Высокая | Риск сломать MVP endpoints и frontend. |

Рекомендация backend: выбрать мягкую миграцию через `StageDraftProcessor` после BE-02-01/BE-02-02, не ломая текущие endpoint paths.

## LLM/RAG assessment

Один большой prompt для всего Discovery хуже нескольких stage-specific prompts: он увеличивает token budget, смешивает цели этапов и усложняет проверку hallucination. Но отдельный Python class на каждый stage тоже не обязателен.

Лучше:

- единый runtime lifecycle;
- stage-specific prompt templates;
- prompt version per stage;
- stage policy: какие входные артефакты обязательны, какой retrieval query использовать, какой output schema ожидать;
- evidence requirement для Problem, Goal и Requirements;
- fallback policy, которая явно фиксирует assumptions и open questions.

Context/RAG должен передаваться так:

- Context stage формирует `source_trace`, `coverage`, `readiness`, `problem_handoff`;
- `SimpleRetriever` возвращает top-k chunks и chunk-level evidence;
- Problem получает `problem_handoff` и chunks по текущим болям/процессам/ограничениям;
- Goal получает Problem + evidence и chunks по KPI/результатам/ограничениям;
- Requirements получает Problem, Goal, Use Cases и chunks по системам, ролям, бизнес-правилам, интеграциям.

## Security and corporate deployment assessment

В корпоративной среде большое количество “агентов” может создать лишний approval overhead, если их описывать как отдельные автономные AI-сервисы. Это не соответствует фактической реализации.

Рекомендуемая формулировка для корпоративной архитектуры:

> AI Discovery Platform использует единый backend Agent Runtime. Runtime выполняет несколько управляемых режимов генерации Discovery-артефактов через общий LLM Gateway, общий audit, единый prompt registry и единые data controls.

Security recommendations:

- не заводить отдельные secrets на каждого Product AI Agent;
- не заводить отдельные корпоративные подключения на каждого stage;
- использовать единый LLM Gateway;
- использовать единый prompt registry с версиями и approval;
- логировать agent runs через единый audit/telemetry слой;
- отделять trusted system prompt от untrusted source chunks;
- применять redaction и data minimization до LLM call;
- фиксировать prompt injection policy для документов и ссылок;
- не сохранять raw provider payloads и полные prompts без отдельной data policy.

## QA assessment

QA-cost текущей модели растёт линейно с числом классов, но качество не растёт, если классы различаются только prompt. Для корпоративного пилота нужны не “tests per class”, а “tests per stage contract”.

Рекомендуемая test strategy:

- unit tests для `ContextIngestionAgent`;
- unit tests для `StageDraftProcessor` stage policy;
- contract tests для `StageProcessorRequest`/`StageProcessorResult`;
- prompt regression tests для Problem, Goal, BusinessEffect, UseCases, Requirements;
- golden examples на 10-20 кейсов для Problem/Goal/Requirements;
- context-empty tests;
- metadata-only source tests;
- source_trace/evidence tests;
- LLM fallback tests;
- hallucination checks: unsupported claim rate;
- QA gate before corporate pilot.

## Мнение каждого Global Codex Delivery Agent

### ai-solution-architect

Текущая модель не должна называться полноценной multi-agent architecture. Это ранний internal runtime с registry и набором stage prompt wrappers. Целевая модель должна быть гибридной: отдельный context ingestion, единый stage processor для draft stages, специализированный requirements processor и отдельный critic.

### ai-product-orchestrator

Для пользователя важны этапы Discovery и качество результата, а не количество внутренних агентов. В презентациях и UI следует говорить о “сквозном Discovery workflow” и “AI-помощи по этапам”, а не о семи независимых агентах.

### ai-system-analyst

Главный gap - отсутствие единого stage result contract и распространения `source_trace` на downstream artifacts. Нужны `StageProcessorRequest`, `StageProcessorResult`, `evidence`, `assumptions`, `open_questions`, `warnings`.

### ai-backend-developer

Поддерживать текущие классы можно, но при развитии они начнут дублировать prompt assembly, LLM call lifecycle, error mapping, parsing, fallback и telemetry. Рекомендуется постепенная миграция без изменения API paths.

### ai-llm-rag-engineer

Stage-specific prompts лучше одного универсального prompt, но их нужно хранить и версионировать как templates/policies. Retrieval должен быть централизованным и выдавать evidence, а не расползаться по каждому agent class.

### ai-security-reviewer

В corporate review нельзя создавать впечатление, что каждый Product AI Agent имеет отдельные secrets, сетевые подключения и security boundary. Нужны единый LLM Gateway, единый audit, prompt registry, data minimization и prompt injection controls.

### ai-qa-engineer

Множество классов без строгих contract tests увеличивает regression scope. QA должна тестировать stage contracts, golden datasets, fallback, evidence и hallucination rate.

### ai-code-reviewer

Рекомендация реалистична, потому что не требует немедленного изменения runtime-кода. Риск был бы выше, если бы review предлагал сразу переписать `AgentOrchestrator` и endpoints.

### ai-delivery-project-manager

Решение создаёт roadmap impact: нужен backlog item на утверждение ADR и отдельная фаза миграции stage processors. Existing Gantt нужно расширить как draft, не меняя текущие committed dates.

### ai-trello-analyst

Так как есть target-architecture change, нужен manual Trello card draft. Trello API не использовался, поэтому нельзя утверждать, что доска синхронизирована.

### ai-technical-writer

Документы должны явно различать Product AI Agents и Global Codex Delivery Agents. Для руководства формулировка должна быть простой: единый Agent Runtime, управляемые режимы генерации, traceability, security controls.

## Аргументы за текущую модель

- Явно отражает Discovery stages в коде.
- Проста для MVP и локальной отладки.
- Позволяет быстро добавить новый stage через новый class.
- Не требует внешних agent frameworks.
- `BaseAgent` уже даёт единый fallback lifecycle.
- `ContextIngestionAgent` уже имеет зрелый специализированный contract.

## Аргументы против текущей модели

- Большинство классов отличаются только prompt/fallback.
- Нет единого structured output contract для downstream stages.
- `source_trace` и evidence не распространены на все артефакты.
- Generic и specialized generation расходятся.
- Требования, NFR и Final BT уже используют один `RequirementsAgent`, что противоречит идее “отдельный агент на каждый stage”.
- Corporate approval может раздуться, если описывать каждый stage wrapper как отдельного агента.
- QA regression scope растёт быстрее, чем зрелость архитектуры.

## Сравнение архитектурных альтернатив

| Вариант | Суть | Плюсы | Минусы | Corporate fit | Рекомендация |
|---|---|---|---|---|---|
| A. Оставить текущую модель | Отдельные Product AI Agent classes по этапам. | Минимальный риск для MVP; понятная привязка к stages. | Дублирование, слабые contracts, overhead согласования. | Средний: нужно объяснять как внутренние handlers, а не отдельные AI-сервисы. | Допустимо временно, не как target. |
| B. Agent Runtime + stage processors | Единый runtime, stage processors/templates для Problem/Goal/BusinessEffect/UseCases/Requirements. | Строгие contracts, меньше дублирования, лучше QA/security. | Требует migration plan и compatibility layer. | Высокий. | Хорошая target base. |
| C. Один универсальный DiscoveryAgent | Один class получает `stage_type` и генерирует всё. | Максимально просто в registry. | Слабая управляемость, выше hallucination risk, хуже stage-specific tests. | Средний/низкий. | Не рекомендовано для MVP и corporate pilot. |
| D. Гибрид | Отдельные `ContextIngestionAgent` и `CriticAgent`; stage templates/processors для draft stages; отдельный requirements processor. | Лучший баланс управляемости, QA и corporate explainability. | Требует аккуратной миграции и prompt governance. | Высокий. | Рекомендовано. |

## Итоговая рекомендация

Принять вариант D: гибридная целевая модель.

Целевой состав:

- `AgentRuntime` - единый lifecycle, trace, fallback, error, audit, LLM Gateway;
- `ContextIngestionAgent` - отдельный specialized ingestion component;
- `StageDraftProcessor` - единый processor для `PROBLEM`, `GOAL`, `BUSINESS_EFFECT`, `USE_CASES` через stage policies и versioned prompt templates;
- `RequirementsProcessor` - специализированный processor для `FUNCTIONAL_REQUIREMENTS`, `NON_FUNCTIONAL_REQUIREMENTS`, `FINAL_BT`, потому что требования требуют строгой структуры, IDs, acceptance criteria, dependencies и evidence;
- `CriticAgent` или `ValidationProcessor` - отдельный проверочный компонент;
- `SimpleRetriever` - отдельный retrieval boundary, а не часть каждого agent class;
- `PromptRegistry` - версия, владелец, статус approval, language, output schema, evidence policy.

Не делать:

- не переписывать production-код до утверждения ADR;
- не удалять существующие classes одномоментно;
- не подключать Global Codex Delivery Agents как backend services;
- не представлять stage wrappers как отдельные корпоративные AI-сервисы.

## Migration plan

### Phase 0. Decision only

- Создать review, target architecture и ADR.
- Создать backlog item и manual Trello card draft.
- Обновить Gantt как draft impact.
- Production-код не менять.

### Phase 1. Contract alignment

- Закрыть BE-02-01: единый `AgentResult` contract для всех генераторов.
- Зафиксировать `StageProcessorRequest` и `StageProcessorResult` в документации и tests.
- Не менять endpoint paths.

### Phase 2. Processor introduction

- Добавить `StageDraftProcessor` behind compatibility registry.
- Перенести prompt templates для Problem/Goal/BusinessEffect/UseCases.
- Сохранить thin wrappers временно, если они нужны для backward compatibility.

### Phase 3. Evidence and retrieval

- Подключить `SimpleRetriever` к Problem/Goal/Requirements.
- Сохранять evidence/source_trace в structured content.
- Добавить prompt regression и golden datasets.

### Phase 4. Cleanup

- Удалять или депрецировать stage wrapper classes только после tests, frontend smoke и release note.
- Обновить docs/API/backlog.

## Decision record

Решение review: текущую модель оставить в runtime до завершения MVP-hardening, но целевую архитектуру упростить до гибридной модели. Это не срочный production refactor, а архитектурное направление для BE-02 и RAG/evidence задач.

Связанные документы:

- [Целевая архитектура Product AI Agents](product-ai-agents-target-architecture.md);
- [ADR-003 Product AI Agents target architecture](ADR-003-product-ai-agents-target-architecture.md);
- [Backlog по архитектурному решению Product AI Agents](../backlog/product-ai-agents-architecture-decision-backlog.md);
- [Agent Runtime Contract](agent-runtime-contract.md);
- [SimpleRetriever Contract](simple-retriever-contract.md);
- [RAG/retrieval target design](../llm-rag/rag-and-retrieval-target-design.md);
- [ТЗ целевого состояния](../system/tz-ai-discovery-platform-target.md).

## Open questions

- Достаточно ли `RequirementsProcessor` для `FINAL_BT` или нужен отдельный `DocumentAssemblyProcessor` для финального БТ.
- Где хранить prompt templates: Python constants, DB, markdown registry или отдельный config package.
- Нужно ли versioned API response для generation endpoints или достаточно backward-compatible fields.
- Какие artifact types входят в MVP migration scope, а какие остаются в MMP.
- Нужен финальный approval `ADR-003` владельцем архитектуры перед началом BE-02-05/BE-02-06.
