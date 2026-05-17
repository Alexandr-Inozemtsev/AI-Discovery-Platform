# ADR-002: Эволюция AI Discovery Platform через собственный Agent Runtime и внутренний retrieval boundary

Дата: 2026-05-17

Статус: proposed

## Контекст

AI Discovery Platform уже имеет собственный React frontend, FastAPI backend, SQLAlchemy-модели discovery-проектов и артефактов, настраиваемые LLM providers, `AgentOrchestrator`, доменных discovery-агентов и runtime-типы `AgentContext` / `AgentResult`.

Текущий контур поддерживает загрузку контекстных источников, извлечение текста, chunks, `source_trace`, `coverage`, `readiness`, `problem_handoff`, генерацию discovery-артефактов и DOCX export. Это означает, что платформа уже содержит доменную модель AI Discovery и не должна заменяться generic low-code/RAG платформой.

ADR-001 зафиксировал общий выбор: сохранить React/FastAPI, не строить foundation на Dify/Flowise/RAGFlow, сначала стабилизировать собственный runtime, затем добавить `SimpleRetriever`, затем optional adapters для LlamaIndex/Haystack и только после этого рассматривать LangGraph как workflow layer.

## Проблема

Нужно развить платформу так, чтобы:

- не переписать продукт на внешний framework;
- не потерять контроль над discovery stages, artifacts, readiness gates и source trace;
- подготовить основу для RAG без преждевременного vendor/framework lock-in;
- сохранить возможность корпоративной поставки с понятными зависимостями, лицензиями и отключаемыми интеграциями;
- дать backend/frontend разработке понятные архитектурные границы.

Основной риск текущего состояния: `AgentOrchestrator`, специализированные endpoints и agents уже работают, но runtime boundary пока недостаточно явно отделяет orchestration, retrieval, LLM calls, tracing, retries, audit metadata и rollback.

## Варианты

### Вариант 1. Продолжать развивать текущий код точечно

Плюсы:

- минимальная скорость входа;
- нет новых зависимостей;
- низкий лицензионный риск.

Минусы:

- растет связность endpoints, agents и LLM-вызовов;
- retrieval, tracing и readiness могут расходиться по разным реализациям;
- сложнее подключить LangGraph/LlamaIndex/Haystack позже без переписывания.

### Вариант 2. Сразу подключить LangGraph как orchestration foundation

Плюсы:

- явные workflow states и graph execution;
- потенциально удобен для human-in-the-loop.

Минусы:

- преждевременно меняет runtime-модель до стабилизации собственных contracts;
- увеличивает зависимость от внешней экосистемы;
- может скрыть архитектурные долги текущих agents под graph layer.

### Вариант 3. Сразу подключить LlamaIndex или Haystack для RAG

Плюсы:

- готовые retrievers, pipelines, connectors и индексы;
- быстрее проверить продвинутые RAG-сценарии.

Минусы:

- появляются transitive dependencies до фиксации внутреннего retrieval contract;
- framework может начать диктовать структуру chunks, metadata и source trace;
- сложнее обеспечить режим без внешнего RAG в корпоративном контуре.

### Вариант 4. Перейти на Dify, Flowise или RAGFlow как foundation

Плюсы:

- готовые UI/workflow/RAG возможности;
- быстрые демонстрационные сценарии.

Минусы:

- это платформы, а не узкие библиотеки;
- они конкурируют с собственной доменной моделью AI Discovery Platform;
- меняют boundaries продукта, delivery model, security surface и licensing profile;
- усложняют монетизацию и корпоративную поставку.

### Вариант 5. Сначала собственный Agent Runtime, затем SimpleRetriever, затем adapters

Плюсы:

- сохраняется текущая продуктовая архитектура;
- минимальный dependency risk на первом этапе;
- формируется стабильная adapter boundary;
- внешние frameworks можно подключать позже как replaceable adapters.

Минусы:

- требуется дисциплина контрактов и документации;
- часть capabilities придется реализовать минимально внутри проекта;
- эффект от внешних RAG/workflow framework появится позже.

