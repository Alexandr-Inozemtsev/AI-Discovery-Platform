# Context screen spec

## Назначение

Страница Контекст собирает ручное описание инициативы, файлы, ссылки и corporate knowledge, затем формирует `extracted_knowledge`, `source_trace`, `coverage`, `readiness` и `problem_handoff`.

## Ручной контекст

- Название инициативы.
- Краткое описание.
- Бизнес-домен.
- Целевая аудитория.
- Известные ограничения.
- Вопросы и гипотезы.

## Источники знаний

Source list показывает `title`, `type`, `status`, `chunksCount`, `errorMessage`, `updatedAt` и связь с `source_trace`.

## Файлы

Поддерживаемые MVP форматы: txt, md, csv, docx, pdf, xlsx. `xls` должен быть явно показан как unsupported с рекомендацией конвертации в xlsx/csv.

Состояния: uploaded, indexing, ready, empty, unsupported, error, metadata-only.

## Ссылки

Текущий MVP хранит links как metadata. Target flow для Issue #75:

- Corporate RAG mode: URL передается в CorporateRagConnector, который возвращает chunks и metadata.
- Universal Parser mode: URL парсится через UniversalLinkParser с security controls.

## Corporate RAG mode

UI показывает режим источника, search scope, найденные chunks, confidence/source metadata и предупреждение, если RAG недоступен.

## Universal Parser mode

UI показывает статус HTML fetch, main text extraction, найденные attachments, статус обработки каждого attachment и security rejection reason.

## Вложения

Allowlist: txt, md, csv, docx, pdf, xlsx. Для MVP запрещены executable files, archive parsing, private IP targets, unknown protocols и oversized files.

## Extracted knowledge

Блоки: summary, facts, assumptions, missing information, contradictions, source references.

## Coverage

Coverage показывает, какие части Discovery достаточно подкреплены источниками, а какие требуют уточнения.

## Readiness

- `ready` - можно переходить к Problem.
- `warning` - можно продолжить, но есть gaps.
- `blocked` - недостаточно данных.

## Переход к Problem

Кнопка перехода доступна всегда, но при `warning/blocked` показывает предупреждение и missing information. `problem_handoff` передается в Problem stage.

## Связанные документы

- [Схема Context Ingestion и RAG](../architecture/diagrams/04-context-ingestion-and-rag.md)
- [Схема Issue #75](../architecture/diagrams/06-link-processing-corporate-rag-and-parser.md)
- [RAG target design](../llm-rag/rag-and-retrieval-target-design.md)
- [Current OpenAPI contract](../api/openapi-contracts-current.md)

