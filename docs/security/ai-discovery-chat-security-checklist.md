# Security checklist AI Discovery Chat

Дата проверки: 2026-07-08

## Проверки

- [x] AI Discovery Chat не применяет изменения автоматически: запись в артефакт идёт только через `proposed_patch -> preview -> apply`.
- [x] `ApplyPatchService` проверяет `project_id`, `session_id`, `action_id`, `action_type` и статус действия.
- [x] `ApplyPatchService` применяет только действия в статусах `proposed` или `previewed`; `applied`, `rejected` и `failed` заблокированы.
- [x] `assistant_tool_runs` не сохраняет полный `proposed_patch`, полный patch или retrieved chunk text; в audit остаются `patch_hash`, список изменённых полей и счётчики.
- [x] `ToolPolicy` для AI Discovery Chat разрешает только read/search операции для Confluence, Jira, Git и RAG в MVP.
- [x] `ToolPolicy` явно запрещает write/push и доступ к credentials.
- [x] LLM provider errors не раскрываются пользователю: наружу возвращается безопасное русскоязычное сообщение, raw details остаются только во внутреннем состоянии/логах.
- [x] Добавлен root `.gitignore` для `.env`, local config, ключей, cookies, tokens и runtime cache.
- [x] `discovery-ai-agent/.env` снят с git index без удаления локального файла.

## Оставшиеся риски

- Нужно добавить миграцию/retention policy для уже существующих строк `assistant_tool_runs`, если в базе до исправления были сохранены полные patch или фрагменты документов.
- Нужна отдельная проверка backend logs, чтобы raw LLM/MCP errors и корпоративные документы не попадали в пользовательские ответы или долгоживущие логи.
- Для Corporate Tool Gateway нужны интеграционные тесты с реальными adapter mocks: Confluence/Jira/Git/RAG должны оставаться read-only на уровне gateway, а не только `ToolPolicy`.
- Перед production включением требуется privacy review для хранения `assistant_messages.payload` и `assistant_actions.proposed_patch`, потому что proposed patch может содержать business-sensitive данные.

## Блокеры

Блокеры из security review закрыты на уровне backend foundation. Для Phase 2 остаются не блокеры, а обязательные hardening-задачи: миграция/очистка старых audit logs, gateway-level read-only enforcement и политика retention.
