# 17_Project_Initialization.md

**Status:** Draft

**Version:** 2.0

**Category:** Development

---

## Purpose

Настоящий документ описывает полный процесс инициализации проекта DevOS.

После выполнения всех шагов разработчик получает полностью подготовленную инженерную среду, соответствующую архитектуре платформы.

Документ используется один раз — при создании нового проекта или настройке нового рабочего окружения.

Он определяет:

- создание Git-репозитория;
- структуру каталогов;
- выбор технологий;
- настройку окружения;
- подготовку Backend;
- подготовку Frontend;
- подготовку базы данных;
- настройку Docker;
- настройку контроля качества кода;
- первый запуск проекта.

---

## 1. Initialization Goals

После завершения всех шагов должны быть достигнуты следующие результаты:

- создан Git Repository;
- подготовлена структура каталогов;
- документация подключена к проекту;
- Backend запускается;
- Frontend запускается;
- PostgreSQL подключена;
- Docker полностью настроен;
- система миграций работает;
- настроены инструменты контроля качества;
- проект готов к реализации MVP.

---

## 2. Technology Decisions

Настоящий раздел фиксирует официальный стек технологий DevOS.

Изменение технологий допускается только после архитектурного согласования.

| Категория | Технология | Причина выбора |
|------------|------------|----------------|
| Backend | FastAPI | Высокая производительность, отличная поддержка OpenAPI |
| Frontend | React + Vite + TypeScript | Современный стек с высокой скоростью разработки |
| Database | PostgreSQL | Надёжная промышленная СУБД |
| ORM | SQLAlchemy 2.x | Гибкость и зрелость экосистемы |
| Migrations | Alembic | Стандарт миграций SQLAlchemy |
| Python Package Manager | uv | Высокая скорость работы |
| Node Package Manager | pnpm | Быстрая и эффективная работа с зависимостями |
| Containers | Docker + Docker Compose | Единое окружение разработки |
| Version Control | Git + GitHub | Совместная разработка и CI/CD |
| IDE | Visual Studio Code | Основная среда разработки |
| AI Assistant | Совместимый AI coding agent | Реализация задач по `AGENTS.md` и профильной документации |

---

## Technology Principles

При выборе технологий DevOS используются следующие критерии:

- долгосрочная поддержка;
- высокая производительность;
- зрелость сообщества;
- совместимость между компонентами;
- минимальное количество лишних зависимостей.

Все последующие инженерные решения должны соответствовать данным принципам.

## 3. Prerequisites

Перед началом инициализации проекта необходимо установить все обязательные инструменты разработки.

Работа без полного набора инструментов не поддерживается.

---

## Operating System

Рекомендуемые операционные системы:

- Windows 11
- macOS (последняя стабильная версия)
- Ubuntu LTS

---

## Required Software

Перед началом работы должны быть установлены следующие программы.

| Инструмент | Назначение |
|------------|------------|
| Git | Контроль версий |
| Docker Desktop | Контейнеризация |
| Python 3.12+ | Backend |
| Node.js LTS | Frontend |
| pnpm | Менеджер пакетов Frontend |
| uv | Менеджер пакетов Python |
| Visual Studio Code | Основная IDE |
| Совместимый AI coding agent | AI-разработка |

---

## Git

Проверка установки:

```bash
git --version
```

Ожидаемый результат:

```text
git version 2.x.x
```

---

## Docker

Проверка установки:

```bash
docker --version

docker compose version
```

Docker Desktop должен быть запущен.

---

## Python

Проверка установки:

```bash
python --version
```

или

```bash
python3 --version
```

Минимальная версия:

```text
Python 3.12
```

---

## uv

Проверка установки:

```bash
uv --version
```

Если uv отсутствует, его необходимо установить до начала работы.

---

## Node.js

Проверка:

```bash
node --version
```

Минимальная версия:

```text
LTS
```

---

## pnpm

Проверка:

```bash
pnpm --version
```

---

## Visual Studio Code

Необходимо установить:

- Python Extension
- Docker Extension
- ESLint
- Prettier
- GitHub Pull Requests
- GitLens

---

## AI coding agent

Используемый AI coding agent должен быть установлен, настроен и иметь доступ к локальному проекту в пределах задачи владельца.

DevOS не зависит от конкретного AI-инструмента. Обязательный порядок работы задаётся корневым `AGENTS.md`, контекстным слоем `99_AI` и профильными документами-владельцами.

---

## 4. Repository Preparation

DevOS уже существует как локальный проект. Репозиторий подготавливается по local-first сценарию без клонирования и без изменения физической структуры документации.

### Repository Root

Официальный корень будущего Git-репозитория:

```text
D:\Project_Zero\DevOS
```

Родительский каталог `D:\Project_Zero` не должен становиться Git-репозиторием DevOS.

### Approved sequence

