# Глоссарий AI Discovery Platform

Дата: 2026-05-17

## Термины

`AI Discovery Platform`: платформа для прохождения Discovery и подготовки БТ с помощью AI.

`БТ`: бизнес-требования, формальный документ по результатам Discovery.

`ТЗ`: техническое задание, системное описание требований, API, моделей, ошибок и этапов delivery.

`Discovery`: этап уточнения проблемы, цели, контекста, сценариев, требований и рисков.

`Artifact`: результат этапа Discovery, например Context, Problem, Goal, Requirements или Final BT.

`AgentRuntime`: внутренний слой запуска агентов, управления trace, prompt version, LLM metadata и fallback.

`AgentResult`: единый результат работы агента с content, structured_content, warnings, errors, source_trace и metadata.

`AgentContext`: входной контекст агента: проект, артефакты, LLM client, metadata.

`SimpleRetriever`: внутренний retrieval слой без внешних зависимостей и без vector DB на первом этапе.

`RetrievalHit`: найденный chunk с score, source metadata и объяснением совпадения.

`source_trace`: связь AI-утверждения с источником, chunk и версией артефакта.

`readiness`: оценка готовности контекста или этапа к следующему шагу.

`coverage`: покрытие контекстом ключевых областей: процессы, системы, роли, KPI, ограничения, риски.

`prompt version`: версия prompt template, использованная при запуске агента.

`fallback policy`: правила поведения при ошибке LLM, пустом ответе или некорректном JSON.

`LLM provider`: поставщик LLM: mock, OpenRouter или корпоративный OpenAI-compatible endpoint.

`RAG`: retrieval augmented generation, генерация с предварительным поиском релевантных источников.

`LlamaIndex`: возможный будущий RAG-framework adapter, не foundation платформы.

`Haystack`: возможный будущий RAG pipeline adapter, не foundation платформы.

`LangGraph`: возможный будущий workflow adapter для ограниченной цепочки Context -> Problem.

`Dify`, `Flowise`, `RAGFlow`: готовые AI/RAG платформы, не используемые как foundation AI Discovery Platform.
