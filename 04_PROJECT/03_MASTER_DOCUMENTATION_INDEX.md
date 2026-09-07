# 03_MASTER_DOCUMENTATION_INDEX.md

**Status:** Draft

**Version:** 2.0

**Category:** Project

## Purpose

Master Documentation Index — официальный реестр документации DevOS. Он фиксирует фактический состав, относительные пути, текущие lifecycle-статусы, версии и назначение документов.

Реестр не заменяет документы-владельцы, не устанавливает отдельную Documentation Priority и не является операционным регламентом AI. Единственный операционный регламент AI — корневой `AGENTS.md`.

Все пути ниже указаны относительно корня проекта `D:\Project_Zero\DevOS`.

## 1. Lifecycle statuses

Для официальных документов допустимы следующие lifecycle-статусы:

- `Draft` — документ разрабатывается;
- `Review` — документ подготовлен и проходит проверку;
- `Approved` — документ утверждён владельцем;
- `Deprecated` — документ выведен из активного использования, но сохранён для совместимости;
- `Archived` — документ хранится только как исторический материал и не изменяется.

Статус не включает номер версии. Версия указывается отдельно в поле `Version`.

Статус `Active` не входит в этот lifecycle. Он временно сохранён у `04_PROJECT/18_Developer_Workstation.md` до отдельного решения владельца; это несоответствие явно отмечено в реестре и не должно исправляться автоматическим массовым утверждением.

## 2. Documentation registry

Существующие ID сохранены. Новые ID добавлены только для ранее незарегистрированных документов; пропуски и историческая нумерация не исправлялись.

### Research

| ID | Path | Status | Version | Purpose |
|---|---|---:|---:|---|
| RES-001 | `00_RESEARCH/00_RESEARCH_METHOD.md` | Review | 1.0 | Методика и стандарт проведения исследований |
| RES-002 | `00_RESEARCH/00A_DATA_SOURCES.md` | Review | 1.0 | Реестр и правила использования источников данных |
| RES-003 | `00_RESEARCH/01_Market_Research.md` | Draft | 1.0 | Исследование рынка |
| RES-004 | `00_RESEARCH/02_Client_Research.md` | Draft | 1.0 | Исследование клиентских сегментов и проблем |
| RES-005 | `00_RESEARCH/03_Competitor_Research.md` | Draft | 1.0 | Исследование конкурентной среды |
| RES-006 | `00_RESEARCH/04_SaaS_Research.md` | Draft | 1.0 | Исследование SaaS-моделей и практик |

### Architecture

| ID | Path | Status | Version | Purpose |
|---|---|---:|---:|---|
| ARC-001 | `01_ARCHITECTURE/05_Core_Modules.md` | Draft | 2.0 | Состав и ответственность основных модулей |
| ARC-002 | `01_ARCHITECTURE/05_DevOS_Architecture_Foundation.md` | Draft | 1.1 | Архитектурный фундамент DevOS |
| ARC-003 | `01_ARCHITECTURE/05A_Architecture_Rules.md` | Draft | 1.1 | Обязательные архитектурные правила |
| ARC-004 | `01_ARCHITECTURE/05B_Platform_Reference.md` | Draft | 1.0 | Справочная модель платформы |
| ARC-005 | `01_ARCHITECTURE/06_System_Design.md` | Draft | 1.1 | Системный дизайн и границы компонентов |
| ARC-006 | `01_ARCHITECTURE/07_Module_Specification.md` | Draft | 1.0 | Нормативная спецификация модулей |
| ARC-007 | `01_ARCHITECTURE/08_Database_Design.md` | Draft | 1.0 | Модель и правила проектирования данных |
| ARC-008 | `01_ARCHITECTURE/09_API_Design.md` | Draft | 1.0 | Правила и контракты API |
| ARC-009 | `01_ARCHITECTURE/10_Event_Architecture.md` | Draft | 1.0 | Событийная архитектура |
| ARC-010 | `01_ARCHITECTURE/11_Security_Model.md` | Draft | 1.1 | Модель безопасности DevOS |

### Product

| ID | Path | Status | Version | Purpose |
|---|---|---:|---:|---|
| PRD-001 | `02_PRODUCT/12_Product_Roadmap.md` | Draft | 1.0 | Продуктовая дорожная карта |
| PRD-002 | `02_PRODUCT/13_MVP_Specification.md` | Draft | 1.0 | Границы и требования MVP |
| PRD-003 | `02_PRODUCT/14_UI_UX_System.md` | Draft | 1.0 | UI/UX-система продукта |