Операции выполняются только в отдельной задаче владельца и в следующем порядке:

1. пройти pre-Git gate;
2. выполнить локальный `git init -b main` в корне DevOS;
3. проверить состав файлов и создать первый локальный commit;
4. создать пустой приватный GitHub-репозиторий без README, license и `.gitignore`;
5. подключить SSH remote `origin`;
6. отправить `main`;
7. создать `develop` от `main` и отправить её после проверки.

Команды в этом документе являются инструкцией, а не разрешением выполнить их в рамках документационной задачи.

### Local initialization command

```bash
git init -b main
```

Перед выполнением необходимо повторно подтвердить текущий каталог и отсутствие `.git` в DevOS и родительском каталоге.

### Private GitHub repository

GitHub-репозиторий создаётся приватным и пустым. Clone-first сценарий к существующему локальному проекту DevOS не применяется.

### SSH remote

После создания удалённого репозитория подключается SSH remote:

```bash
git remote add origin git@github.com:<owner>/DevOS.git
```

Фактический владелец и точное имя репозитория подтверждаются человеком перед выполнением команды.


## 5. Project Folder Structure

Документация DevOS уже размещена в корне проекта. При последующей инициализации приложений эта структура сохраняется.

```text
DevOS/
├── AGENTS.md
├── 00_RESEARCH/
├── 01_ARCHITECTURE/
├── 02_PRODUCT/
├── 03_DEVELOPMENT/
├── 04_PROJECT/
├── 99_AI/
├── apps/
├── backend/
├── frontend/
├── packages/
├── infrastructure/
├── scripts/
└── .github/
```

Каталоги приложений, инфраструктуры и GitHub-конфигурации создаются только в рамках отдельной задачи bootstrap. Настоящий документ не требует создавать их на этапе подготовки документации.

---

## Folder Description

### `AGENTS.md`

Единственный операционный регламент AI в корне проекта.

### `00_RESEARCH/` — `04_PROJECT/`

Официальные исследовательские, архитектурные, продуктовые, development- и project-документы DevOS.

### `99_AI/`

Навигационный и контекстный слой AI.

### `apps/`

Точки входа пользовательских приложений.

### `backend/`

Исходный код Backend на FastAPI.

### `frontend/`

React-приложение.

### `packages/`

Общие библиотеки платформы.

### `infrastructure/`

Контейнеры, PostgreSQL, deployment и Infrastructure as Code.

### `scripts/`

Вспомогательные скрипты проекта.

### `.github/`

GitHub Actions, Issue Templates, Pull Request Templates и CI/CD.

---

## 6. Documentation Placement

Документационные каталоги располагаются непосредственно в корне `D:\Project_Zero\DevOS` рядом с `AGENTS.md`.

Каталог `docs/` для текущего репозитория не используется. Перенос документации в `docs/` не является частью инициализации.

Официальная структура:

```text
DevOS/
├── AGENTS.md
├── 00_RESEARCH/
├── 01_ARCHITECTURE/
├── 02_PRODUCT/
├── 03_DEVELOPMENT/
├── 04_PROJECT/
└── 99_AI/
```

Документы сохраняют существующие относительные пути. Любое будущее изменение физического размещения требует отдельного решения владельца проекта и синхронного обновления ссылок.

---

## 7. Backend Bootstrap

Backend DevOS строится на основе FastAPI.

Все Python-зависимости управляются через **uv**.

---

## Backend Directory

Создать каталог:

```text
backend/
```

Структура Backend будет развиваться постепенно, однако базовая структура должна быть подготовлена сразу.

---

## Initialize Python Project

Перейти в каталог Backend.

```bash
cd backend
```

Создать проект:

```bash
uv init
```

---

## Install Core Dependencies

Установить основные библиотеки проекта.

```bash
uv add fastapi
uv add uvicorn
uv add sqlalchemy
uv add alembic
uv add pydantic
uv add pydantic-settings
uv add asyncpg
uv add python-jose
uv add passlib[bcrypt]
uv add python-multipart
```

---

## Development Dependencies

Установить инструменты разработки.

```bash
uv add --dev ruff
uv add --dev mypy
uv add --dev pytest
uv add --dev pytest-asyncio
```

---

## Backend Structure

После инициализации структура Backend должна иметь следующий вид.

```text
backend/

├── app/
│
├── tests/
│
├── migrations/
│
├── pyproject.toml
│
└── uv.lock
```

---

## Backend Principles

Backend должен соответствовать следующим требованиям.

- только Python 3.12+
- только SQLAlchemy 2.x
- асинхронная работа с БД
- строгая типизация
- отсутствие глобального состояния
- модульная архитектура

---

## 8. Frontend Bootstrap

Frontend DevOS строится на основе React.

---

## Frontend Directory

Создать каталог:

```text
frontend/
```

---

## Create Application

