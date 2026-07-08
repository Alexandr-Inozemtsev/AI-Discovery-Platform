# Release gate checklist

Дата: 2026-07-08

## Обязательные проверки перед release

Выполняйте команды из корня repository `C:\Projects\AI-Discovery-Platform`.

### 1. Repository hygiene

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check-repo-hygiene.ps1
```

Проверка должна завершиться с exit code `0`.

Gate блокируется, если в `git ls-files` найдены:
- `node_modules/`;
- `.venv/` или `venv/`;
- `.env` или `.env.*`, кроме `.env.example`;
- `__pycache__/` или `*.pyc`;
- `credentials*`, `cookies*`, `token*`;
- `*.key`, `*.pem`, `*.p12`, `*.pfx`.

Разрешены только безопасные шаблоны без секретов, например `.env.example` и `docs/**/mcp.example.json`.

### 2. Backend tests

```powershell
cd discovery-ai-agent/backend
python -m pytest -q
```

Ожидаемый результат: все backend tests проходят.

### 3. Frontend build

```powershell
cd discovery-ai-agent/frontend
npm run build
```

Ожидаемый результат: TypeScript/Vite build проходит. Warning о размере chunk не блокирует release, если нет runtime regression.

### 4. Browser smoke

Запустите backend и frontend:

```powershell
cd discovery-ai-agent/backend
python -m uvicorn app.main:app --reload --port 8000
```

```powershell
cd discovery-ai-agent/frontend
npm run dev
```

Проверьте в браузере:
- AI Discovery Chat Panel открывается в Project Workspace;
- команда `@problem` создаёт preview/diff, но не применяет patch автоматически;
- apply обновляет `PROBLEM` artifact и stage view;
- rejected action нельзя применить;
- stale patch возвращает `VERSION_CONFLICT` с русским user-facing сообщением.

Если browser automation недоступна, статус browser smoke должен быть `not executed`, а release readiness остаётся `not ready`.

### 5. No secrets

Перед release убедитесь, что:
- реальные API keys, bearer tokens, cookies, MCP credentials и private endpoints не tracked;
- `assistant_tool_runs` не содержит полный corporate chunk text;
- MCP/Corporate Tool Gateway остаётся read-only в MVP;
- `.env`, local config и credentials находятся только локально и покрыты `.gitignore`.

## Release decision

Release readiness может быть `ready` только если:
- repository hygiene прошёл;
- backend tests прошли;
- frontend build прошёл;
- browser smoke выполнен фактически и без blocker;
- security checklist не содержит P0/P1 blocker.