## Выбранное решение

Выбран вариант 5: эволюция через собственный `Agent Runtime`, внутренний `SimpleRetriever` без новых внешних RAG-зависимостей и явную adapter boundary для будущих frameworks.

Решение:

1. Сохранить React frontend и FastAPI backend.
2. Сохранить доменных agents и текущий `AgentOrchestrator` как исходную точку.
3. Выделить целевой `Agent Runtime` вокруг `AgentContext`, `AgentResult`, runtime metadata, source trace, readiness gates, error policy и artifact versions.
4. Добавить `SimpleRetriever` как внутренний retrieval component поверх существующих extracted text/chunks/source metadata.
5. Зафиксировать `Retriever` / `RagAdapter` boundary до подключения LlamaIndex или Haystack.
6. Рассматривать LangGraph только после стабилизации runtime contract, как optional workflow adapter, а не как новое ядро.
7. Не использовать Dify, Flowise и RAGFlow как foundation продукта.

## Почему сначала SimpleRetriever

`SimpleRetriever` нужен первым, потому что текущая платформа уже имеет источники, chunks, `source_trace`, `readiness` и `problem_handoff`. Минимальный внутренний retriever может использовать эти данные без новых storage engines, vector databases и RAG frameworks.

Он закрывает ближайшие архитектурные задачи:

- единый контракт retrieval-запроса и retrieval-ответа;
- top-k chunks для agents;
- сохранение `source_trace` и evidence links;
- deterministic fallback без внешних сервисов;
- возможность полностью отключить retrieval;
- baseline для сравнения LlamaIndex/Haystack по quality, latency и explainability.

## Почему LlamaIndex/Haystack позже

LlamaIndex и Haystack полезны как adapters для более зрелых RAG pipelines, но их нельзя добавлять до внутреннего contract, потому что иначе framework начнет владеть моделью chunks, metadata, citations и storage.

Они рассматриваются позже, когда будут выполнены условия:

- есть стабильный `Retriever` interface;
- есть baseline на `SimpleRetriever`;
- понятны метрики качества retrieval;
- пройден license/dependency gate;
- определены storage, telemetry и data residency boundaries;
- adapter можно выключить без деградации базового продукта.

## Почему LangGraph после runtime

LangGraph решает orchestration/workflow graph, но не заменяет доменные agents, artifacts, readiness и source trace. Если подключить его до стабилизации runtime, он станет обходным способом управления состоянием вместо явного контракта платформы.

LangGraph допустим позже как pilot для ограниченного workflow `Context -> Problem`, когда уже есть:

- стабильный `AgentResult`;
- trace id propagation;
- state persistence boundary;
- rollback behavior;
- human-in-the-loop gates;
- policy для retries и errors;
- возможность отключить adapter и вернуться к текущему runtime.

## Почему Dify/Flowise/RAGFlow не foundation

Dify, Flowise и RAGFlow являются полноценными платформами или low-code/RAG products. Их использование как foundation означало бы замену существенной части AI Discovery Platform:

- UI/workspace/application model;
- workflow model;
- runtime model;
- secrets/tool/plugin model;
- deployment model;
- security and governance surface;
- часть commercial/licensing profile.

Их можно изучать как reference для UX, RAG quality или deployment ideas, но нельзя включать как основу продукта без отдельного ADR, юридической проверки и product strategy decision.

## Последствия

Положительные:

- сохраняется контроль над доменной архитектурой;
- снижается dependency и license risk;
- backend получает понятную границу `Agent Runtime -> Retriever -> LLM Provider`;
- frontend продолжает работать с discovery artifacts и не зависит от RAG framework;
- появляется основа для explainability через source trace и evidence.

Отрицательные:

- первые RAG-возможности будут проще, чем у mature frameworks;
- потребуется отдельная дисциплина контрактов и тестов;
- часть advanced features откладывается до adapter phases;
- понадобится архитектурный review перед каждой новой AI/RAG dependency.

## Риски