Перейти в каталог проекта.

```bash
cd frontend
```

Создать приложение.

```bash
pnpm create vite . --template react-ts
```

---

## Install Dependencies

Установить основные библиотеки.

```bash
pnpm install
```

Дополнительные зависимости.

```bash
pnpm add react-router-dom

pnpm add axios

pnpm add zod

pnpm add @tanstack/react-query

pnpm add clsx
```

---

## Development Dependencies

```bash
pnpm add -D eslint

pnpm add -D prettier

pnpm add -D typescript
```

---

## Frontend Structure

Базовая структура.

```text
frontend/

├── public/

├── src/

├── package.json

├── vite.config.ts

└── tsconfig.json
```

---

## Frontend Principles

Frontend должен использовать:

- React
- TypeScript
- Vite
- React Query
- React Router

Любая бизнес-логика должна находиться в Backend.

Frontend отвечает только за пользовательский интерфейс.

---

## 9. Database Bootstrap

Официальной СУБД DevOS является PostgreSQL.

---

## Database Engine

Используется:

```text
PostgreSQL
```

---

## ORM

Используется:

```text
SQLAlchemy 2.x
```

---

## Migration System

Используется:

```text
Alembic
```

---

## Initialize Alembic

В каталоге Backend выполнить.

```bash
alembic init migrations
```

---

## Database Principles

Все изменения структуры базы данных выполняются исключительно через миграции.

Запрещается:

- изменять таблицы вручную;
- редактировать БД напрямую;
- создавать таблицы без миграций.

---

## 10. Docker Bootstrap

Все основные сервисы платформы запускаются через Docker Compose.

---

## Infrastructure Directory

Создать каталог.

```text
infrastructure/
```

---

## docker-compose.yml

На первом этапе создаётся единый файл.

```text
docker-compose.yml
```

---

## Initial Containers

Минимальный набор контейнеров.

| Контейнер | Назначение |
|------------|------------|
| backend | FastAPI |
| frontend | React |
| postgres | PostgreSQL |

---

## Docker Principles

Все сервисы проекта должны запускаться одной командой.

```bash
docker compose up
```

Локальная разработка без Docker не является основной конфигурацией проекта.

## 11. Environment Configuration

Все конфигурационные параметры платформы должны храниться во внешних переменных окружения.

Конфигурация не должна быть захардкожена в исходном коде.

---

## Environment Files

В корне проекта создаются следующие файлы.

```text
.env

.env.example
```

---

## Environment Principles

Файл `.env` используется только локально.

Файл `.env.example` содержит шаблон всех необходимых переменных без конфиденциальных данных.

---

## Configuration Categories

Переменные окружения группируются по категориям.

### Application

```text
APP_NAME

APP_ENV

APP_VERSION
```

---

### Database

```text
POSTGRES_HOST

POSTGRES_PORT

POSTGRES_DB

POSTGRES_USER

POSTGRES_PASSWORD
```

---

### Backend

```text
SECRET_KEY

ACCESS_TOKEN_EXPIRE_MINUTES

REFRESH_TOKEN_EXPIRE_DAYS
```

---

### Frontend

```text
VITE_API_URL
```

---

### AI

```text
ANTHROPIC_API_KEY
```

---

## Security Rules

Запрещается:

- хранить секретные ключи в Git;
- публиковать файл `.env`;
- использовать реальные ключи в документации.

---

## 12. Git Configuration

DevOS использует Git как единственную систему контроля версий.

---

## Branch Strategy

Используются следующие основные ветки.

```text
main

develop

feature/*
```

---

### main

Содержит только стабильные версии проекта.

---

### develop

Основная ветка разработки.

---

### feature/*

Каждая новая функциональность реализуется в отдельной ветке от `develop`.

Пример.

```text
feature/auth

feature/projects

feature/tasks
```

---

## Commit Principles

Каждый commit должен быть:

- небольшим;
- логически завершённым;
- понятным без дополнительного контекста.

---

## Commit Message Style

Рекомендуемый формат.

```text
type(scope): description
```

Примеры.

```text
feat(identity): add JWT authentication

fix(tasks): resolve status update bug

docs(api): update endpoint specification
```

---

## Git Ignore

В проекте обязательно используется файл:

```text
.gitignore
```

Он должен исключать:

- виртуальные окружения;
- временные файлы;
- логи;
- локальные настройки IDE;
- файл `.env`.

---

## 13. Code Quality

Перед началом разработки должны быть подключены инструменты контроля качества.

---

## Backend

Используются.

- Ruff
- MyPy
- Pytest

---

## Frontend

Используются.

- ESLint
- Prettier
- TypeScript

---

## General Principles

Код должен соответствовать следующим требованиям.

- единый стиль оформления;
- строгая типизация;
- отсутствие неиспользуемого кода;
- отсутствие предупреждений линтера;
- успешное прохождение тестов.

