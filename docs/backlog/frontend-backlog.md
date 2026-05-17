# Frontend backlog по React frontend

Дата ревизии: 17.05.2026  
Зона ревизии: `discovery-ai-agent/frontend`  
Роль: `ai-frontend-developer`  
Ограничение: backlog описывает только frontend-работы; production-код не менялся.

## Контекст ревизии

Frontend построен на React, Vite и `react-router-dom`. Основные маршруты: главная/дашборд, список проектов, рабочая область проекта, настройки LLM. Рабочая область проекта реализована в `ProjectPage.tsx` с этапами `CONTEXT`, `PROBLEM`, `GOAL`, `BUSINESS_EFFECT`, `AS_IS`, `TO_BE`, `USE_CASES`, `FUNCTIONAL_REQUIREMENTS`, `RISKS`, `FINAL_BT`. Для `CONTEXT`, `PROBLEM`, `GOAL` есть специализированные UI-блоки, для последующих этапов используется общий редактор артефакта. Компоненты `LoadingState`, `ErrorState`, `EmptyState` и часть row/status-компонентов пока являются заглушками.

## Обязательная матрица UX-состояний

Для каждого экрана и ключевого блока должны быть явно реализованы и проверены состояния:

- Загрузка: первичная загрузка данных, выполнение AI-действия, сохранение, экспорт, проверка подключения.
- Ошибка: ошибка backend/API, ошибка генерации, ошибка сохранения, ошибка загрузки/индексации источника.
- Пусто: нет проектов, нет источников, нет извлеченных знаний, нет артефакта этапа, нет результатов проверки.
- Заблокировано: действие недоступно из-за отсутствия проекта, LLM не готова, недостаточен контекст, нет обязательных предыдущих этапов.
- Предупреждение: устаревший зависимый раздел, metadata-only источники, низкая полнота, средняя readiness, неполные SMART/KPI/requirements.
- Готово: данные загружены, артефакт сохранен, контекст/этап готов, экспорт доступен, проверка прошла.

## Эпики и задачи

### FE-BL-001

**ID:** FE-BL-001  
**Название:** Унифицировать базовые UX-состояния frontend  
**Описание:** Создать единый паттерн отображения состояний загрузки, ошибки, пустого экрана, блокировки, предупреждения и готовности на базе существующих UI-компонентов. Сейчас часть состояний разрознена в `ProjectPage.tsx`, а `LoadingState`, `ErrorState`, `EmptyState` являются заглушками.  
**Приоритет:** P0  
**Этап:** Foundation / UI states  
**Зависимости:** текущий `api/client.ts`, `ErrorBoundary`, дизайн-токены, существующие классы `ui-badge`, `ui-card`, `status-dot`.  
**Критерии приемки:**  
- Для `LoadingState`, `ErrorState`, `EmptyState` определены props и визуальные варианты.
- Есть общий способ показать заблокированное действие с причиной и CTA.
- Есть варианты `warning` и `ready` для readiness/status-блоков.
- Компоненты применимы на всех экранах без изменения backend-контрактов.
- Тексты состояний на русском, без технических stack trace для пользователя.
**DoD:** Компоненты покрыты frontend-тестами на рендер состояний, доступны через keyboard navigation, не ломают существующие маршруты и не содержат секретов.  
**Labels:** `frontend`, `ui-state`, `accessibility`, `p0`, `tech-debt`

### FE-BL-002

**ID:** FE-BL-002  
**Название:** Дашборд проекта: рабочий обзор и навигация по discovery  
**Описание:** Доработать экран главной/проектного дашборда так, чтобы пользователь видел активные проекты, прогресс discovery, незаполненные этапы, последние изменения, AI-рекомендации и быстрые действия. Текущий `HomePage.tsx` показывает KPI и быстрые карточки, но нет полноценных состояний ошибки, пусто, загрузки и блокировок действий.  
**Приоритет:** P0  
**Этап:** Дашборд проекта  
**Зависимости:** `GET /projects`, `GET /projects/{id}/completion`, маршруты `/projects`, `/projects/:projectId`, экспорт DOCX.  
**Критерии приемки:**  
- При загрузке проектов и completion отображается loading skeleton.
- При ошибке backend отображается recoverable error с действием повторить.
- При пустом списке проектов отображается empty state с CTA создать проект.
- Быстрые действия блокируются, если нет активного проекта, с понятной причиной.
- Для проектов показаны `готово`, `предупреждение` и `незаполнено` по completion/missing sections.
- Экспорт с дашборда доступен только для проекта с достаточной готовностью или показывает предупреждение.
**DoD:** Проверены сценарии 0 проектов, backend недоступен, проект в работе, проект готов к экспорту; добавлены UI-тесты для ключевых состояний.  
**Labels:** `frontend`, `dashboard`, `routing`, `api-integration`, `p0`

