# Quality gates глобальных Codex-агентов

| Gate | Кто отвечает | Что проверяется | Какие файлы должны быть обновлены | Тесты/проверки | Что считается fail |
|---|---|---|---|---|---|
| Product gate | `ai-product-orchestrator` | Scope, цели, DoR/DoD, value. | `docs/backlog/*`, product docs при изменении scope. | Проверка непротиворечивости требований. | Нет цели, критериев приемки или владельца. |
| Architecture gate | `ai-solution-architect` | Target architecture, API/data contracts, rollout/rollback. | `docs/architecture/*`, ADR при необходимости. | Review contracts и dependencies. | Backend/frontend/DB меняются без architecture decision. |
| Backend gate | `ai-backend-developer` | API, services, validation, errors, logging. | Backend код и docs API при необходимости. | Unit/API tests или объясненный gap. | Непроверенный endpoint, сломанный контракт, secrets в коде. |
| Frontend gate | `ai-frontend-developer` | UI states, routing, API integration, accessibility basics. | Frontend код, design docs/screenshots при UI изменениях. | Build, UI smoke, browser screenshot при возможности. | White screen, broken route, непроверенные states. |
| Database gate | `ai-database-engineer` | Schema, migrations, indexes, constraints, rollback. | Migrations, data docs. | Migration test/inspection. | Несовместимая миграция без rollback. |
| LLM/RAG gate | `ai-llm-rag-engineer` | Prompts, retrieval, provider boundary, traceability, token/cost. | `docs/llm-rag/*`, prompt docs. | Prompt review, eval checklist, source trace check. | Нет traceability или provider assumptions скрыты. |
| Security gate | `ai-security-reviewer` | Auth/authz, secrets, privacy, injection, dependency risk. | `docs/security/*`, threat notes. | Security checklist, secret scan по необходимости. | Секреты в репозитории, external data transfer без policy. |
| QA gate | `ai-qa-engineer` | Acceptance criteria, regression, exploratory findings. | `docs/qa/*`, test report. | Smoke/regression/manual tests. | Нет проверки ключевого flow. |
| Documentation gate | `ai-technical-writer` | README, runbook, API/user docs, release docs. | Соответствующие docs. | Link/path sanity check. | Документы противоречат коду или не на русском. |
| Trello gate | `ai-trello-analyst` | Board model, cards, labels, checklist, sync status. | `docs/backlog/trello-cards.md`, `06-trello-operating-model.md`. | Проверка полноты карточек. | Утверждение о созданной доске без подтверждения. |
| Gantt gate | `ai-delivery-project-manager` | Milestones, dates, dependencies, critical path. | `07-gantt-delivery-plan.md`, roadmap docs. | Mermaid syntax inspection. | Изменены сроки без обновления Gantt. |
| Release gate | `ai-release-manager` | Readiness, changelog, rollback, approvals. | Release notes, runbook, docs. | Go/no-go checklist. | Нет rollback plan при production impact. |