---

## Quality Gate

Ни один commit не должен нарушать правила качества проекта.

Исправление ошибок качества имеет более высокий приоритет, чем добавление новой функциональности.

## 14. First Run

После завершения настройки инфраструктуры необходимо убедиться, что все компоненты проекта работают корректно.

---

## Backend Startup

Запустить Backend.

```bash
cd backend

uv run uvicorn app.main:app --reload
```

Проверить:

- приложение успешно запускается;
- отсутствуют ошибки импорта;
- OpenAPI доступен;
- Swagger UI открывается.

---

## Frontend Startup

Запустить Frontend.

```bash
cd frontend

pnpm dev
```

Проверить:

- приложение запускается;
- отсутствуют ошибки TypeScript;
- страница успешно открывается в браузере.

---

## Docker Startup

Запустить инфраструктуру.

```bash
docker compose up
```

Проверить:

- Backend запущен;
- Frontend запущен;
- PostgreSQL успешно стартовала;
- отсутствуют ошибки контейнеров.

---

## Database Connection

Проверить:

- соединение с PostgreSQL успешно устанавливается;
- приложение получает доступ к базе данных;
- миграции выполняются без ошибок.

---

## Migration Check

Создать тестовую миграцию.

```bash
alembic revision --autogenerate -m "initial"
```

После этого выполнить.

```bash
alembic upgrade head
```

Проверить:

- база успешно обновилась;
- ошибок миграции нет.

---

## API Check

Открыть документацию OpenAPI.

```text
http://localhost:8000/docs
```

Проверить:

- Swagger UI открывается;
- все зарегистрированные маршруты отображаются корректно.

---

## 15. First Commit

После успешного запуска всех компонентов необходимо создать первый commit проекта.

---

## Initial Commit

Рекомендуемое сообщение.

```text
chore(init): bootstrap DevOS project
```

или

```text
Initial DevOS bootstrap
```

---

## Repository State

После первого commit репозиторий должен содержать:

- структуру каталогов;
- Backend;
- Frontend;
- Docker;
- документацию;
- базовую конфигурацию проекта.

Без реализации бизнес-логики.

---

## 16. Ready Checklist

Перед переходом к разработке MVP необходимо убедиться, что проект полностью подготовлен.

## Infrastructure

- [ ] Git Repository создан
- [ ] Docker установлен
- [ ] Docker Compose работает
- [ ] PostgreSQL запускается

---

## Backend

- [ ] FastAPI запускается
- [ ] OpenAPI доступен
- [ ] SQLAlchemy подключён
- [ ] Alembic работает

---

## Frontend

- [ ] React запускается
- [ ] TypeScript работает
- [ ] Vite работает

---

## Environment

- [ ] `.env` создан
- [ ] `.env.example` создан
- [ ] секретные ключи не попадают в Git

---

## Documentation

- [ ] Документация размещена в корневых каталогах `00_RESEARCH/` — `99_AI/`
- [ ] Корневой `AGENTS.md` доступен
- [ ] Архитектурные документы актуальны
- [ ] AI Layer подключён

---

## Quality

- [ ] Ruff настроен
- [ ] MyPy настроен
- [ ] ESLint настроен
- [ ] Prettier настроен

---

## Version Control

- [ ] Первый commit выполнен
- [ ] Ветки `main` и `develop` созданы
- [ ] SSH remote `origin` подключён
- [ ] Репозиторий готов к разработке

---

## 17. Development Entry Point

После выполнения настоящего документа проект считается полностью подготовленным к разработке.

Дальнейшая работа должна выполняться в следующем порядке.

```text
Project Initialization

↓

Development Workflow

↓

AI Development Guide

↓

Core Modules

↓

Module Specification

↓

Implementation

↓

Testing

↓

Documentation Update

↓

Commit
```

Настоящий порядок является официальным процессом разработки DevOS.

---

## 18. Related Documents

Настоящий документ связан со следующими разделами документации.

- `15_Development_Workflow.md`
- `16_AI_Development_Guide.md`
- `05_Core_Modules.md`
- `06_System_Design.md`
- `07_Module_Specification.md`
- `08_Database_Design.md`
- `09_API_Design.md`
- `11_Security_Model.md`
- `99_AI/04_QUICK_START.md`

---

## 19. Final Statement

`17_Project_Initialization.md` завершает этап подготовки проекта DevOS.

После выполнения всех рекомендаций настоящего документа разработчик получает полностью готовую инженерную среду, соответствующую архитектуре платформы.

Дальнейшая разработка должна выполняться исключительно в соответствии с архитектурной документацией DevOS.

Любые отклонения от утверждённой структуры проекта, технологического стека или процесса разработки допускаются только после архитектурного согласования.

Настоящий документ является официальной точкой перехода от этапа проектирования к этапу реализации платформы.
