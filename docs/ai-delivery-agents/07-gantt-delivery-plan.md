# Gantt delivery plan

Статус: draft. План ориентировочный на 6-8 недель, начиная с 2026-05-21. Mermaid Gantt ниже не означает подключение к внешнему инструменту.

```mermaid
gantt
    title AI Discovery Platform Delivery Plan
    dateFormat YYYY-MM-DD
    axisFormat %d.%m

    section Delivery Governance
    Стабилизация MVP                         :active, mvp, 2026-05-21, 10d
    Оформление global Codex agents           :agents, 2026-05-21, 7d
    Agent operating model                    :model, after agents, 5d
    Trello operating model                   :trello, 2026-05-25, 5d
    Gantt/reporting                          :gantt, after trello, 5d

    section Product Runtime
    Backend stabilization                    :backend, 2026-05-28, 14d
    Database/audit                           :db, 2026-06-01, 10d
    LLM/RAG settings                         :llm, 2026-06-04, 10d
    Security review                          :security, after llm, 7d

    section Frontend and Quality
    Frontend stabilization                   :frontend, 2026-06-03, 14d
    QA automation                            :qaauto, 2026-06-10, 14d
    DOCX/export                              :docx, 2026-06-12, 8d
    Release readiness                        :release, 2026-06-24, 7d
```

## Правила обновления

- Если меняются сроки, dependencies или release scope, обновляет `ai-delivery-project-manager`.
- Если меняется Trello/backlog scope, `ai-trello-analyst` синхронизирует Markdown package.
- Если план используется только как Mermaid-файл, нельзя утверждать, что он подключен к внешнему Gantt-инструменту.

## Delivery notes

- `BE-01-01` относится к блоку `Backend stabilization`; даты Gantt не изменялись, так как задача фиксирует текущий API contract без изменения сроков.

## Gantt v2: backlog-linked delivery plan

Статус: draft. План связывает 20 эпиков из `docs/backlog/trello-cards.md`, Issue #75 и руководительские артефакты. Даты ориентировочные и не являются внешним обязательством.

```mermaid
gantt
    title AI Discovery Platform Backlog-Linked Delivery Plan
    dateFormat YYYY-MM-DD
    axisFormat %d.%m

    section Discovery Foundation
    ЭПИК-01 Product foundation                         :e01, 2026-05-21, 7d
    ЭПИК-02 Context sources and knowledge indexing     :e02, after e01, 14d
    Issue #75 Links via Corporate RAG and Parser       :i75, after e02, 10d
    ЭПИК-05 Problem Goal Business Effect               :e05, after e02, 10d
    ЭПИК-06 AS IS TO BE Use Cases                      :e06, after e05, 8d
    ЭПИК-07 Requirements                               :e07, after e06, 8d

    section Architecture Stabilization
    ЭПИК-03 Agent Runtime                              :e03, 2026-05-21, 12d
    ЭПИК-04 SimpleRetriever grounding                  :e04, after e03, 10d
    Architecture docs before implementation            :milestone, archgate, 2026-05-28, 0d
    ЭПИК-18 Future RAG adapters                        :e18, after e04, 8d
    ЭПИК-19 LangGraph workflow adapter                 :e19, after e18, 8d

    section UI UX and Frontend
    ЭПИК-10 UI UX and UI Kit                           :e10, 2026-05-28, 12d
    UI design spec before frontend implementation      :milestone, uigate, 2026-06-03, 0d
    Frontend stabilization                             :fe, after uigate, 12d

    section Backend Data Security
    Backend API contract and hardening                 :be, 2026-05-27, 14d
    ЭПИК-11 Data versioning audit                      :e11, after be, 10d
    ЭПИК-09 LLM provider corporate mode                :e09, 2026-06-03, 10d
    ЭПИК-12 Security privacy prompt injection          :e12, after e09, 10d
    Security before Universal Parser                   :milestone, secgate, after e12, 0d

    section Export QA and Operations
    ЭПИК-08 Final BT and DOCX export                   :e08, 2026-06-10, 10d
    ЭПИК-13 Metrics and AI quality monitoring          :e13, 2026-06-12, 8d
    ЭПИК-14 DevOps environments CI CD                  :e14, 2026-06-12, 8d
    ЭПИК-15 QA testing validation                      :e15, after e08, 12d
    Tests before release readiness                     :milestone, qagate, after e15, 0d

    section Delivery Management
    ЭПИК-16 Documentation user instructions            :e16, 2026-05-30, 18d
    ЭПИК-17 Trello delivery operating model            :e17, 2026-05-30, 8d
    ЭПИК-20 Commercial packaging monetization          :e20, after qagate, 8d
    Management presentation                            :mgmt, 2026-05-31, 7d
    Pilot readiness                                    :pilot, after qagate, 7d
```

