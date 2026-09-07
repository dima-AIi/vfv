# 02_ARCHITECTURE_INDEX.md

**Status:** Approved

**Version:** 2.0

**Category:** AI Bootstrap

## Purpose

Architecture Index — маршрутизатор по документации DevOS.

Он помогает определить профильный документ-владелец для конкретной задачи, но не содержит самостоятельных архитектурных, продуктовых или процессных решений. Индекс не разрешает конфликты между документами и не заменяет корневой [`AGENTS.md`](../AGENTS.md).

## 1. Канонический маршрут

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

`AGENTS.md` является единственным операционным регламентом AI. Настоящий индекс используется только для навигации.

## 2. Структура документации

| Каталог | Ответственность |
|---|---|
| `00_RESEARCH/` | Методология, источники, факты, исследования и происхождение решений |
| `01_ARCHITECTURE/` | Архитектурный фундамент, модули, System Design, данные, API, события и безопасность |
| `02_PRODUCT/` | Product Roadmap, MVP и UI/UX |
| `03_DEVELOPMENT/` | Процесс разработки, правила работы AI и инициализация проекта |
| `04_PROJECT/` | Реестр, стандарты документации и рабочее окружение |
| `99_AI/` | Краткий контекст, навигация и терминология |

## 3. Маршрутизация по области

| Область | Профильный документ-владелец | Связанные документы при необходимости |
|---|---|---|
| Архитектурные ограничения | [`01_ARCHITECTURE/05A_Architecture_Rules.md`](../01_ARCHITECTURE/05A_Architecture_Rules.md) | `05_DevOS_Architecture_Foundation.md`, `05B_Platform_Reference.md` |
| Архитектурный фундамент | [`01_ARCHITECTURE/05_DevOS_Architecture_Foundation.md`](../01_ARCHITECTURE/05_DevOS_Architecture_Foundation.md) | `05A_Architecture_Rules.md`, `06_System_Design.md` |
| Каталог модулей | [`01_ARCHITECTURE/05_Core_Modules.md`](../01_ARCHITECTURE/05_Core_Modules.md) | `07_Module_Specification.md` |
| Обзор платформы | [`01_ARCHITECTURE/05B_Platform_Reference.md`](../01_ARCHITECTURE/05B_Platform_Reference.md) | `05_DevOS_Architecture_Foundation.md`, `06_System_Design.md` |
| Системное устройство | [`01_ARCHITECTURE/06_System_Design.md`](../01_ARCHITECTURE/06_System_Design.md) | `05A_Architecture_Rules.md`, `07_Module_Specification.md` |
| Границы и устройство модулей | [`01_ARCHITECTURE/07_Module_Specification.md`](../01_ARCHITECTURE/07_Module_Specification.md) | `05_Core_Modules.md`, `06_System_Design.md` |
| Данные и миграции | [`01_ARCHITECTURE/08_Database_Design.md`](../01_ARCHITECTURE/08_Database_Design.md) | `07_Module_Specification.md`, `11_Security_Model.md` |
| API | [`01_ARCHITECTURE/09_API_Design.md`](../01_ARCHITECTURE/09_API_Design.md) | `07_Module_Specification.md`, `08_Database_Design.md`, `11_Security_Model.md` |
| События | [`01_ARCHITECTURE/10_Event_Architecture.md`](../01_ARCHITECTURE/10_Event_Architecture.md) | `07_Module_Specification.md`, `09_API_Design.md` |
| Безопасность | [`01_ARCHITECTURE/11_Security_Model.md`](../01_ARCHITECTURE/11_Security_Model.md) | `08_Database_Design.md`, `09_API_Design.md` |
| Этапы продукта | [`02_PRODUCT/12_Product_Roadmap.md`](../02_PRODUCT/12_Product_Roadmap.md) | `13_MVP_Specification.md` |
| Состав и границы MVP | [`02_PRODUCT/13_MVP_Specification.md`](../02_PRODUCT/13_MVP_Specification.md) | `12_Product_Roadmap.md`, профильная архитектурная документация |
| Интерфейсы | [`02_PRODUCT/14_UI_UX_System.md`](../02_PRODUCT/14_UI_UX_System.md) | `13_MVP_Specification.md`, `09_API_Design.md` |
| Процесс разработки и Git | [`03_DEVELOPMENT/15_Development_Workflow.md`](../03_DEVELOPMENT/15_Development_Workflow.md) | `16_AI_Development_Guide.md` |
| Полномочия и процесс работы AI | [`03_DEVELOPMENT/16_AI_Development_Guide.md`](../03_DEVELOPMENT/16_AI_Development_Guide.md) | `15_Development_Workflow.md`, `AGENTS.md` |
| Стек и первоначальная структура | [`03_DEVELOPMENT/17_Project_Initialization.md`](../03_DEVELOPMENT/17_Project_Initialization.md) | `15_Development_Workflow.md`, `18_Developer_Workstation.md` |
| Состав, статусы и версии документации | [`04_PROJECT/03_MASTER_DOCUMENTATION_INDEX.md`](../04_PROJECT/03_MASTER_DOCUMENTATION_INDEX.md) | Метаданные самих документов |
| Правила документации | [`04_PROJECT/04_DOCUMENTATION_STANDARDS.md`](../04_PROJECT/04_DOCUMENTATION_STANDARDS.md) | Master Documentation Index, Glossary |
| Рабочая станция | [`04_PROJECT/18_Developer_Workstation.md`](../04_PROJECT/18_Developer_Workstation.md) | Project Initialization |
| Терминология | [`99_AI/03_GLOSSARY.md`](03_GLOSSARY.md) | Профильный документ-владелец термина |

