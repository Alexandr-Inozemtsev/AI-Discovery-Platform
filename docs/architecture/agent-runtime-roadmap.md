# Roadmap Agent Runtime

Дата: 2026-05-17

Статус: draft

## Цель

Постепенно превратить текущий `AgentOrchestrator` и runtime-типы в управляемый `Agent Runtime`, не переписывая production-код на внешний framework и не ломая существующие React/FastAPI сценарии.

## Текущее состояние

Уже есть:

- `AgentOrchestrator` с mapping `artifact_type -> agent`;
- доменные agents для discovery stages;
- `BaseAgent.run()` для обратной совместимости;
- `BaseAgent.run_with_result()` с `AgentResult`;
- `AgentContext`;
- LLM provider boundary через `BaseLLMClient`;
- специализированный `ContextIngestionAgent.analyze()` с `source_trace`, `coverage`, `readiness`, `problem_handoff`;
- storage discovery artifacts через `DiscoveryArtifact`;
- DOCX export.

Ограничения:

- runtime policy распределена между agents и API endpoints;
- trace metadata пока неполная;
- retrieval boundary отсутствует;
- retries, rollback и human-in-the-loop gates не оформлены как единый runtime contract;
- LangGraph/LlamaIndex/Haystack еще не должны подключаться.

## Целевые capabilities

| Capability | Назначение | Приоритет |
|---|---|---:|
| Agent registry | Явный registry agents и supported artifact types | P0 |
| Unified run contract | Все agents возвращают `AgentResult` или специализированный typed result | P0 |
| Trace metadata | `trace_id`, `run_id`, source versions, prompt version, LLM metadata | P0 |
| Error/fallback policy | Единая классификация errors, warnings, fallback | P0 |
| Readiness gates | Управляемые переходы между stages | P1 |
| SimpleRetriever | Retrieval без внешних RAG dependencies | P1 |
| Audit trail | История AI runs и source inputs | P1 |
| Adapter boundary | LlamaIndex/Haystack/LangGraph только за interfaces | P2 |
| Workflow adapter | Optional LangGraph pilot | P3 |

## Фаза 0. Документы и границы

Выход:

- ADR-002;
- target architecture;
- `SimpleRetriever` contract;
- runtime roadmap.

Quality gate:

- документы на русском языке;
- production-код не изменен;
- все решения совместимы с ADR-001.

## Фаза 1. Runtime contract hardening

Цель: сделать текущий runtime проверяемым без изменения поведения agents.

Работы:

- описать internal interface `AgentRuntime.run(context) -> AgentResult`;
- оставить `run()` для обратной совместимости;
- стандартизировать `AgentResult.metadata`;
- добавить generation metadata: provider, model, timeout, temperature;
- добавить `trace_id` и `run_id`;
- передавать версии входных артефактов;
- описать controlled runtime errors.

Definition of Done:

- все новые runtime fields необязательны для старого UI;
- существующие endpoints продолжают возвращать текущие response models;
- tests подтверждают fallback behavior.

## Фаза 2. Registry и policies

Цель: отделить выбор agent от endpoint logic.

Работы:

- оформить registry с supported artifact types;
- явно задать unsupported stages;
- определить policy для missing context, missing LLM, LLM timeout, empty response;
- разделить user-facing errors и diagnostic errors;
- добавить prompt version в metadata.

Definition of Done:

- endpoint не знает деталей конкретного agent, кроме artifact type и сценария;
- unsupported artifact возвращает controlled error;
- metadata не содержит secrets.

## Фаза 3. SimpleRetriever integration

Цель: дать agents evidence-aware context без новых RAG dependencies.

Работы:

- реализовать `Retriever` interface;
- реализовать `SimpleRetriever`;
- подключить retrieval к runtime через feature flag;
- первым consumer сделать `ProblemAgent`;
- не менять public frontend contract;
- сохранять retrieved chunks в `AgentResult.source_trace` или metadata.

Definition of Done:

- retrieval отключаем;
- metadata-only sources не считаются evidence;
- top-k и max_chars работают;
- fallback без retrieval работает;
- source trace не теряется.

## Фаза 4. Runtime observability и audit

Цель: сделать AI-запуски объяснимыми и проверяемыми.

Работы:

- определить, где хранить AI run trace: structured metadata или отдельная таблица;
- фиксировать входные artifact versions;
- фиксировать retrieval summary;
- фиксировать warnings/errors;
- не хранить API keys и credentials;
- определить redaction policy для prompts.

Definition of Done:

- можно объяснить, какие источники повлияли на артефакт;
- можно сравнить версии AI runs;
- diagnostics доступны backend/QA без раскрытия секретов.

## Фаза 5. Adapter boundary для LlamaIndex/Haystack

Цель: подготовить mature RAG adapters без lock-in.

Работы:

- определить `RagAdapter` как реализацию `Retriever`;
- провести license/dependency gate;
- сделать PoC в отдельной ветке;
- сравнить с `SimpleRetriever`;
- не менять UI и public API;
- добавить feature flag.

Definition of Done:

- adapter можно отключить;
- internal result contract одинаковый;
- dependency review завершен;
- есть измеримые критерии качества.

## Фаза 6. LangGraph pilot

Цель: проверить workflow orchestration только после runtime hardening.

Scope pilot:

- `Context -> readiness gate -> Problem`;
- clarification questions;
- user answer;
- apply patch;
- rollback к предыдущей версии problem artifact.

Не входит:

- перенос всех stages;
- замена `AgentOrchestrator`;
- изменение frontend на graph editor;
- подключение managed LangChain/LangSmith services без отдельного решения.

Definition of Done:

- pilot отключаем;
- state persistence понятен;
- rollback проверен;
- trace id проходит через graph;
- качество не хуже текущего flow.

## Фаза 7. Production governance

Цель: подготовить runtime к корпоративной поставке.

Работы:

- dependency allowlist;
- SBOM/transitive license review;
- security review LLM/retrieval data flow;
- QA regression на adapter-off режиме;
- release notes и rollback runbook.

Definition of Done:

- есть go/no-go checklist;
- есть rollback plan;
- есть ownership по runtime, retriever, adapters и LLM providers.

## Риски roadmap

| Риск | Митигация |
|---|---|
| Runtime станет слишком абстрактным | Делать фазы от текущих endpoints и agents, не вводить framework ради framework |
| SimpleRetriever даст слабое качество | Использовать как baseline и быстро сравнить с adapters после стабилизации contract |
| Metadata начнет содержать приватные данные | Ввести redaction и запрет secrets в logs/metadata |
| Adapters начнут диктовать API | Держать framework-specific поля внутри adapter diagnostics |
| LangGraph подключат слишком рано | Quality gate: stable runtime, trace, rollback, feature flag |

## Handoff

- Backend developer: реализовать runtime phases P0/P1 после согласования.
- LLM/RAG engineer: определить retrieval scoring и evaluation dataset.
- Security reviewer: проверить secrets, prompts, outbound data и dependencies.
- QA engineer: подготовить regression cases для fallback, trace и adapter-off режима.
- DevOps engineer: подготовить feature flags и rollback runbook.

