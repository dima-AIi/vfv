# DevOS — MVP Prototype

Рабочий вертикальный срез платформы DevOS: аутентификация и организации (RBAC,
аудит) → CRM (клиенты/компании/контакты/заметки/теги) → проекты (дедлайн,
участники) → рабочее пространство (задачи: исполнитель, дедлайн, комментарии,
вложения; документация: папки, файлы, версии) → AI-assisted действие →
уведомления, глобальный поиск, настройки, журнал аудита → сохранение состояния.

Строится по документации из `00_RESEARCH/` — `99_AI/` (см. `AGENTS.md`).

## Стек

Утверждённый стек (`03_DEVELOPMENT/17_Project_Initialization.md`):
FastAPI · React + Vite + TypeScript · SQLAlchemy 2.x · Alembic · uv · pnpm.

> **Отступление прототипа (требует ратификации владельца):** Docker и
> PostgreSQL недоступны в текущем окружении, поэтому локальное хранилище —
> SQLite через тот же SQLAlchemy/Alembic слой, а файловое хранилище — локальная
> директория за заменяемым протоколом `FileStorage`. Переход на PostgreSQL
> выполняется сменой `DATABASE_URL`, на объектное хранилище — реализацией нового
> провайдера `FileStorage`, без изменения бизнес-кода.

## Требования

- Python 3.12+ и [uv](https://docs.astral.sh/uv/)
- Node.js LTS и pnpm

## Запуск

### 1. Backend

```bash
cd backend
uv sync                        # установить зависимости
cp ../.env.example ../.env     # затем при необходимости отредактировать
uv run alembic upgrade head    # создать схему БД + системный RBAC-seed (SQLite по умолчанию)
uv run uvicorn app.main:app --reload --port 8000
```

Проверка: <http://localhost:8000/api/v1/health>, OpenAPI: <http://localhost:8000/docs>

### 2. Frontend

```bash
cd frontend
pnpm install
pnpm dev        # http://127.0.0.1:5173 (проксирует /api и /docs на :8000)
```

### 3. Регистрация и вход

Регистрация — через UI (`/register`) или `POST /api/v1/auth/register`. Первый
пользователь создаёт организацию через UI (кнопка в топбаре) и автоматически
получает роль `org_admin` в ней. Дальнейшие пользователи добавляются
администратором на экране «Пользователи» (приглашение выдаёт одноразовый
временный пароль).

## Переменные окружения (`.env`, шаблон `.env.example`)

| Переменная | Назначение | По умолчанию |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy async URL | `sqlite+aiosqlite:///devos.db` |
| `SECRET_KEY` | подпись JWT | dev-fallback (обязателен вне local — см. ограничения) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS` | срок токенов | 30 / 7 |
| `STORAGE_DIR` | корень файлового хранилища (вне web-директории) | `<repo>/storage` |
| `FILE_MAX_BYTES` | лимит размера загружаемого файла | 25000000 |
| `AI_PROVIDER` | `mock` \| `anthropic` | `mock` |
| `ANTHROPIC_API_KEY` | ключ реального LLM (пусто → mock) | пусто |
| `CORS_ORIGINS` | разрешённые origin | localhost:5173 |

`.env` не попадает в Git (см. `.gitignore`). Реальные ключи хранить только локально.

## Порты по умолчанию

- Backend (uvicorn): `8000`
- Frontend (vite dev): `5173` (прокси `/api`, `/docs`, `/openapi.json` → `:8000`)
- Проверочные прогоны/демо агента: `:8041+` (backend) и `:5274+` (vite preview)
  на собственной temp-БД и temp `STORAGE_DIR`, чтобы не мешать запущенным
  серверам владельца.

## Пользовательский сценарий (MVP flow)

1. Регистрация → вход → создание организации → роль `org_admin`.
2. Пользователи — пригласить коллег, назначать роли, блокировать/разблокировать.
3. CRM — создать клиента, теги/заметки/контакты/компанию, поиск, архив/восстановление.
4. Projects — создать проект (дедлайн, участники), связать с клиентом.
5. Workspace → Tasks — задачи: исполнитель, дедлайн, статус, комментарии, вложения.
6. Workspace → Documentation — папки, markdown-контекст репозитория, загрузка файлов (версии).
7. AI Assistant — analyze / plan / execute / summarize (mock-провайдер), история сохраняется.
8. Уведомления (колокольчик), глобальный поиск, Настройки, Аудит, Dashboard.

## Проверки (quality gates)

```bash
# backend
cd backend
uv run pytest -q                 # unit/integration/API/регрессия
uv run ruff check .
uv run mypy app
uv run alembic heads             # ровно одна head-ревизия

# frontend
cd frontend
pnpm exec prettier --check .
pnpm exec tsc -b
pnpm exec oxlint
pnpm exec vite build

# формальная приёмка MVP (§13) против запущенного backend на своей temp-БД:
cd backend
$env:DATABASE_URL="sqlite+aiosqlite:///<temp>/acceptance.db"
$env:STORAGE_DIR="<temp>/acceptance_storage"
uv run alembic upgrade head
uv run uvicorn app.main:app --host 127.0.0.1 --port 8041
uv run python ../scripts/acceptance_check.py   # exit!=0 при любом FAIL
```

## Структура

```
backend/
  app/core/           конфигурация, БД, ошибки, конверты, события (диспетчер), аудит, поиск
  app/modules/        identity · organizations · rbac · projects · tasks · documents ·
                      files · crm · comments · notifications · search · settings ·
                      audit · ai · dashboard
  migrations/         Alembic
  tests/              pytest
frontend/
  src/pages/          Dashboard, Projects, ProjectWorkspace, AIWorkspace, Crm,
                      CustomerDetail, Notifications, Settings, Users, Audit, Login, Register
  src/features/       workspace, documents, ai, auth
  src/layout/         AppLayout (сайдбар, топбар: поиск/колокольчик/профиль)
  src/shared/         api-клиент, типы контрактов, UI-примитивы, breadcrumbs
scripts/
  acceptance_check.py формальная приёмка §13 (HTTP-сценарий, ненулевой exit при FAIL)
  e2e_smoke.py        сквозной дым-сценарий через реальные серверы
  seed_demo.py        демо-данные
```

## Известные ограничения прототипа

- **Хранилище/БД:** SQLite и локальная ФС вместо PostgreSQL/Docker (ратификация
  владельца; переход — сменой `DATABASE_URL` / новым `FileStorage`).
- **AI:** работает через mock-провайдер без внешних вызовов; реальный LLM
  подключается через реестр провайдеров (`app/modules/ai/registry.py`) и
  `AI_PROVIDER=anthropic` + `ANTHROPIC_API_KEY`.
- **SECRET_KEY:** имеет dev-fallback для локального запуска; вне `local` обязан
  задаваться явно (жёсткая проверка — backlog).
- **События:** in-process диспетчер с дедупликацией по `eventId`; dead-letter
  queue, персистентность событий и сквозной `correlationId` — backlog.
- **Уведомления:** только in-app; email/webhook-каналы — будущие этапы.
- **Frontend-бандл:** единый чанк >500 kB (code-splitting — backlog).
