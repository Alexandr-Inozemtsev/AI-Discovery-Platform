# Инструкция локального запуска AI Discovery Platform

Дата: 2026-05-17

## Требования

- Windows.
- Python 3.11 или выше.
- Node.js 20 или выше.
- Доступ к папке `discovery-ai-agent`.

## Запуск через `start.bat`

1. Откройте папку `C:\Projects\AI-Discovery-Platform\discovery-ai-agent`.
2. Запустите `start.bat`.
3. Дождитесь запуска backend и frontend.
4. Откройте frontend: `http://localhost:5173`.
5. Проверьте backend health: `http://localhost:8000/health`.

## Backend отдельно

```bat
cd C:\Projects\AI-Discovery-Platform\discovery-ai-agent\backend
run_backend.bat
```

## Frontend отдельно

```bat
cd C:\Projects\AI-Discovery-Platform\discovery-ai-agent\frontend
run_frontend.bat
```

## Локальная база

SQLite файл:

```text
C:\Projects\AI-Discovery-Platform\discovery-ai-agent\backend\data\discovery_agent.db
```

## Repository hygiene

Перед release и перед подготовкой commit проверьте, что локальные артефакты и secrets не попали в git index:

```powershell
cd C:\Projects\AI-Discovery-Platform
powershell -ExecutionPolicy Bypass -File scripts/check-repo-hygiene.ps1
```

Проверка должна завершиться без нарушений. Если найдены `node_modules/`, `.venv/`, `.env`, `__pycache__/`, `*.pyc`, credentials, cookies или token files, удалите их из git index через `git rm --cached`, не удаляя локальные файлы с диска.

## Очистка локальных данных

1. Остановите backend и frontend.
2. Удалите `backend\data\discovery_agent.db`.
3. При необходимости очистите `backend\storage`.
4. Запустите приложение снова.

## LLM settings

По умолчанию используется mock provider.

Для корпоративного provider:
- откройте «Настройки -> LLM настройки»;
- укажите provider, base URL, model и API key;
- нажмите «Проверить подключение»;
- убедитесь, что статус подключён.

## Частые проблемы

### Backend недоступен

- Проверьте, что порт `8000` свободен.
- Проверьте Python version.
- Проверьте backend terminal на ошибки dependencies.

### Frontend недоступен

- Проверьте, что порт `5173` свободен.
- Проверьте Node.js version.
- Выполните `npm install` в `frontend`, если зависимости не установлены.

### Ошибка LLM

- Проверьте API key.
- Проверьте base URL.
- Проверьте model name.
- Для закрытых данных используйте корпоративный provider.

### Не извлекается текст из файла

- Проверьте формат.
- Для XLS используйте XLSX или CSV.
- Для больших PDF используйте сокращённый документ или ручное описание.

## Smoke: AI Chat Q&A по DOCX

1. Запустите backend и frontend.
2. Откройте `http://localhost:5173` и перейдите в проект.
3. На этапе «Контекст» загрузите DOCX с описанием процесса.
4. Дождитесь, что файл появился в источниках и у него есть chunks/extracted text.
5. В AI Discovery Chat спросите: `найди описание БТ во вложении`.
6. Ожидаемый результат:
   - ответ приходит без `Failed to fetch`;
   - в ответе есть краткая выдержка по документу;
   - отображается блок «Найдено в источниках»;
   - кнопка «Применить в артефакт» не активируется, если нет proposed patch.

Если после загрузки файла `indexing_status = requires_update`, AI Chat всё равно использует уже извлечённые chunks и показывает мягкое предупреждение, что контекст требует обновления.
