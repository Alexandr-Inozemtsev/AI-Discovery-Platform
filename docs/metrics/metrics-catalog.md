# Каталог метрик AI Discovery Platform

Дата: 2026-05-17

## Цель

Определить продуктовые метрики, метрики качества AI и backlog событий, чтобы управлять развитием платформы на данных.

## Продуктовые метрики

| Метрика | Формула | Вопрос |
|---|---|---|
| Активация | доля пользователей, создавших первый проект и загрузивших контекст | Доходят ли пользователи до первого полезного шага |
| Принятие функциональности | доля проектов с генерацией Problem/Goal/Requirements | Используют ли AI-функции |
| Удержание | доля пользователей, вернувшихся в течение 7/30 дней | Есть ли повторная ценность |
| Доля завершённых Discovery | проекты со статусом БТ готово / все проекты | Заканчивается ли процесс результатом |
| Время до готового БТ | время от создания проекта до export DOCX | Ускоряет ли платформа Discovery |
| Конверсия в экспорт | проекты с DOCX export / проекты с контекстом | Получают ли пользователи финальный артефакт |

## Метрики качества AI

| Метрика | Описание |
|---|---|
| Context readiness score | качество входного контекста для генерации |
| Retrieval hit rate | доля генераций, где были найдены релевантные chunks |
| Source coverage | доля утверждений, связанных с источниками |
| Fallback rate | доля запусков с deterministic fallback |
| Invalid JSON rate | доля некорректных структурированных LLM-ответов |
| Hallucination flags | число утверждений без источников или с противоречиями |
| User edit rate | доля AI-текста, изменённая пользователем |
| LLM latency | время ответа provider |
| Extraction failure rate | доля источников с ошибкой извлечения |

## Event tracking backlog

| Event | Когда отправляется | Обязательные свойства |
|---|---|---|
| `project_created` | создан проект | project_id, user_id, created_at |
| `context_source_uploaded` | загружен источник | source_id, type, size, status |
| `context_analyzed` | завершён анализ контекста | project_id, readiness_score, source_count |
| `agent_run_started` | начат запуск агента | trace_id, agent_name, artifact_type |
| `agent_run_completed` | агент завершён | trace_id, status, latency_ms, fallback |
| `artifact_saved` | сохранён артефакт | artifact_type, version, actor |
| `bt_exported` | выполнен DOCX export | project_id, artifact_versions |
| `llm_settings_checked` | проверено подключение | provider, status, latency_ms |
| `validation_completed` | выполнена проверка | readiness, warnings_count, errors_count |

## Dashboard backlog

- Воронка: проект создан -> контекст загружен -> проблема сгенерирована -> БТ экспортирован.
- Качество AI: readiness, retrieval hit rate, fallback, invalid JSON.
- Операционная панель: ошибки extraction, LLM latency, provider status.
- Пользовательская активность: возвращаемость, активные проекты, этапы с наибольшими правками.

## Governance

- Метрики не должны хранить API keys или полный sensitive content.
- Для закрытого контура допускается локальное хранение метрик.
- Внешняя аналитика подключается только через security review и ADR.