| Риск | Вероятность | Влияние | Митигация |
|---|---:|---:|---|
| `SimpleRetriever` окажется недостаточно качественным | Средняя | Среднее | Использовать как baseline, заранее держать adapter boundary для LlamaIndex/Haystack |
| Runtime останется набором ручных endpoints | Средняя | Высокое | Ввести roadmap runtime capabilities и quality gate перед LangGraph |
| Source trace разойдется между context ingestion и retrieval | Средняя | Высокое | Единый retrieval response contract с `source_trace` и `evidence` |
| Новые dependencies попадут в продукт без license review | Средняя | Высокое | License/dependency gate до изменения dependency manifests |
| Adapter начнет протекать в UI/API | Средняя | Среднее | UI/API работают с internal contracts, framework-specific поля остаются внутри adapter |
| Увеличится latency генерации | Средняя | Среднее | Top-k limits, chunk size limits, telemetry, fallback без retrieval |

## Phased implementation plan

### Фаза 0. Документирование решений

- Создать ADR-002.
- Создать целевую архитектуру.
- Создать контракт `SimpleRetriever`.
- Создать roadmap `Agent Runtime`.

### Фаза 1. Runtime hardening

- Зафиксировать `AgentRuntime`, `AgentContext`, `AgentResult`, `AgentError`, `AgentTrace`.
- Привести agents к единому runtime entrypoint без массового переписывания prompt logic.
- Добавить metadata: `trace_id`, `run_id`, `artifact_type`, `project_id`, `source_artifact_versions`, `prompt_version`, `llm_provider`, `llm_model`.
- Явно описать retry/error/fallback policy.

### Фаза 2. SimpleRetriever

- Реализовать internal `Retriever` interface.
- Использовать существующие `documents`, `links`, `extracted_text`, `chunks`, `source_trace`.
- Возвращать top-k chunks с score, reason, source metadata и trace.
- Подключить к `ContextIngestionAgent` и `ProblemAgent` через runtime/context, а не через UI.

### Фаза 3. Adapter boundary

- Ввести `RetrieverProvider` / `RagAdapter` abstraction.
- Добавить feature flag для adapter.
- Создать PoC LlamaIndex или Haystack в отдельной ветке.
- Сравнить качество, latency, explainability, dependency tree и deployment complexity.

### Фаза 4. Workflow pilot

- Пилотировать LangGraph только для `Context -> Problem`.
- Проверить state persistence, rollback, human approval и observability.
- Не переносить остальные stages до результата пилота.

### Фаза 5. Governance перед production

- Вести allowlist AI/RAG dependencies.
- Фиксировать SBOM/transitive license review.
- Документировать data flow в LLM, retriever, storage и telemetry.
- Подготовить security, QA и release handoff.

## Rollback strategy

- Каждая новая runtime/retrieval capability включается через feature flag или конфигурационную опцию.
- `SimpleRetriever` должен быть отключаемым: agents возвращаются к текущему поведению на основе context artifact.
- Adapter LlamaIndex/Haystack не меняет публичный API и может быть заменен на `SimpleRetriever`.
- LangGraph pilot не меняет storage schema без отдельного migration ADR; rollback возвращает workflow к текущему `AgentOrchestrator`.
- При ошибках retrieval или adapter runtime должен возвращать controlled warning и продолжать через deterministic fallback, если это допустимо для stage.
- Dependency rollback включает удаление dependency из manifest, отключение feature flag и возврат к internal implementation.

## License/dependency gate

До добавления любой новой AI/RAG/workflow dependency в `requirements.txt`, `package.json`, Docker image или production deployment требуется отдельная проверка:

- license основного пакета;
- transitive dependencies;
- cloud/enterprise/additional terms;
- telemetry и outbound network behavior;
- data residency implications;
- compatibility с коммерческой поставкой;
- security review dependency surface;
- ADR или dependency decision note.

Запрещено без отдельного approval:

- GPL/AGPL/SSPL dependencies;
- non-commercial/source-available лицензии;
- dependencies с Commons Clause или похожими ограничениями;
- managed/cloud services, которые отправляют project artifacts или context sources без явного data-flow решения.

