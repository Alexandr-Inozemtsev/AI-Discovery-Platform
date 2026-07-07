# ADR-003: Целевая модель Product AI Agents

Дата: 2026-05-22  
Статус: accepted as baseline for ADR-004 chat-first architecture  
Scope: Product AI Agents внутри backend AI Discovery Platform  
Не scope: Global Codex Delivery Agents, замена FastAPI/React runtime, DB migration, внешние AI frameworks.

Примечание по нумерации: `docs/architecture/adr-002-target-platform-evolution.md` сохраняет номер `ADR-002` и смысл решения по эволюции платформы. ADR по Product AI Agents выделен в отдельный номер `ADR-003`, чтобы исключить конфликт архитектурных ссылок.

## Контекст

AI Discovery Platform уже содержит собственный backend Agent Runtime:

- `AgentOrchestrator`;
- `BaseAgent`;
- `AgentContext`;
- `AgentResult`;
- Product AI Agents: `ContextIngestionAgent`, `ProblemAgent`, `GoalAgent`, `BusinessEffectAgent`, `UseCaseAgent`, `RequirementsAgent`, `CriticAgent`.

Фактический review показал:

- `ContextIngestionAgent` является специализированным компонентом с отдельным JSON-контрактом, `source_trace`, `coverage`, `readiness`, `problem_handoff`;
- `ProblemAgent`, `GoalAgent`, `BusinessEffectAgent`, `UseCaseAgent` сейчас являются в основном stage-specific prompt wrappers;
- `RequirementsAgent` уже используется для нескольких artifact types;
- `CriticAgent` используется как отдельный validation component;
- generic generation и stage-specific generation пока расходятся по response shape и месту логики;
- `source_trace` и retrieval evidence ещё не унифицированы для всех downstream artifacts.

## Решение

Выбрать гибридную целевую модель:

```text
Agent Runtime
  ContextIngestionAgent
  StageDraftProcessor
    problem_template
    goal_template
    business_effect_template
    use_cases_template
  RequirementsProcessor
    functional_requirements_template
    non_functional_requirements_template
    final_bt_template
  CriticAgent / ValidationProcessor
  SimpleRetriever
  PromptRegistry
  LLM Gateway
```

Решение означает:

- не считать каждый stage wrapper самостоятельным корпоративным AI-сервисом;
- использовать эту модель как backend foundation для AI Discovery Chat из `ADR-004`;
- сохранить отдельным `ContextIngestionAgent`;
- сохранить отдельным validation/critic component;
- объединить draft stages через processor + prompt templates;
- оставить Requirements как специализированный processor из-за delivery-impact и необходимости строгих requirement contracts;
- не давать chat/runtime компонентам прямую запись в `discovery_artifacts` без `proposed_patch -> preview -> apply`;
- не внедрять полный refactor немедленно, пока не утверждён migration backlog.

## Связка с AI Discovery Chat

`ADR-004` добавляет chat-first UX поверх этой модели. Граница ответственности:

- `Chat Orchestrator` управляет intent, policy, user-facing ответом, proposed patch и apply gate;
- `StageDraftProcessor` и `RequirementsProcessor` готовят stage-specific результат через `StageProcessorRequest/StageProcessorResult`;
- `ContextIngestionAgent` остается отдельным workflow для анализа контекста;
- `CriticAgent` / `ValidationProcessor` остается отдельным validation компонентом;
- `ToolPolicy` запрещает прямую запись AI-чата в `discovery_artifacts`.

Таким образом, ADR-003 отвечает на вопрос "какая runtime-модель Product AI Agents используется", а ADR-004 отвечает на вопрос "как пользователь управляет этой моделью через chat-first UX".

## Альтернативы

### A. Оставить текущую модель

Плюсы:

- минимальный риск для MVP;
- понятное соответствие class names и Discovery stages;
- не требует миграции.

Минусы:

- дублирование prompt/fallback lifecycle;
- слабое объяснение для corporate architecture;
- много QA объектов без пропорциональной пользы;
- риск роста несогласованности prompts и contracts.

### B. Единый Agent Runtime + stage processors

Плюсы:

- меньше дублирования;
- проще prompt governance;
- проще security approval;
- лучше testability через stage contracts.

Минусы:

- нужна миграция и compatibility layer;
- риск сломать stage-specific behavior при поспешном refactor.

### C. Один универсальный DiscoveryAgent

Плюсы:

- самый простой registry;
- меньше классов.

Минусы:

- слабая stage isolation;
- выше hallucination risk;
- сложнее prompt regression;
- хуже подходит для structured requirements и evidence.

### D. Гибрид

Плюсы:

- сохраняет реальную специализацию там, где она есть;
- убирает лишние stage wrappers;
- хорошо объясняется в corporate environment;
- совместим с `SimpleRetriever` и prompt registry;
- позволяет мигрировать постепенно.

Минусы:

- требует нового processor contract;
- требует аккуратной синхронизации generic и specialized endpoints;
- требует QA golden datasets.

## Последствия

Положительные:

- меньше архитектурного overhead;
- меньше security approval objects;
- единый LLM Gateway и audit;
- лучшее управление prompt versions;
- проще распространять `source_trace` и evidence на downstream artifacts;
- QA фокусируется на stage contracts, а не на количестве Python classes.

Отрицательные:

- потребуется delivery task на migration plan;
- понадобится compatibility strategy для существующих endpoint paths;
- текущие docs и backlog нужно синхронизировать;
- нужна дисциплина prompt registry и regression tests.

## Implementation guidance

Не реализовывать этот ADR одной большой правкой.

Рекомендуемый порядок:

1. Утвердить ADR.
2. Закрыть BE-02-01: единый `AgentResult` contract для всех генераторов.
3. Закрыть BE-02-02: определить canonical generation flows и compatibility endpoints.
4. Спроектировать `StageProcessorRequest` и `StageProcessorResult`.
5. Ввести `ToolPolicy` для AI Discovery Chat.
6. Добавить `Chat Orchestrator` как application service без изменения существующих endpoint paths.
7. Добавить `StageDraftProcessor` за существующими endpoint paths.
8. Подключить `SimpleRetriever` и evidence propagation.
9. Добавить prompt regression/golden datasets.
10. Депрецировать лишние stage wrappers только после тестов и release notes.

## Corporate wording

Для корпоративной документации использовать формулировку:

> Система использует единый Agent Runtime с управляемыми режимами генерации Discovery-артефактов. Режимы используют общий LLM Gateway, общий prompt registry, общий audit и общий retrieval boundary.

Не использовать формулировку:

> В системе работает отдельный автономный AI Agent на каждый этап Discovery.

## Rollback

Так как этот ADR пока не меняет production-код, rollback документационный:

- отменить ADR или перевести в статус rejected;
- оставить текущую модель Product AI Agents;
- убрать backlog migration task из active delivery scope;
- Gantt вернуть к предыдущей версии.

## Связанные документы

- [Экспертный review архитектуры Product AI Agents](product-ai-agents-architecture-review.md);
- [ADR-004 AI Discovery Chat Architecture](ADR-004-ai-discovery-chat-architecture.md);
- [Chat Orchestrator Contract](chat-orchestrator-contract.md);
- [Целевая архитектура Product AI Agents](product-ai-agents-target-architecture.md);
- [Backlog по архитектурному решению](../backlog/product-ai-agents-architecture-decision-backlog.md);
- [Agent Runtime Contract](agent-runtime-contract.md);
- [SimpleRetriever Contract](simple-retriever-contract.md);
- [RAG/retrieval target design](../llm-rag/rag-and-retrieval-target-design.md).
