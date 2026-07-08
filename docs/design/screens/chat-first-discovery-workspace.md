# Screen spec: Chat-first Discovery Workspace

Дата: 2026-07-08

## Назначение экрана

Project Workspace — основной рабочий экран Discovery. Он объединяет навигацию по этапам, structured artifact forms и AI Discovery Chat. Главный принцип: пользователь управляет workflow через AI Chat, а формы показывают текущее структурированное состояние и дают контроль над подтверждением результата.

## Общий Project Workspace

### Layout

| Зона | Назначение | Рекомендации |
|---|---|---|
| Левая навигация | Этапы Discovery, readiness, completion, stale/blocking markers. | Компактный вертикальный список этапов; status dot; completion percent; предупреждения по зависимостям. |
| Центральная область | Structured state текущего артефакта. | Формы, таблицы, preview, версии, source/evidence summary; поля не скрывать. |
| Правая AI Chat Panel | Главная точка входа для команд пользователя. | История сообщений, input, suggested actions, proposed patch preview/diff, warnings/errors. |

### Левая навигация

- Показывает этапы: Context, Problem, Goal, Business Effect, AS IS, TO BE, Use Cases, Requirements, Risks, Final BT.
- Для каждого этапа: статус, версия, stale marker, readiness marker.
- Заблокированные этапы остаются видимыми, но показывают причину блокировки и следующий шаг.
- Верхний блок показывает общий progress и последний изменённый артефакт.

### Центральная область

- Заголовок: название этапа, версия, дата обновления, статус.
- Structured form остаётся основным отображением состояния.
- Для любого AI-предложения центральная область должна подсвечивать поля, которые будут изменены.
- Ручное редактирование не должно конфликтовать с chat flow: если пользователь изменил поле после preview, apply должен предупреждать о возможном конфликте версий.

### Правая AI Chat Panel

- Верх: текущий этап, активная сессия, состояние runtime.
- История: user/assistant/tool-status сообщения.
- Suggested actions: «Применить в артефакт», «Открыть этап», «Показать источники», «Задать уточняющие вопросы», «Проверить качество», «Экспортировать DOCX».
- Preview/diff: целевой артефакт, изменённые поля, новое значение, источник предложения, warnings.
- Кнопка apply активна только для pending proposed patch.

## Context stage

### Что показывать

- Ручной контекст инициативы: описание, цель продукта, домен, владелец процесса, ответственный за Discovery.
- Источники: документы и ссылки со статусами `uploaded`, `indexing`, `ready`, `metadata-only`, `unsupported`, `empty`, `error`.
- Readiness: статус, score, причины блокировки, предупреждения, next actions.
- Coverage: процессы, системы, роли, интеграции, KPI, SLA, BPMN, ограничения.
- Source trace: источник, chunk/reference, confidence, какие поля/артефакты подкрепляет.

### Chat-first рекомендации

- AI Chat предлагает: «обновить контекст», «найти gaps», «подготовить вопросы», «перейти к Problem».
- Если source trace слабый, AI должен предлагать уточнение или новый источник, а не генерировать Problem без предупреждения.
- В central form рядом с readiness показывать короткую причину: что мешает переходу дальше.

## Problem stage

### Что показывать

- Problem statement: ручная формулировка и AI-рекомендованная формулировка.
- Pains: user pains и business pains отдельными списками.
- Root causes: причины, гипотезы, confidence.
- Evidence: ссылки на context source trace.
- Questions: уточняющие вопросы, ответы пользователя, unanswered gaps.

### Chat-first рекомендации

- AI Chat должен уметь предложить problem statement только как preview.
- В diff показывать поля: `problem_statement`, `user_pains`, `business_pains`, `root_causes`, `evidence_signals`.
- Если пользователь отвечает на вопрос в чате, ответ должен отразиться в structured questions/answers.
- Центральная форма должна показывать evidence рядом с каждой pain/root cause, чтобы снизить риск неподтверждённых выводов.

## Goal stage

### Что показывать

