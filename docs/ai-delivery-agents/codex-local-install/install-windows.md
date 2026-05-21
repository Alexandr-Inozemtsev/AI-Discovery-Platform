# Установка Codex delivery agents на Windows

## Назначение

Инструкция копирует локальные TOML-шаблоны глобальных Codex delivery agents в папку пользователя Codex. Это не меняет production-код и не устанавливает runtime-агентов продукта.

## Шаги

1. Откройте PowerShell.

2. Перейдите в корень репозитория:

```powershell
cd C:\Projects\AI-Discovery-Platform
```

3. Проверьте текущий путь:

```powershell
Get-Location
```

Ожидаемый путь:

```text
C:\Projects\AI-Discovery-Platform
```

4. Выполните установку:

```powershell
powershell -ExecutionPolicy Bypass -File docs/ai-delivery-agents/codex-local-install/install-agents.ps1
```

5. Проверьте установку:

```powershell
powershell -ExecutionPolicy Bypass -File docs/ai-delivery-agents/codex-local-install/verify-agents.ps1
```

6. Перезапустите Codex или терминал, если agents не появились сразу.

7. Проверьте, что agents доступны в вашей версии Codex.

## Важно

Если Codex CLI в вашей версии ожидает другой формат TOML-профилей, адаптируйте файлы из `agents-toml/` под официальный формат этой версии.