### FE-BL-003

**ID:** FE-BL-003  
**Название:** Контекст: полноценный workspace источников и readiness  
**Описание:** Закрепить экран `CONTEXT` как первый обязательный этап: ручной контекст, загрузка файлов, ссылки, извлеченные знания, покрытие и действия перехода к Problem. Сейчас специализированные карточки уже есть, но нужны единые состояния, retry-flow и более явные блокировки при низкой готовности.  
**Приоритет:** P0  
**Этап:** Контекст  
**Зависимости:** `GET/PUT /projects/{id}/artifacts/CONTEXT`, `POST /projects/{id}/context/sources/upload`, `POST /projects/{id}/context/analyze`, `GET /runtime/status`, `ContextStage`, `KnowledgeSourcesCard`, `KnowledgeCoverageCard`, `AIAssistantCard`.  
**Критерии приемки:**  
- Загрузка: отдельные индикаторы для загрузки артефакта, upload файлов, индексации и autosave.
- Ошибка: файл, ссылка и общий analyze-flow показывают локализованную ошибку и retry.
- Пусто: нет ручного контекста и источников, показан clear empty state.
- Заблокировано: переход к Problem блокируется или требует подтверждения при `readiness.status=blocked`.
- Предупреждение: metadata-only источники, частичное покрытие, устаревшая индексация `requires_update`.
- Готово: `readiness.status=ready`, summary для Problem и source trace видны пользователю.
**DoD:** Проверены форматы файлов, лимит 15 МБ, удаление источников, повторная индексация, autosave без потери введенного текста.  
**Labels:** `frontend`, `context`, `upload`, `readiness`, `source-trace`, `p0`

### FE-BL-004

**ID:** FE-BL-004  
**Название:** Проблема: экран анализа проблемы из контекста  
**Описание:** Доработать этап `PROBLEM`: показать входной контекст, готовность, ручную формулировку, AI-вопросы, ответы пользователя, версии и применение AI patch. В текущем UI есть три колонки, но нужны явные состояния загрузки, stale context, пустого черновика и ошибок AI-действий.  
**Приоритет:** P0  
**Этап:** Проблема  
**Зависимости:** `GET/PUT /projects/{id}/artifacts/PROBLEM`, `GET /projects/{id}/artifacts/CONTEXT`, `POST /projects/{id}/problem/generate`, `POST /projects/{id}/problem/ask`, `POST /projects/{id}/problem/apply-patch`, `POST /projects/{id}/stage/PROBLEM/questions`.  
**Критерии приемки:**  
- Загрузка: генерация проблемы, генерация вопросов и сохранение ответов имеют отдельные progress-состояния.
- Ошибка: AI/LLM/backend ошибки отображаются рядом с действием и не стирают draft.
- Пусто: нет проблемы, показан CTA сгенерировать из контекста или заполнить вручную.
- Заблокировано: генерация заблокирована, если нет готового контекста или LLM не настроена.
- Предупреждение: показано, если версия Context новее `source_context_version`.
- Готово: можно принять проблему как финальную, статус и версия явно отображаются.
**DoD:** Draft не теряется при ошибках, ответы пользователя сохраняются, patch можно применить/отклонить, есть тесты на stale context warning.  
**Labels:** `frontend`, `problem`, `ai-actions`, `state-management`, `p0`

### FE-BL-005

