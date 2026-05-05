# AI Discovery Agent (MVP, локальный запуск на Windows)

## Требования
- Python 3.11+
- Node.js 20+

## Запуск
1. Откройте папку `discovery-ai-agent`.
2. Запустите `start.bat` двойным кликом или через PowerShell/CMD.
3. Скрипт автоматически:
   - создаст backend venv (если нет),
   - установит Python зависимости,
   - поднимет backend на `http://localhost:8000`,
   - откроет новое окно PowerShell для frontend,
   - выполнит `npm install` (если `node_modules` нет),
   - поднимет frontend на `http://localhost:5173`.

## URL
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Health check: http://localhost:8000/health

## Где хранится база
- SQLite файл: `backend/data/discovery_agent.db`

## Где хранятся файлы
- Локальные файлы приложения (для следующих этапов, например DOCX): `backend/storage/`

## Как удалить локальные данные
1. Остановить backend/frontend процессы.
2. Удалить файл `backend/data/discovery_agent.db`.
3. При необходимости очистить `backend/storage/`.

## API endpoints
### Projects
- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/{project_id}`
- `PATCH /api/projects/{project_id}`
- `DELETE /api/projects/{project_id}`

### Artifacts
- `GET /api/projects/{project_id}/artifacts`
- `GET /api/projects/{project_id}/artifacts/{artifact_type}`
- `PUT /api/projects/{project_id}/artifacts/{artifact_type}`

### Health
- `GET /health`
