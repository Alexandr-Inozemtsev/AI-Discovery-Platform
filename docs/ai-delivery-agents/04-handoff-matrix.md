# Handoff-матрица глобальных Codex-агентов

| From agent | To agent | Когда выполняется handoff | Что передается | Формат результата | Критерии приемки |
|---|---|---|---|---|---|
| `ai-orchestrator` | `ai-product-orchestrator` | Задача требует уточнения product scope. | Цель, ограничения, ожидаемые артефакты. | Codex task brief. | Scope понятен, есть DoR/DoD. |
| `ai-product-orchestrator` | `ai-business-analyst` | Нужно оформить бизнес-требования. | Problem statement, цели, stakeholders. | Business analysis brief. | Есть бизнес-цель и критерии успеха. |
| `ai-business-analyst` | `ai-system-analyst` | Бизнес-требования готовы к системной детализации. | User stories, business rules, acceptance criteria. | System analysis input. | Нет противоречий в правилах. |
| `ai-system-analyst` | `ai-solution-architect` | Нужно определить target architecture или API/data contracts. | API, поля, статусы, ошибки, permissions. | Architecture brief/ADR input. | Контракты проверяемы. |
| `ai-solution-architect` | `ai-backend-developer` | Backend implementation готова к разработке. | API contract, services, errors, rollout. | Backend task. | Есть acceptance criteria и rollback impact. |
| `ai-solution-architect` | `ai-frontend-developer` | Frontend implementation готова к разработке. | Screen flow, API contract, states. | Frontend task. | Есть UX states и API assumptions. |
| `ai-solution-architect` | `ai-database-engineer` | Нужны schema/migration/index изменения. | Data model, constraints, migration needs. | DB task. | Есть migration и rollback требования. |
| `ai-solution-architect` | `ai-llm-rag-engineer` | Задача затрагивает LLM/RAG. | Prompt boundary, provider policy, source trace. | LLM/RAG task. | Есть evaluation и token/cost constraints. |
| `ai-llm-rag-engineer` | `ai-security-reviewer` | Есть external provider, prompts, secrets или пользовательские данные. | LLM flow, data sent outside, config needs. | Security review request. | Нет утечки secrets, есть privacy boundary. |
| `ai-backend-developer` | `ai-code-reviewer` | Backend changes готовы к review. | Diff, tests, known risks. | Review package. | Код покрыт проверками или есть reason. |
| `ai-frontend-developer` | `ai-code-reviewer` | Frontend changes готовы к review. | Diff, screenshots, UI states, tests. | Review package. | UI проверен в браузере при возможности. |
| `ai-database-engineer` | `ai-code-reviewer` | DB changes готовы к review. | Migration, indexes, rollback, data risk. | Review package. | Migration не ломает совместимость без плана. |
| `ai-code-reviewer` | `ai-qa-engineer` | Review пройден или замечания зафиксированы. | Findings, changed files, risk areas. | QA brief. | Blocking issues закрыты или явно приняты. |
| `ai-qa-engineer` | `ai-test-automation-engineer` | Нужна автоматизация регрессии. | Manual cases, expected data, flows. | Automation task. | Тесты воспроизводимы. |
| `ai-qa-engineer` | `ai-release-manager` | QA gate пройден. | Test report, residual risks. | Release readiness input. | Критичные дефекты отсутствуют. |
| `ai-delivery-project-manager` | `ai-trello-analyst` | Scope влияет на delivery/backlog. | Milestones, dependencies, priorities. | Trello package update. | Карточки отражают актуальный scope. |
| `ai-technical-writer` | `ai-release-manager` | Документация готова к выпуску. | Docs summary, changelog notes. | Release notes input. | Документы на русском, ссылки актуальны. |
| `ai-release-manager` | `ai-orchestrator` | Выпуск подготовлен. | Release notes, rollback plan, gates. | Final delivery report. | Есть go/no-go recommendation. |