**ID:** FE-BL-005  
**Название:** Цель: SMART-цель, KPI и impact map  
**Описание:** Доработать этап `GOAL`: structured form, метрики успеха, SMART-анализ, AI drafts, AI questions и связи с проблемой/требованиями. Сейчас экран содержит основные поля и AI drafts, но часть AI-действий отключена, а состояния неполноты и блокировок не формализованы.  
**Приоритет:** P0  
**Этап:** Цель  
**Зависимости:** `GET/PUT /projects/{id}/artifacts/GOAL`, `POST /projects/{id}/goal/generate`, `POST /projects/{id}/stage/GOAL/ask`, `POST /projects/{id}/stage/GOAL/apply-patch`, артефакты Context и Problem.  
**Критерии приемки:**  
- Загрузка: генерация цели, сохранение, добавление KPI и AI patch показывают понятный progress.
- Ошибка: ошибки генерации/сохранения не очищают форму.
- Пусто: нет цели, показаны варианты начать вручную или сгенерировать из Context + Problem.
- Заблокировано: генерация цели недоступна без принятой проблемы или готового контекста.
- Предупреждение: SMART-пункты `warning/error`, отсутствующие KPI, противоречия с Problem.
- Готово: цель имеет status `VALIDATED/APPROVED`, KPI заполнены, impact map показывает связи.
**DoD:** Форма валидирует обязательные поля на frontend, зависимости на downstream-этапы помечаются stale после изменения цели, тесты покрывают SMART warning/error.  
**Labels:** `frontend`, `goal`, `smart`, `kpi`, `p0`

### FE-BL-006

**ID:** FE-BL-006  
**Название:** Требования: специализированный экран функциональных требований  
**Описание:** Заменить общий `RichEditor` для `FUNCTIONAL_REQUIREMENTS` на структурированный экран требований: список требований, тип, приоритет, источник, linked goal/problem/use case, статус полноты, AI-проверка. Сейчас этап отображается как общий черновик артефакта.  
**Приоритет:** P1  
**Этап:** Требования  
**Зависимости:** `GET/PUT /projects/{id}/artifacts/FUNCTIONAL_REQUIREMENTS`, `POST /projects/{id}/generate/FUNCTIONAL_REQUIREMENTS`, `POST /projects/{id}/validate`, Goal, Problem, Use Cases.  
**Критерии приемки:**  
- Загрузка: список требований и AI-генерация имеют loading state.
- Ошибка: ошибки генерации/валидации показываются без потери черновика.
- Пусто: показан CTA сгенерировать требования из предыдущих этапов.
- Заблокировано: генерация заблокирована без Goal и Use Cases либо показывает список недостающих зависимостей.
- Предупреждение: требования без источника, без acceptance criteria, дубликаты, конфликтующие формулировки.
- Готово: каждое требование имеет ID, описание, приоритет, источник, acceptance criteria и статус.
**DoD:** Есть frontend-модель requirement item, список поддерживает ручное редактирование, сохранение и проверку полноты; тесты покрывают empty/blocked/warning states.  
**Labels:** `frontend`, `requirements`, `structured-editor`, `validation`, `p1`

### FE-BL-007

**ID:** FE-BL-007  
**Название:** Финальный БТ: сборка, preview и контроль полноты  
**Описание:** Доработать этап `FINAL_BT` как экран сборки финального бизнес-требования: структура документа, preview секций, readiness по зависимостям, список незаполненных разделов, действия генерации, проверки и экспорта. Сейчас есть общий editor и небольшой preview-блок.  
**Приоритет:** P1  
**Этап:** Финальный БТ  
**Зависимости:** `GET/PUT /projects/{id}/artifacts/FINAL_BT`, `POST /projects/{id}/generate/FINAL_BT`, `POST /projects/{id}/validate`, `GET /projects/{id}/completion`, `GET /projects/{id}/export/docx`, все предыдущие артефакты.  
**Критерии приемки:**  
- Загрузка: сборка документа, проверка пустых разделов и экспорт показывают progress.
- Ошибка: ошибка генерации или экспорта отображается с retry и ссылкой на проблемный этап.
- Пусто: нет финального БТ, показан CTA собрать документ.
- Заблокировано: сборка заблокирована, если критичные этапы пустые или stale.
- Предупреждение: показаны stale sections, missing sections, неподтвержденные warning-состояния.
- Готово: preview показывает все секции, экспорт DOCX доступен, completion достаточный.
**DoD:** Пользователь видит, какие этапы попали в БТ и какие исключены; экспорт не открывается молча при ошибке; есть тесты на blocked export и ready export.  
**Labels:** `frontend`, `final-bt`, `export`, `readiness`, `p1`