- Recommended goal: один основной вариант с объяснением, почему он выбран.
- Альтернативные варианты цели в компактном списке.
- SMART-анализ: Specific, Measurable, Achievable, Relevant, Time-bound.
- KPI: метрика, текущее значение, целевое значение, способ измерения, источник данных.
- Assumptions и constraints.

### Chat-first рекомендации

- AI Chat предлагает goal patch на основе Context + Problem.
- SMART warnings должны быть видны и в панели чата, и в форме.
- KPI без источника данных помечать как assumption.
- Apply patch не должен затирать ручные KPI без preview конфликтов.

## Business Effect stage

### Что показывать

- Qualitative effect: качество, скорость, клиентский опыт, операционная прозрачность.
- Quantitative effect: FTE, time saving, cost impact, revenue impact, risk reduction.
- Metrics: baseline, target, формула, источник данных.
- Open questions: что нужно уточнить для расчёта.

### Chat-first рекомендации

- AI Chat должен различать подтверждённые метрики и гипотезы.
- В форме использовать indicator: `подтверждено источником`, `расчёт`, `допущение`, `нет данных`.
- Если quantitative effect невозможен, AI предлагает список вопросов, а не пустой расчёт.

## Use Cases stage

### Что показывать

- UC cards: actor, goal, trigger, preconditions, main flow, alternative flow, exceptions, postconditions.
- Flows: основной сценарий и отклонения.
- Exceptions: ошибки, edge cases, негативные сценарии.
- Linked requirements: связь UC → FR/NFR.

### Chat-first рекомендации

- AI Chat может генерировать UC cards пачкой, но preview должен показывать каждую карточку отдельно.
- Исключения и negative flows не прятать в текстовом поле; показывать отдельным списком.
- Если UC не связан с requirement, показывать warning `нет связанного требования`.

## Requirements stage

### Что показывать

- FR/NFR table: ID, тип, формулировка, priority, acceptance criteria, source evidence, assumption indicator, linked UC.
- Evidence: source trace или ссылка на Problem/Goal/Use Case.
- Assumption indicator: confirmed, assumption, missing evidence.
- Validation warnings: дубли, неоднозначность, отсутствие acceptance criteria.

### Chat-first рекомендации

- AI Chat предлагает добавление/изменение требований через tabular diff.
- Для каждого требования показывать источник или reason, почему это assumption.
- Apply patch должен сохранять стабильные IDs требований и не пересоздавать всю таблицу без необходимости.

## Final BT stage

### Что показывать

- Document preview: разделы БТ в порядке экспорта.
- Validation warnings: пустые разделы, stale dependencies, missing evidence, unresolved assumptions.
- Export status: DOCX readiness, дата генерации, версия артефактов.
- Export action: «Экспортировать DOCX».

### Chat-first рекомендации

- AI Chat должен уметь собрать Final BT, но перед экспортом показывать validation summary.
- В preview подсвечивать разделы, которые устарели после изменения Context/Goal/Requirements.
- Экспорт разрешать с warnings, но требовать явное подтверждение, если есть blockers.

## Компоненты и visual guidance

- Использовать существующие `ui-card`, `ui-btn`, `ui-badge`, `ui-input`, `ui-textarea`, таблицы и status dots.
- Не использовать hero/marketing layout внутри workspace.
- Карточки применять для повторяемых сущностей: UC card, metric row, warning, proposed patch item.
- Основные формы должны быть плотными, сканируемыми, без декоративных иллюстраций.
- Текст в кнопках короткий; длинные пояснения переносить в helper text.

## Acceptance criteria для реализации

- Chat Panel видна на Project Workspace desktop layout.
- Все этапы остаются доступны через левую навигацию.
- Structured fields не скрыты и не заменены чатом.
- Для AI patch есть preview/diff до apply.
- Apply patch обновляет центральную форму и версию артефакта.
- Warnings/readiness/source trace видны там, где пользователь принимает решение.
- Все user-facing строки на русском языке.

