# DevOS Backend Modules (MVP prototype)

Модульная организация backend по правилам `05A_Architecture_Rules.md`:
каждый модуль отвечает за одну бизнес-область и разделён на слои
domain → application → infrastructure → api.

> Примечание: в MVP-прототипе слои размещены в одном пакете модуля
> (`models/repository = infrastructure+domain storage`, `service = application`,
> `router/schemas = api`). Выделение `module.yaml` и отдельных каталогов
> слоя выполняется при переносе модулей в полный стек платформы.

## projects

- **Ответственность:** жизненный цикл проектов (создание, изменение, архивирование, удаление).
- **Владеет данными:** таблица `project`.
- **API:** `/api/v1/projects`, `/api/v1/projects/{id}`.
- **События:** отложены (ProjectCreated/Updated/Archived/Deleted — при внедрении Event Bus).

## tasks

- **Ответственность:** задачи внутри проекта: статусы, приоритеты.
- **Владеет данными:** таблица `task` (ссылка `project_id`).
- **API:** `/api/v1/tasks`, `/api/v1/tasks/{id}`.
- **Границы:** не обращается к внутренностям Projects — только через `project_id` и публичный сервис Projects для проверки существования.

## documents

- **Ответственность:** документационный контекст проекта: ссылки на Markdown-файлы репозитория, безопасное чтение.
- **Владеет данными:** таблица `document` (ссылка `project_id`, относительный путь).
- **API:** `/api/v1/documents`, `/api/v1/documents/catalog`.
- **Безопасность:** чтение только из разрешённых корней документации (`DOCUMENT_ROOTS`), запрет path traversal, лимит размера, только `.md/.markdown`.

## ai

- **Ответственность:** AI-assisted действия над контекстом проекта: analyze / plan / execute / summarize; сохранение действий и результатов.
- **Владеет данными:** таблицы `ai_action`, `ai_result` (ссылки на project/task).
- **API:** `/api/v1/ai/actions`, `/api/v1/ai/actions/{id}`, `/api/v1/ai/providers`.
- **Провайдеры:** абстракция `AIProvider` (Protocol) + детерминированный `MockAIProvider`. Реальные провайдеры подключаются через реестр без изменения frontend.
- **События:** AIRequestCreated/AIResponseGenerated отложены до Event Bus.

## dashboard

Агрегирующий read-only endpoint `/api/v1/dashboard` для главной панели
(статистика + последние проекты/AI-действия). Собственных данных не владеет.
