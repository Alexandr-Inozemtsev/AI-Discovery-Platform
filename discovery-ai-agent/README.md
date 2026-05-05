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

## Этап 2: Mock AI Agents

### Что добавлено
- `POST /api/projects/{project_id}/generate/{artifact_type}` — генерация артефакта mock-агентом и сохранение с увеличением версии.
- `POST /api/projects/{project_id}/validate` — запуск CriticAgent и сохранение отчёта в `VALIDATION_REPORT`.
- Архитектура `llm/base.py` + `llm/mock_client.py`, которую позже можно заменить на корпоративный LLM-клиент без переписывания агентов.

### Как протестировать генерацию
1. Запустить `start.bat`.
2. Создать проект на главной странице.
3. Открыть вкладки «Проблема», «Цель», «Бизнес-эффект», «Use Cases», «Требования» или «Финальный БТ».
4. Нажать «Сгенерировать».
5. Убедиться, что textarea заполнена и версия артефакта увеличилась.
6. Нажать «Проверить» и убедиться, что появился отчёт `VALIDATION_REPORT`.

### Как позже заменить MockLLMClient
1. Создать `CorporateLLMClient`, реализующий интерфейс `BaseLLMClient.generate(prompt: str) -> str`.
2. В `agents/orchestrator.py` заменить инициализацию `MockLLMClient()` на `CorporateLLMClient()`.
3. При необходимости добавить конфигурацию токенов/URL в отдельный settings-модуль.

## Этап 3: Structured Discovery Forms + Completion Checklist
- Добавлены структурированные формы по этапам Discovery (Problem, Goal, Business Effect, Use Cases, Requirements, Risks).
- Добавлен progress/checklist endpoint `GET /api/projects/{project_id}/completion`.
- Сохранение артефакта теперь поддерживает `content` + `structured_content`.

### Как проверить
1. Откройте проект в Workspace.
2. Выберите режим «Структурированная форма», заполните поля и нажмите «Сохранить».
3. Проверьте, что в Progress Panel вырос процент completion.
4. Переключитесь на «Свободный текст» и сохраните `content` — чеклист также учитывает заполненность.

## Новая навигация UI
- Главная страница проектов: `http://localhost:5173/`
- Страница проекта: `http://localhost:5173/projects/{projectId}`
- Переход в проект: кнопка «Открыть» на карточке проекта.
- Возврат на главную: кнопка «← К списку проектов» на странице проекта или «На главную» в верхней панели.
