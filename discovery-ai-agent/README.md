# AI Discovery Agent (MVP, этап 1)

## Запуск
```bash
cd discovery-ai-agent
docker compose up --build
```

## Миграции
В отдельном терминале:
```bash
docker compose exec backend alembic upgrade head
```

## URL
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Health: http://localhost:8000/health

## Доступные endpoints
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
