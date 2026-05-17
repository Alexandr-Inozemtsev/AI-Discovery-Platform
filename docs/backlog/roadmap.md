# Roadmap развития AI Discovery Platform

Дата: 2026-05-17

## Принципы roadmap

- Сначала фиксируются архитектура, backlog, БТ, ТЗ и quality gates.
- Production-код меняется только после утверждения ADR-002 и delivery-ready backlog.
- Внешние AI/RAG-framework dependencies добавляются только после отдельного ADR и license/dependency gate.
- Корпоративный контур является базовым сценарием: локальный запуск, контролируемый LLM, traceability, audit, безопасность.

## Этап 0. Ревизия и подготовка delivery

Период: текущий этап.
Цель: собрать единый пакет документов и Trello-доску.

Результаты:
- БТ и ТЗ на развитие платформы.
- ADR-002 и целевая архитектура.
- Product backlog и roadmap.
- Trello operating model.
- Manual import package для Trello и фактическое оформление доски при доступной интеграции.

## Этап 1. MVP: управляемый Discovery workspace

Цель: довести текущий MVP до повторяемого рабочего процесса.

Входит:
- ЭПИК-01 Продуктовый фундамент и сквозной Discovery-процесс.
- ЭПИК-02 Источники контекста, извлечение текста и индексация знаний.
- ЭПИК-03 Runtime агентов и оркестрация.
- ЭПИК-04 SimpleRetriever и генерация с опорой на источники.
- ЭПИК-05 Проблема, Цель, Бизнес-эффект.
- ЭПИК-07 Функциональные и нефункциональные требования.
- ЭПИК-08 Финальный БТ и DOCX export.
- ЭПИК-09 LLM settings и корпоративный режим.
- ЭПИК-11 Модель данных, версионирование и аудит.
- ЭПИК-12 Безопасность.
- ЭПИК-15 QA.
- ЭПИК-16 Документация.
- ЭПИК-17 Trello operating model.

Критерии выхода:
- Один проект Discovery можно провести от контекста до DOCX.
- Все AI-результаты имеют trace id, source trace и понятный статус.
- Ошибки LLM и extraction не ломают пользовательский flow.
- Есть smoke/regression test plan и локальный runbook.

## Этап 2. MMP: пилотная эксплуатация

Цель: подготовить платформу к пилотам с реальными командами.

Входит:
- ЭПИК-06 AS IS, TO BE, Use Cases.
- ЭПИК-10 UI/UX и UI Kit.
- ЭПИК-13 Метрики продукта и AI quality.
- ЭПИК-14 DevOps и CI/CD.
- Расширение ЭПИК-11 audit и versioning.
- Расширение ЭПИК-15 test automation.

Критерии выхода:
- Пилотная команда может работать без сопровождения разработчика.
- Есть pipeline checks: backend tests, frontend build, lint, security/license gate.
- Метрики показывают activation, export conversion, readiness, fallback и edit rate.
- Документация пригодна для onboarding.

## Этап 3. Целевой промышленный контур

Цель: обеспечить расширяемость, отказоустойчивость и коммерческую готовность.

Входит:
- ЭПИК-18 RAG adapters LlamaIndex/Haystack.
- ЭПИК-19 LangGraph workflow adapter для Context -> Problem.
- ЭПИК-20 Коммерциализация и упаковка.
- Расширенный access control.
- Observability и production monitoring.
- License/SBOM governance.

Критерии выхода:
- Внешние RAG adapters подключаются через стабильный интерфейс.
- LangGraph используется только как optional workflow adapter, если PoC доказал ценность.
- Платформа имеет pilot package, support model и ограничения поставки.

## Go / No-Go критерии

Go для разработки MVP:
- Утверждены БТ, ТЗ и ADR-002.
- Backlog покрывает backend, frontend, LLM/RAG, data, security, DevOps, QA, docs и Trello.
- Trello-доска отражает delivery workflow.

No-Go:
- Требуется подключить внешнюю платформу вместо собственного runtime.
- Требуется добавить dependency без ADR и license gate.
- Не описаны source trace, audit и LLM data policy.
