# Проверка установки Codex delivery agents

## Проверка через скрипт

Из корня репозитория:

```powershell
powershell -ExecutionPolicy Bypass -File docs/ai-delivery-agents/codex-local-install/verify-agents.ps1
```

Если все 20 TOML-файлов найдены, скрипт вернет exit code `0`.

Если хотя бы одного файла нет, скрипт покажет `MISSING` и вернет exit code `1`.

## Ручная проверка

Проверьте целевую папку:

```powershell
Get-ChildItem "$env:USERPROFILE\.codex\agents" -Filter "*.toml"
```

Ожидается 20 файлов с именами `ai-*.toml`.

## Частые ошибки

### Не тот путь

Симптом: скрипт не находит `agents-toml`.

Что делать: запустить команду из корня репозитория `C:\Projects\AI-Discovery-Platform` или убедиться, что структура `docs/ai-delivery-agents/codex-local-install/agents-toml` существует.

### PowerShell execution policy

Симптом: PowerShell блокирует запуск `.ps1`.

Что делать: использовать команду с `-ExecutionPolicy Bypass`, как в инструкции установки.

### Codex не видит агентов до перезапуска

Симптом: файлы есть в `$env:USERPROFILE\.codex\agents`, но Codex не показывает agents.

Что делать: перезапустить Codex Desktop, Codex CLI или терминал.

### Формат TOML не соответствует версии Codex

Симптом: Codex видит файлы, но не загружает профили или сообщает ошибку parsing/config.

Что делать: сверить официальный формат agent profiles вашей версии Codex CLI и адаптировать поля TOML. Текущий package использует безопасный переносимый шаблон, но не утверждает совместимость со всеми версиями Codex.

## Что считается успешной установкой

- Папка `$env:USERPROFILE\.codex\agents` существует.
- Все 20 TOML-файлов присутствуют.
- `verify-agents.ps1` завершился с exit code `0`.
- После перезапуска ваша версия Codex видит или принимает эти локальные profiles.