### FE-BL-008

**ID:** FE-BL-008  
**Название:** Настройки/LLM: безопасная настройка и проверка provider  
**Описание:** Доработать `LLMSettingsPage`: provider presets, base URL, model, api key, timeout, temperature, проверка подключения и статус. Сейчас форма работает, но ключ вводится как обычный input, нет явного loading state и нет блокировки генеративных действий на других экранах через общий статус.  
**Приоритет:** P0  
**Этап:** Настройки/LLM  
**Зависимости:** `GET/PUT /settings/llm`, `POST /settings/llm/test`, `GET /runtime/status`, `StatusIndicator`, frontend safety boundary по secrets.  
**Критерии приемки:**  
- Загрузка: чтение настроек, сохранение и test connection имеют отдельные состояния.
- Ошибка: unauthorized/model_not_found/timeout/backend_error отображаются как понятные сообщения.
- Пусто: для provider без настроек показаны обязательные поля и подсказки.
- Заблокировано: кнопки генерации на discovery-экранах disabled при `ready_for_generation=false`.
- Предупреждение: mock provider и model mismatch помечаются как предупреждение или mock-status.
- Готово: connected provider показывает actual model, latency и masked key tail.
**DoD:** API key не логируется, не отображается полностью и вводится как секретное поле; тесты покрывают статусы connected/mock/error/not_configured.  
**Labels:** `frontend`, `llm-settings`, `security-basics`, `runtime-status`, `p0`

### FE-BL-009

**ID:** FE-BL-009  
**Название:** Трассировка источников и Readiness Center  
**Описание:** Вынести source trace/readiness из отдельных карточек Context в общий экран или панель контроля качества: какие источники использованы, какие этапы зависят от каких версий, где есть metadata-only, stale и blocking reasons. Это нужно для прозрачности генерации и подготовки к QA/release gates.  
**Приоритет:** P1  
**Этап:** Трассировка источников/Readiness  
**Зависимости:** `source_trace`, `readiness`, `pipeline_meta`, `GET /projects/{id}/artifacts`, `GET /projects/{id}/completion`, Context/Problem/Goal/Final BT.  
**Критерии приемки:**  
- Загрузка: readiness center загружает completion, artifacts и pipeline meta с progress state.
- Ошибка: частичная ошибка одного источника не ломает весь экран.
- Пусто: если trace отсутствует, показано, какие действия его сформируют.
- Заблокировано: downstream-этапы показывают blocking dependencies.
- Предупреждение: stale версии, metadata-only, missing information, неполное покрытие.
- Готово: для каждого этапа видны источники, версии, статус и next action.
**DoD:** Пользователь может перейти из warning/blocking reason к нужному этапу; данные не раскрывают приватные endpoints или секреты; тесты покрывают trace empty/partial/ready.  
**Labels:** `frontend`, `source-trace`, `readiness`, `quality-gate`, `p1`

### FE-BL-010

**ID:** FE-BL-010  
**Название:** Экспорт: UX потока DOCX и ошибок скачивания  
**Описание:** Доработать экспорт из списка проектов, дашборда и финального БТ. Сейчас экспорт реализован прямыми ссылками/open window на backend URL; frontend не показывает прогресс, ошибки и ограничения готовности.  
**Приоритет:** P1  
**Этап:** Экспорт  
**Зависимости:** `GET /projects/{id}/export/docx`, `GET /projects/{id}/completion`, `FINAL_BT`, readiness финального документа.  
**Критерии приемки:**  
- Загрузка: при запросе экспорта отображается прогресс подготовки/скачивания.
- Ошибка: ошибка backend или недоступный файл отображается в UI.
- Пусто: если финальный БТ отсутствует, показан CTA собрать документ.
- Заблокировано: экспорт заблокирован при критически неполных этапах.
- Предупреждение: экспорт разрешен с предупреждением при некритичных gaps.
- Готово: файл скачивается, имя файла понятно пользователю, статус экспорта виден.
**DoD:** Экспортный flow проверен из трех точек входа, нет hardcoded backend URL вне API abstraction в новом коде, тесты покрывают blocked/warning/ready export.  
**Labels:** `frontend`, `export`, `docx`, `api-integration`, `p1`