## 4. Маршрутизация по типу задачи

| Задача | Начать с | Затем проверить |
|---|---|---|
| Изменение существующего модуля | `07_Module_Specification.md` | `05A_Architecture_Rules.md` и затронутые данные, API, события, безопасность и MVP |
| Новый модуль или изменение его ответственности | `05_Core_Modules.md` | `05_DevOS_Architecture_Foundation.md`, `06_System_Design.md`, `07_Module_Specification.md` и необходимость решения человека |
| Изменение модели данных | `08_Database_Design.md` | `07_Module_Specification.md`, `09_API_Design.md`, `11_Security_Model.md` и MVP |
| Изменение API | `09_API_Design.md` | `07_Module_Specification.md`, `08_Database_Design.md`, `11_Security_Model.md` и MVP |
| Новое или изменённое событие | `10_Event_Architecture.md` | `07_Module_Specification.md`, `09_API_Design.md` и владельца данных |
| Authentication, Authorization, RBAC или tenant isolation | `11_Security_Model.md` | `08_Database_Design.md`, `09_API_Design.md` и необходимость решения человека |
| Новая пользовательская возможность | `13_MVP_Specification.md` | `12_Product_Roadmap.md` и профильные архитектурные документы |
| Изменение интерфейса | `14_UI_UX_System.md` | `13_MVP_Specification.md` и `09_API_Design.md` |
| Изменение процесса разработки | `15_Development_Workflow.md` | `16_AI_Development_Guide.md` и `04_DOCUMENTATION_STANDARDS.md` |
| Инициализация проекта или изменение стека | `17_Project_Initialization.md` | `05A_Architecture_Rules.md` и необходимость решения человека |
| Обновление документации | Документ-владелец изменяемой информации | `04_DOCUMENTATION_STANDARDS.md`, `03_MASTER_DOCUMENTATION_INDEX.md` и связанные документы |
| Исследование | [`00_RESEARCH/00_RESEARCH_METHOD.md`](../00_RESEARCH/00_RESEARCH_METHOD.md) | [`00_RESEARCH/00A_DATA_SOURCES.md`](../00_RESEARCH/00A_DATA_SOURCES.md) и профильные исследования |

Таблицы показывают, где искать информацию, но не являются разрешением на реализацию. Обязательный порядок работы, границы полномочий и процедура разрешения конфликтов определены в `AGENTS.md`.

## 5. Статусы и расхождения

- Состав документации сверяется с Master Documentation Index и фактической файловой системой.
- Статус и версия сверяются с Master Documentation Index и метаданными самого документа.
- Оформление и обновление документации сверяются с Documentation Standards.
- При расхождении документов индекс не выбирает решение. Необходимо применить процедуру из `AGENTS.md`, определить профильный документ-владелец и при необходимости запросить решение человека.

## Related Documents

- [`AGENTS.md`](../AGENTS.md)
- [`01_PROJECT_CONTEXT.md`](01_PROJECT_CONTEXT.md)
- [`03_GLOSSARY.md`](03_GLOSSARY.md)
- [`04_QUICK_START.md`](04_QUICK_START.md)
- [`03_MASTER_DOCUMENTATION_INDEX.md`](../04_PROJECT/03_MASTER_DOCUMENTATION_INDEX.md)
- [`04_DOCUMENTATION_STANDARDS.md`](../04_PROJECT/04_DOCUMENTATION_STANDARDS.md)

## Final Statement

Architecture Index помогает найти официальный источник информации. Решения и требования находятся только в соответствующих документах-владельцах.
