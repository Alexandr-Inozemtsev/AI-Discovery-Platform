# Local install package для Codex delivery agents

Эта папка содержит install package для локальных TOML-профилей глобальных Codex delivery agents проекта AI Discovery Platform.

Package не устанавливает агентов автоматически в GitHub, репозиторий или Codex Cloud. Фактическая установка выполняется локально пользователем на своей машине.

Целевой путь установки на Windows:

```text
C:\Users\alexp\.codex\agents
```

Содержимое package:

- `agents-toml/` - 20 TOML-шаблонов глобальных Codex delivery agents.
- `install-agents.ps1` - PowerShell-скрипт копирования TOML-файлов в локальную папку Codex.
- `verify-agents.ps1` - PowerShell-скрипт проверки наличия всех 20 TOML-файлов.
- `install-windows.md` - инструкция установки на Windows.
- `verify-installation.md` - инструкция проверки и устранения типовых проблем.

## Важные ограничения

- Это Global Codex Delivery Agents, а не Product AI Agents runtime-приложения.
- Production-код AI Discovery Platform не меняется.
- Backend `AgentOrchestrator`, `discovery-ai-agent/backend/app/agents`, API, frontend, DB-модели и миграции не затрагиваются.
- TOML-формат сделан простым и переносимым. Если конкретная версия Codex CLI использует другой официальный формат agent profiles, эти шаблоны нужно адаптировать под фактическую версию.
- Скрипты не содержат API keys, tokens, passwords или других секретов.

## Быстрый запуск

Из корня репозитория:

```powershell
powershell -ExecutionPolicy Bypass -File docs/ai-delivery-agents/codex-local-install/install-agents.ps1
powershell -ExecutionPolicy Bypass -File docs/ai-delivery-agents/codex-local-install/verify-agents.ps1
```

После установки может потребоваться перезапустить Codex или терминал.