### FE-BL-011

**ID:** FE-BL-011  
**Название:** Общая рабочая область проекта: этапы, stale dependencies и autosave  
**Описание:** Доработать верхнюю часть `ProjectPage`: stage tabs, progress, AI action bar, autosave, save/generate/validate controls, message area. Сейчас логика есть, но state feedback смешан в одном `msg`, а disabled/blocked reasons не всегда видны.  
**Приоритет:** P0  
**Этап:** Общая рабочая область проекта  
**Зависимости:** `ProjectPage.tsx`, `AIActionBar`, `GET /projects/{id}/completion`, `GET /projects/{id}/artifacts`, `pipeline_meta`, `stageOrder`.  
**Критерии приемки:**  
- Загрузка: stage switch и artifact load показывают состояние без мерцания пустого editor.
- Ошибка: ошибка конкретного этапа не ломает весь project shell.
- Пусто: новый этап имеет понятный empty state с next action.
- Заблокировано: AI-действие показывает причину disabled, а не только неактивную кнопку.
- Предупреждение: stale dependencies видны на tab, в header этапа и в action area.
- Готово: сохранение, validation и generated states отображаются отдельно.
**DoD:** `msg` заменен или дополнен структурированным status model, этапы не теряют данные при переключении, тесты покрывают переключение этапов и stale indicator.  
**Labels:** `frontend`, `project-workspace`, `autosave`, `stage-tabs`, `p0`

### FE-BL-012

**ID:** FE-BL-012  
**Название:** Frontend test coverage для discovery workflows  
**Описание:** Добавить тестовое покрытие для экранов и состояний, критичных для frontend discovery workflow. Сейчас в ревизируемом frontend не видно выделенных тестов для routes, API states и component states.  
**Приоритет:** P1  
**Этап:** Frontend tests  
**Зависимости:** выбранный test runner проекта, React Testing Library или аналог, mock API layer для `api/client.ts`, сценарии из FE-BL-001...FE-BL-011.  
**Критерии приемки:**  
- Покрыты route smoke tests: dashboard, projects, project stage, settings/llm.
- Покрыты UX-состояния: loading, error, empty, blocked, warning, ready.
- Покрыты критичные flows: context upload/analyze, problem generate, goal generate, requirements empty/ready, final BT export.
- Моки API не содержат секретов и приватных endpoints.
- Тесты можно запускать локально одной командой.
**DoD:** Тесты входят в frontend quality gate, падение теста указывает на конкретный экран/состояние, документация по запуску добавлена в релевантный frontend README или package scripts в отдельной задаче.  
**Labels:** `frontend`, `tests`, `quality-gate`, `regression`, `p1`

## Handoff

**Assumptions:** backend-контракты остаются совместимыми с текущими вызовами frontend; специализированные экраны для `BUSINESS_EFFECT`, `AS_IS`, `TO_BE`, `USE_CASES`, `RISKS` будут описаны отдельно или расширены из паттерна `FUNCTIONAL_REQUIREMENTS` и `FINAL_BT`.  
**Risks:** часть действий зависит от LLM/runtime readiness; hardcoded backend export URL потребует отдельной frontend/API abstraction задачи; текущий общий `ProjectPage.tsx` уже перегружен состояниями.  
**Open questions:** нужны ли отдельные экранные backlog для Business Effect, AS IS, TO BE, Use Cases и Risks; какой test runner считается стандартом проекта; какие completion thresholds блокируют экспорт.  
**Next quality gate:** перед реализацией задач передать backlog в `ai-ui-ux-designer` для UX-согласования состояний и в `ai-qa-engineer` для детализации тест-кейсов.