## Dependencies v2

- Architecture docs before implementation.
- Security before Universal Parser.
- Context/RAG before Problem/Goal grounding.
- UI design spec before frontend implementation.
- Tests before release readiness.
- Issue #75 зависит от context/RAG design, security controls и frontend Context screen spec.

## Product AI Agents architecture decision impact

Статус: draft. Этот блок отражает архитектурный impact review Product AI Agents от 2026-05-22. Mermaid Gantt ниже не означает подключение к внешнему Gantt-инструменту и не меняет автоматически сроки существующих задач.

Связанные документы:

- `docs/architecture/product-ai-agents-architecture-review.md`;
- `docs/architecture/product-ai-agents-target-architecture.md`;
- `docs/architecture/ADR-003-product-ai-agents-target-architecture.md`;
- `docs/backlog/product-ai-agents-architecture-decision-backlog.md`.

```mermaid
gantt
    title Product AI Agents Target Architecture Impact
    dateFormat YYYY-MM-DD
    axisFormat %d.%m

    section Architecture Decision
    Review Product AI Agents architecture                 :done, pa_review, 2026-05-22, 1d
    ADR-003 approval and scope decision                   :pa_adr, after pa_review, 3d
    StageProcessor contract design                        :pa_contract, after pa_adr, 4d
    Manual Trello card review                             :pa_trello, after pa_adr, 2d

    section Runtime Hardening
    BE-02-01 AgentResult unification                      :pa_be0201, after pa_adr, 5d
    BE-02-02 Canonical generation flows                   :pa_be0202, after pa_be0201, 5d
    StageDraftProcessor migration plan                    :pa_stage, after pa_be0202, 5d
    SimpleRetriever evidence integration                  :pa_rag, after pa_contract, 6d

    section QA and Corporate Readiness
    Prompt regression and golden datasets                 :pa_qa, after pa_contract, 5d
    Security and corporate wording review                 :pa_sec, after pa_adr, 4d
    Go or no-go for implementation                        :milestone, pa_gate, after pa_stage, 0d
```

Delivery impact:

- Если ADR отклонён, блок остаётся decision record и не создаёт implementation scope.
- Если ADR принят, `ARCH-PA-01`, `BE-02-05`, `BE-02-06` и `QA-PA-01` нужно включить в активный backlog.
- Trello API не вызывался; создан только manual import package в Markdown.
- Remediation 2026-05-22: конфликт ADR-нумерации устранён переносом Product AI Agents target architecture в `ADR-003`; сроки Gantt не менялись.

## Chat-first architecture impact

Статус: Phase 1 done, Phase 2 ready for development. Этот блок отражает переход к AI Discovery Chat как единой точке входа без замены FastAPI/React runtime.

Связанные документы:

- `docs/architecture/ADR-004-ai-discovery-chat-architecture.md`;
- `docs/architecture/chat-orchestrator-contract.md`;
- `docs/architecture/ADR-003-product-ai-agents-target-architecture.md`;
- `docs/architecture/agent-runtime-contract.md`;
- `docs/security/security-requirements.md`;
- `docs/backlog/product-ai-agents-architecture-decision-backlog.md`.

```mermaid
gantt
    title AI Discovery Chat Phase 1-2
    dateFormat YYYY-MM-DD
    axisFormat %d.%m

    section Phase 1 Architecture and Contracts
    ARCH-CHAT-01 ADR-004 AI Discovery Chat Architecture       :done, chat_adr, 2026-07-08, 1d
    ARCH-CHAT-02 ADR-003 and Chat Orchestrator linkage        :done, chat_link, 2026-07-08, 1d
    BE-RUNTIME-01 StageProcessorRequest and Result            :done, chat_runtime, 2026-07-08, 1d
    SEC-CHAT-01 ToolPolicy                                    :done, chat_policy, 2026-07-08, 1d

    section Phase 2 Implementation
    Chat Orchestrator backend service                         :chat_be, after chat_policy, 4d
    Chat endpoint contract and API tests                      :chat_api, after chat_be, 3d
    Patch preview and apply service                           :chat_patch, after chat_api, 4d
    React AI Discovery Chat shell                             :chat_fe, after chat_api, 5d
    Chat workflow regression                                  :chat_qa, after chat_patch, 3d
```

Delivery impact:

- Phase 2 может начинаться после acceptance Phase 1 docs/contracts.
- Существующие endpoint paths остаются совместимыми.
- Формы этапов Discovery остаются structured state артефактов и fallback UI.
- Trello API не вызывался; создан только Markdown package.