### Development

| ID | Path | Status | Version | Purpose |
|---|---|---:|---:|---|
| DEV-001 | `03_DEVELOPMENT/15_Development_Workflow.md` | Draft | 1.1 | Git workflow и процесс разработки |
| DEV-002 | `03_DEVELOPMENT/16_AI_Development_Guide.md` | Draft | 2.0 | Правила постановки, выполнения и review задач AI |
| DEV-003 | `03_DEVELOPMENT/17_Project_Initialization.md` | Draft | 2.0 | Local-first инициализация проекта и подключение remote |

### Project

| ID | Path | Status | Version | Purpose |
|---|---|---:|---:|---|
| AI-003 | `04_PROJECT/03_MASTER_DOCUMENTATION_INDEX.md` | Draft | 2.0 | Полный реестр официальной документации |
| PRJ-001 | `04_PROJECT/04_DOCUMENTATION_STANDARDS.md` | Draft | 1.0 | Стандарты структуры и сопровождения документации |
| PRJ-002 | `04_PROJECT/18_Developer_Workstation.md` | Active* | 1.1 | Требования и процедуры рабочей станции разработчика |

### AI Context Layer

| ID | Path | Status | Version | Purpose |
|---|---|---:|---:|---|
| AI-000 | `99_AI/00_CLAUDE.md` | Deprecated | 2.0 | Compatibility artifact: перенаправляет старые ссылки к `AGENTS.md`, не является точкой входа |
| AI-001 | `99_AI/01_PROJECT_CONTEXT.md` | Approved | 2.1 | Краткий фактический контекст проекта |
| AI-002 | `99_AI/02_ARCHITECTURE_INDEX.md` | Approved | 2.0 | Маршрутизатор к профильным документам-владельцам |
| AI-004 | `99_AI/03_GLOSSARY.md` | Draft | 1.0 | Единая терминология DevOS |
| AI-005 | `99_AI/04_QUICK_START.md` | Approved | 2.0 | Короткий навигационный сценарий первого входа |

`Active*` означает фактический текущий статус, который не входит в установленный lifecycle и требует решения владельца. Для `04_PROJECT/18_Developer_Workstation.md` рекомендован `Approved` после содержательного review владельцем.

## 3. Operational artifact

`AGENTS.md` учитывается отдельно от реестра обычных документов:

| ID | Path | Role |
|---|---|---|
| OPS-001 | `AGENTS.md` | Единственный операционный регламент AI и обязательная точка входа |

К `AGENTS.md` не применяется нормализация метаданных обычного документа. Его положения направляют AI к контекстному слою и профильным документам-владельцам, но не заменяют архитектуру, продуктовые спецификации или инженерные документы.

## 4. Context and ownership model

Канонический маршрут AI:

```text
AGENTS.md
  ↓
99_AI/01_PROJECT_CONTEXT.md
  ↓
99_AI/02_ARCHITECTURE_INDEX.md
  ↓
99_AI/03_GLOSSARY.md — при необходимости
  ↓
профильный документ-владелец
```

`99_AI/04_QUICK_START.md` — краткая навигационная памятка. `99_AI/00_CLAUDE.md` находится вне обязательного маршрута и существует только для совместимости.

Решения определяются профильными документами-владельцами. При конфликте, неоднозначности или отсутствии требования применяется порядок действий из `AGENTS.md`; реестр сам конфликт не разрешает.

## 5. Registry maintenance rules

- Каждый официальный документ регистрируется один раз с фактическими путём, статусом и версией.
- Изменение имени или пути одновременно отражается в реестре и подтверждённых ссылках.
- Изменение версии отражается после логически завершённого изменения документа.
- Lifecycle-статус меняется только на основании фактической стадии и, для `Approved`, решения владельца.
- Существующие ID не перенумеровываются автоматически из-за пропусков.
- Исторические, шаблонные и неоднозначные упоминания имён файлов не создают новые документы автоматически.

## Final statement

Реестр отражает полный фактический состав официальной документации DevOS на подготовительном этапе. Его актуальность подтверждается только совместной проверкой файловой структуры, метаданных и ссылок.
