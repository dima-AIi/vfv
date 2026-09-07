# 05B_Platform_Reference.md



**Status:** Draft



**Version:** 1.0



**Category:** Architecture



\*\*Purpose\*\*



Данный документ является центральным справочником платформы DevOS.



В отличие от остальных архитектурных документов, он не описывает новые технические решения.



Его задача — предоставить единую точку входа для разработчиков, архитекторов и AI-инструментов (Claude Code, Cursor и других), позволяя быстро ориентироваться в архитектуре платформы.



Этот документ связывает между собой все остальные документы проекта и определяет единый язык платформы.



\---



\# 1. Executive Summary



По мере развития DevOS количество архитектурной документации постоянно увеличивается.



Каждый документ описывает отдельную область:



\- архитектуру;

\- API;

\- безопасность;

\- события;

\- базу данных;

\- модули;

\- Roadmap.



Без единого справочника становится сложно быстро определить:



\- где находится нужная информация;

\- как связаны модули;

\- что означает конкретный термин;

\- какие зависимости существуют между компонентами.



Поэтому Platform Reference становится центральной навигационной точкой всей документации DevOS.



\---



\## Objectives



Документ должен обеспечивать:



\- единый словарь терминов;

\- обзор архитектуры платформы;

\- карту модулей;

\- карту возможностей;

\- карту зависимостей;

\- основные жизненные циклы;

\- ссылки на специализированные документы.



\---



\## Scope



Документ охватывает:



\- терминологию;

\- общую архитектуру;

\- обзор компонентов;

\- жизненные циклы;

\- навигацию по документации.



Документ \*\*не заменяет\*\* специализированные документы.



Для получения детальной информации необходимо обращаться к соответствующим спецификациям.



\---



\# 2. Platform Overview



\## DevOS Mission



DevOS представляет собой модульную Business Operating System.



Основная цель платформы — предоставить универсальный набор переиспользуемых бизнес-возможностей, из которых можно собирать современные корпоративные приложения.



Архитектура ориентирована не на конкретные отрасли, а на универсальные бизнес-процессы.



\---



\## Platform Model



```

Business Problem



&#x20;       ↓



Business Capability



&#x20;       ↓



Platform Module



&#x20;       ↓



Configuration



&#x20;       ↓



Industry Solution

```



\---



\## Industry Examples



Одни и те же возможности используются различными решениями.



```

CRM



\+



Projects



\+



Tasks



\+



Notifications



=



Construction Platform

```



```

CRM



\+



Calendar



\+



Notifications



=



Beauty CRM

```



```

CRM



\+



Workflow



\+



Documents



=



Service Desk

```



\---



\## Platform Philosophy



DevOS строится вокруг следующих принципов:



\- Platform First;

\- Capability First;

\- Modular Architecture;

\- API First;

\- Event Driven;

\- Security by Default;

\- Documentation First;

\- AI Friendly Development.



\---



\# 3. Platform Vocabulary



\## Purpose



Все документы DevOS используют единый словарь терминов.



Использование разных названий для одной сущности запрещается.



\---



\## Core Terms



| Term | Definition |

|------|------------|

| Organization | Независимая компания (Tenant) внутри платформы |

| Workspace | Рабочее пространство организации |

| User | Пользователь платформы |

| Role | Набор разрешений пользователя |

| Permission | Право выполнения определенного действия |

| Capability | Независимая бизнес-возможность платформы |

| Module | Программная реализация одной или нескольких Capabilities |

| Entity | Бизнес-сущность предметной области |

| Aggregate | Логическая группа связанных сущностей |

| Event | Факт произошедшего бизнес-события |

| Workflow | Последовательность бизнес-действий |

| Automation | Автоматическое выполнение процессов |

| Trigger | Условие запуска автоматизации |

| Action | Выполняемое системой действие |

| Integration | Взаимодействие с внешними системами |

| Dashboard | Панель отображения информации |

| API | Публичный программный интерфейс модуля |

| Repository | Компонент доступа к данным |

| Service | Компонент бизнес-логики |



\---



\## Naming Rules



Во всей платформе используется единая терминология.



Например:



Используется:



\- Organization



Не используются:



\- Company

\- Tenant Company

\- Business



\---



Используется:



\- User



Не используются:



\- Client

\- Employee

\- Member



если речь идет о пользователе платформы.



\---



\## Engineering Decision



Все будущие документы обязаны использовать исключительно термины, определенные в данном разделе.



Изменение терминологии допускается только через ADR.



\---



\# 4. Platform Layers



Архитектура DevOS разделена на независимые уровни.



```

Presentation



&#x20;       ↓



API Gateway



&#x20;       ↓



Business Modules



&#x20;       ↓



Core Services



&#x20;       ↓



Infrastructure



&#x20;       ↓



Persistence

```



\---



\## Presentation Layer



Отвечает за взаимодействие с пользователем.



Включает:



\- Web UI;

\- Admin Panel;

\- Client Portal;

\- Dashboard.



\---



\## API Layer



Предоставляет единый программный интерфейс платформы.



Основные задачи:



\- маршрутизация;

\- авторизация;

\- валидация;

\- версионирование.



\---



\## Business Layer



Основной слой платформы.



Содержит:



\- CRM;

\- Projects;

\- Tasks;

\- Documents;

\- Workflow;

\- Notifications;

\- Analytics.



\---



\## Core Layer



Общие сервисы платформы.



Например:



\- Identity;

\- RBAC;

\- Configuration;

\- Audit;

\- Event Bus.



\---



\## Infrastructure Layer



Содержит инфраструктурные сервисы.



Например:



\- Storage;

\- Queue;

\- Cache;

\- Scheduler;

\- Search.



\---



\## Persistence Layer



Отвечает за долговременное хранение данных.



Включает:



\- PostgreSQL;

\- Redis;

\- Object Storage.



\---



\## Engineering Decision



Каждый модуль принадлежит только одному архитектурному слою.



Перемещение функциональности между слоями требует архитектурного анализа.



\# 5. Capability Map



\## Purpose



Capability Model является центральной концепцией DevOS.



Платформа строится не вокруг конкретных приложений, а вокруг независимых бизнес-возможностей.



Capabilities могут комбинироваться и образовывать различные отраслевые решения.



\---



\## Capability Groups



\### Platform Capabilities



Фундамент платформы.



\- Identity

\- Authentication

\- Authorization

\- Organizations

\- RBAC

\- Configuration

\- Audit

\- Settings



\---



\### Business Capabilities



Основные бизнес-модули.



\- CRM

\- Projects

\- Tasks

\- Documents

\- Files

\- Calendar

\- Workflow

\- Notifications

\- Analytics

\- Reports



\---



\### Infrastructure Capabilities



Системные сервисы.



\- Event Bus

\- Search

\- Scheduler

\- Queue

\- Storage

\- Logging

\- Monitoring



\---



\### Automation Capabilities



Автоматизация процессов.



\- Rules

\- Triggers

\- Actions

\- Background Jobs



\---



\### Integration Capabilities



Внешние взаимодействия.



\- REST

\- Webhooks

\- Email

\- Telegram

\- External APIs



\---



\## Capability Hierarchy



```

Platform



&#x20;   ↓



Core Services



&#x20;   ↓



Business Capabilities



&#x20;   ↓



Automation



&#x20;   ↓



Industry Solutions

```



\---



\## Engineering Decision



Новые возможности должны добавляться как Capabilities.



Создание узкоспециализированных решений без выделения Capability запрещается.



\---



\# 6. Core Module Map



Ниже представлена общая карта основных модулей платформы.



```

Identity



Organizations



RBAC



Configuration



Audit



Events



Storage



Search



CRM



Projects



Tasks



Documents



Workflow



Notifications



Analytics

```



\---



\## Platform Core



Модули ядра:



\- Identity

\- Organizations

\- RBAC

\- Configuration

\- Audit



\---



\## Business Modules



Основные бизнес-модули:



\- CRM

\- Projects

\- Tasks

\- Documents

\- Workflow



\---



\## Supporting Modules



Вспомогательные модули:



\- Notifications

\- Search

\- Analytics

\- Files



\---



\## Infrastructure Modules



Инфраструктура:



\- Event Bus

\- Queue

\- Scheduler

\- Storage



\---



\# 7. Module Dependency Map



\## Purpose



Документирует допустимые зависимости между модулями.



\---



\## Dependency Flow



```

Identity



↓



Organizations



↓



RBAC



↓



Configuration



↓



Audit



↓



CRM



↓



Projects



↓



Tasks



↓



Documents



↓



Workflow



↓



Notifications



↓



Analytics

```



\---



\## Event Dependencies



Допустимы:



```

CRM



→ CustomerCreated



→ Notifications

```



```

Projects



→ ProjectCreated



→ Analytics

```



\---



\## Forbidden Dependencies



Запрещено:



```

CRM



↓



Projects



↓



CRM

```



Циклические зависимости недопустимы.



\---



\## Engineering Decision



Каждый модуль должен иметь минимальное количество зависимостей.



\---



\# 8. Platform Context Diagram



Общая схема платформы.



```

Users



&#x20;       ↓



Web UI



&#x20;       ↓



API Gateway



&#x20;       ↓



Authentication



&#x20;       ↓



Authorization



&#x20;       ↓



Business Modules



&#x20;       ↓



Events



&#x20;       ↓



Infrastructure



&#x20;       ↓



Database

```



\---



\## Context Description



\### Users



Пользователи платформы.



\---



\### UI



Интерфейс взаимодействия.



\---



\### API Gateway



Единая точка входа.



\---



\### Security



Authentication + Authorization.



\---



\### Business Layer



Основные бизнес-модули.



\---



\### Event Layer



Связь между компонентами.



\---



\### Infrastructure



Storage, Queue, Search.



\---



\### Persistence



PostgreSQL, Redis, Files.



\---



\# 9. Request Lifecycle



Жизненный цикл запроса.



```

Request



↓



Validation



↓



Authentication



↓



Authorization



↓



Business Logic



↓



Repository



↓



Database



↓



Event



↓



Response

```



\---



\## Step Description



\### Validation



Проверка входных данных.



\---



\### Authentication



Проверка личности пользователя.



\---



\### Authorization



Проверка прав.



\---



\### Business Logic



Выполнение операций.



\---



\### Repository



Работа с данными.



\---



\### Database



Хранение информации.



\---



\### Event



Публикация событий.



\---



\### Response



Возврат результата.



\---



\## Engineering Decision



Бизнес-логика не должна располагаться:



\- в контроллерах;

\- в API;

\- в репозиториях.



\---



\# 10. Event Lifecycle



Жизненный цикл событий.



```

Business Action



↓



Domain Event



↓



Event Bus



↓



Subscribers



↓



Automation



↓



Notifications



↓



Analytics

```



\---



\## Example



```

Customer Created



↓



CustomerCreated



↓



Notification



↓



Analytics



↓



Audit

```



\---



\## Event Rules



Событие:



\- описывает факт;

\- не содержит бизнес-логики;

\- неизменно после публикации.



\---



\## Engineering Decision



Интеграция модулей должна происходить через события.



Прямые зависимости должны быть минимальными.



\---



\# 11. Data Lifecycle



Жизненный цикл данных.



```

Create



↓



Validate



↓



Store



↓



Publish Event



↓



Update



↓



Archive



↓



Delete

```



\---



\## States



\### Create



Создание записи.



\---



\### Validate



Проверка правил.



\---



\### Store



Сохранение.



\---



\### Publish Event



Публикация события.



\---



\### Update



Изменение.



\---



\### Archive



Архивирование.



\---



\### Delete



Удаление или soft delete.



\---



\## Engineering Decision



Удаление данных должно быть контролируемым и аудируемым процессом.



\---



\# 12. Module Lifecycle



Жизненный цикл модуля.



```

Idea



↓



Specification



↓



Architecture



↓



Implementation



↓



Testing



↓



Documentation



↓



Release



↓



Maintenance

```



\---



\## Description



\### Idea



Формирование потребности.



\---



\### Specification



Создание описания.



\---



\### Architecture



Проектирование.



\---



\### Implementation



Разработка.



\---



\### Testing



Проверка.



\---



\### Documentation



Обновление документации.



\---



\### Release



Выпуск.



\---



\### Maintenance



Поддержка.



\# 13. Security Overview



\## Purpose



Безопасность является фундаментальной частью архитектуры DevOS.



Каждый модуль обязан соблюдать единые принципы безопасности.



Security не является отдельным модулем — она встроена в каждый уровень платформы.



\---



\## Security Architecture



```

User



↓



Authentication



↓



Authorization (RBAC)



↓



Business Module



↓



Audit



↓



Monitoring

```



\---



\## Security Layers



\### Identity



Отвечает за идентификацию пользователя.



\---



\### Authentication



Подтверждает личность пользователя.



Используются:



\- JWT

\- Refresh Token

\- Session Management



\---



\### Authorization



Определяет доступ пользователя.



Используется модель:



```

User



↓



Role



↓



Permission



↓



Resource

```



\---



\### Audit



Все критические действия должны записываться.



Примеры:



\- Login

\- Logout

\- Create User

\- Delete Project

\- Change Role

\- Export Data



\---



\### Monitoring



Контроль:



\- подозрительных действий;

\- ошибок безопасности;

\- неудачных попыток входа;

\- превышения лимитов.



\---



\## Security Principles



Каждый модуль обязан:



\- проверять права доступа;

\- использовать централизованную аутентификацию;

\- не хранить пароли;

\- не обходить RBAC;

\- вести аудит изменений.



\---



\## Reference



Подробное описание находится в:



\*\*11\_Security\_Model.md\*\*



\---



\# 14. API Overview



\## Purpose



Все возможности DevOS доступны через единый API.



API является официальным контрактом между системой и клиентами.



\---



\## API Flow



```

Client



↓



API Gateway



↓



Authentication



↓



Authorization



↓



Validation



↓



Business Module



↓



Repository



↓



Database



↓



Event



↓



Response

```



\---



\## API Principles



Каждый API обязан:



\- быть RESTful;

\- иметь версионирование;

\- использовать OpenAPI;

\- проходить валидацию;

\- возвращать единый формат ошибок;

\- публиковать события после изменения данных.



\---



\## API Categories



\### Platform API



Например:



\- Authentication

\- Users

\- Organizations

\- Roles

\- Permissions



\---



\### Business API



Например:



\- CRM

\- Projects

\- Tasks

\- Documents



\---



\### Integration API



Например:



\- Webhooks

\- External APIs

\- Notifications



\---



\## Reference



Полное описание:



\*\*09\_API\_Design.md\*\*



\---



\# 15. Database Overview



\## Purpose



База данных организована вокруг предметной области.



Каждый модуль владеет своими данными.



\---



\## High-Level Structure



```

Organizations



↓



Users



↓



Roles



↓



Permissions



↓



Business Modules



↓



Events



↓



Audit

```



\---



\## Core Entities



Общие сущности платформы:



\- Organization

\- User

\- Role

\- Permission

\- Settings

\- Audit Log



\---



\## Business Entities



Каждый модуль определяет собственные сущности.



Например:



CRM:



\- Customer

\- Contact

\- Company



Projects:



\- Project

\- Milestone

\- Task



Documents:



\- Document

\- Folder

\- Attachment



\---



\## Storage Principles



Каждый модуль:



\- отвечает за свои таблицы;

\- не изменяет чужие данные напрямую;

\- взаимодействует через API или события.



\---



\## Reference



Подробная схема:



\*\*08\_Database\_Design.md\*\*



\---



\# 16. Architecture Principles Summary



\## Purpose



Ниже приведены основные архитектурные принципы DevOS.



Они являются обязательными для всех новых модулей.



\---



\## Core Principles



\### Business Capability First



Сначала определяется бизнес-возможность.



Только затем создается модуль.



\---



\### Modular Architecture



Каждый модуль независим.



\---



\### API First



Любая функциональность должна быть доступна через API.



\---



\### Event Driven



Модули взаимодействуют через события.



\---



\### Security by Default



Безопасность встроена в платформу.



\---



\### Configuration over Customization



Поведение платформы изменяется настройками, а не изменением кода.



\---



\### Documentation First



Архитектурные решения документируются до реализации.



\---



\### AI Friendly Development



Документация должна быть понятна как разработчику, так и AI.



\---



\## Reference



Основные принципы подробно описаны в:



\- 05\_DevOS\_Architecture\_Foundation.md

\- 05A\_Architecture\_Rules.md



\---



\# 17. Cross Reference Matrix



\## Purpose



Быстрая навигация по документации DevOS.



| Что необходимо найти | Документ |

|----------------------|----------|

| Архитектурные принципы | 05\_DevOS\_Architecture\_Foundation.md |

| Правила разработки | 05A\_Architecture\_Rules.md |

| System Design | 06\_System\_Design.md |

| Бизнес-модули | 07\_Module\_Specification.md |

| Database | 08\_Database\_Design.md |

| API | 09\_API\_Design.md |

| Events | 10\_Event\_Architecture.md |

| Security | 11\_Security\_Model.md |

| Product Roadmap | 12\_Product\_Roadmap.md |

| MVP | 13\_MVP\_Specification.md |



\---



\## Navigation Rule



Перед созданием новой функциональности необходимо определить документ, который уже описывает соответствующую область.



\---



\# 18. Quick Start for AI



\## Purpose



Данный раздел определяет последовательность действий AI при работе с DevOS.



\---



\## Step 1



Изучить:



\*\*05\_DevOS\_Architecture\_Foundation.md\*\*



Чтобы понять философию платформы.



\---



\## Step 2



Изучить:



\*\*05A\_Architecture\_Rules.md\*\*



Чтобы соблюдать правила разработки.



\---



\## Step 3



Использовать настоящий документ как навигационный центр.



\---



\## Step 4



Перед генерацией кода открыть соответствующую спецификацию.



Например:



API →



09\_API\_Design.md



Database →



08\_Database\_Design.md



Security →



11\_Security\_Model.md



\---



\## Step 5



Не создавать:



\- новые архитектурные принципы;

\- новые способы организации модулей;

\- новые паттерны взаимодействия.



Без утвержденного ADR.



\---



\## AI Rules



AI обязан:



\- соблюдать Capability Model;

\- использовать существующие модули;

\- избегать дублирования;

\- обновлять документацию при изменениях;

\- соблюдать принципы платформы.



\---



\# 19. Decision Impact



Platform Reference является центральной точкой навигации по архитектуре DevOS.



Документ не вводит новых архитектурных решений, а объединяет существующую документацию в единую систему знаний.



\---



\# 20. Related Documents



\- 05\_Core\_Modules.md

\- 05\_DevOS\_Architecture\_Foundation.md

\- 05A\_Architecture\_Rules.md

\- 06\_System\_Design.md

\- 07\_Module\_Specification.md

\- 08\_Database\_Design.md

\- 09\_API\_Design.md

\- 10\_Event\_Architecture.md

\- 11\_Security\_Model.md

\- 12\_Product\_Roadmap.md

\- 13\_MVP\_Specification.md



\---



\# 21. Open Questions



Требуют дальнейшей детализации:



\- Marketplace Reference;

\- Plugin SDK Reference;

\- AI Agent Reference;

\- Enterprise Deployment Reference.



\---



\# 22. Decision Log



| Version | Decision | Rationale |

|----------|----------|-----------|

| 1.0 | Создан единый справочник платформы | Централизация архитектурной информации |

| 1.0 | Зафиксирован единый словарь терминов | Исключение неоднозначностей |

| 1.0 | Добавлены обзорные схемы платформы | Упрощение навигации и понимания архитектуры |

| 1.0 | Введён раздел Quick Start for AI | Стандартизация работы Claude Code и Cursor |



\---



\# 23. Research Quality



Документ основан на:



\- исследованиях рынка;

\- архитектурных документах DevOS;

\- принципах модульной архитектуры;

\- современных практиках Enterprise Software Development.



Уровень достоверности: \*\*Высокий\*\*.



\---



\# 24. Change History



| Version | Changes |

|----------|----------|

| 1.0 | Первое утверждённое издание Platform Reference |



\# 25. Platform Navigation Map



\## Purpose



Данный раздел показывает, какой документ необходимо использовать для решения конкретной задачи.



\---



\### Business Analysis



Использовать:



\- 01\_Market\_Research.md

\- 02\_Client\_Research.md

\- 03\_Competitor\_Research.md

\- 04\_SaaS\_Research.md



\---



\### Platform Architecture



Использовать:



\- 05\_Core\_Modules.md

\- 05\_DevOS\_Architecture\_Foundation.md

\- 05A\_Architecture\_Rules.md



\---



\### System Design



Использовать:



\- 06\_System\_Design.md



\---



\### Module Development



Использовать:



\- 07\_Module\_Specification.md



\---



\### Database



Использовать:



\- 08\_Database\_Design.md



\---



\### API



Использовать:



\- 09\_API\_Design.md



\---



\### Events



Использовать:



\- 10\_Event\_Architecture.md



\---



\### Security



Использовать:



\- 11\_Security\_Model.md



\---



\### Product Planning



Использовать:



\- 12\_Product\_Roadmap.md

\- 13\_MVP\_Specification.md



\---



\### User Experience



Использовать:



\- 14\_UI\_UX\_System.md



\---



\### Development Process



Использовать:



\- 15\_Development\_Workflow.md

\- 16\_AI\_Development\_Guide.md



\---



\# 26. Architecture Dependency Matrix



\## Purpose



Показывает зависимости между архитектурными документами.



| Document | Depends On |

|-----------|------------|

| 05\_Core\_Modules | Research |

| 05\_Architecture\_Foundation | Core Modules |

| 05A\_Architecture\_Rules | Architecture Foundation |

| 05B\_Platform\_Reference | Все архитектурные документы |

| 06\_System\_Design | Architecture Foundation |

| 07\_Module\_Specification | System Design |

| 08\_Database\_Design | Module Specification |

| 09\_API\_Design | Module Specification |

| 10\_Event\_Architecture | API + Modules |

| 11\_Security\_Model | System Design |

| 12\_Product\_Roadmap | Architecture |

| 13\_MVP\_Specification | Product Roadmap |

| 14\_UI\_UX\_System | MVP |

| 15\_Development\_Workflow | Architecture |

| 16\_AI\_Development\_Guide | Development Workflow |



\---



\## Engineering Decision



Любые изменения должны вноситься сверху вниз.



Изменение документа верхнего уровня требует проверки всех зависимых документов.



\---



\# 27. AI Context Loading Strategy



\## Purpose



Определяет порядок загрузки документации AI-инструментами.



\---



\### Stage 1



Всегда читать:



\- 05\_DevOS\_Architecture\_Foundation.md

\- 05A\_Architecture\_Rules.md



\---



\### Stage 2



Открыть:



05B\_Platform\_Reference.md



для получения общей картины проекта.



\---



\### Stage 3



Определить область задачи.



Например:



Создание API



↓



09\_API\_Design.md



Создание нового модуля



↓



07\_Module\_Specification.md



Работа с безопасностью



↓



11\_Security\_Model.md



\---



\### Stage 4



После завершения разработки:



\- обновить документацию;

\- проверить Architecture Rules;

\- проверить отсутствие конфликтов.



\---



\## Engineering Decision



AI никогда не должен генерировать код без предварительного изучения соответствующей архитектурной документации.



\---



\# 28. Platform Reference Maintenance



\## Purpose



Platform Reference должен всегда отражать актуальное состояние DevOS.



\---



Документ обновляется при:



\- добавлении нового модуля;

\- изменении архитектуры;

\- появлении новой Capability;

\- изменении терминологии;

\- создании нового архитектурного документа.



\---



\## Update Rules



При любом изменении необходимо обновить:



\- Vocabulary;

\- Capability Map;

\- Cross Reference;

\- Navigation Map;

\- Dependency Matrix.



\---



\# 29. Final Statement



Platform Reference является официальной картой платформы DevOS.



Любой разработчик, архитектор или AI должен использовать данный документ как первую точку входа перед изучением специализированной документации.



Цель документа — обеспечить единое понимание архитектуры, терминологии и структуры проекта независимо от того, кто участвует в разработке.



\# 30. Architecture Decision Flow



\## Purpose



Данный раздел определяет порядок принятия архитектурных решений в DevOS.



Все изменения архитектуры должны проходить единый процесс оценки.



\---



\## Decision Flow



```

Business Need



↓



Research



↓



Architecture Analysis



↓



ADR



↓



Implementation



↓



Documentation Update



↓



Release

```



\---



\## Decision Levels



\### Level 1 — Local



Изменения внутри одного модуля.



Пример:



\- новая таблица;

\- новый endpoint;

\- новое событие.



ADR не требуется.



\---



\### Level 2 — Platform



Изменения нескольких модулей.



Пример:



\- изменение API;

\- изменение Event Flow;

\- изменение структуры модулей.



Требуется архитектурное согласование.



\---



\### Level 3 — Foundation



Изменения фундаментальных принципов платформы.



Пример:



\- изменение Capability Model;

\- изменение Core Architecture;

\- изменение Security Model.



Обязательно оформляется ADR.



\---



\## Engineering Decision



Фундаментальные решения принимаются только после анализа влияния на всю платформу.



\---



\# 31. Platform Evolution Strategy



\## Purpose



DevOS развивается поэтапно.



Каждый этап должен оставаться полностью работоспособным.



\---



\## Phase 1



Architecture



Документация.



\---



\## Phase 2



Platform Foundation



Ядро платформы.



\---



\## Phase 3



Core Modules



Identity



Organization



RBAC



Settings



Audit



\---



\## Phase 4



Business Modules



CRM



Projects



Tasks



Documents



Workflow



\---



\## Phase 5



Automation



Rules



Triggers



Actions



Notifications



\---



\## Phase 6



Commercial Products



Создание отраслевых решений.



\---



\## Engineering Decision



Разработка всегда ведется снизу вверх.



\---



\# 32. Architecture Quality Checklist



Перед завершением любой новой функциональности необходимо проверить следующие вопросы.



\---



\## Business



□ Решает ли изменение бизнес-задачу?



□ Не дублирует ли существующий функционал?



\---



\## Architecture



□ Используется существующая Capability?



□ Не нарушены границы модулей?



□ Нет циклических зависимостей?



\---



\## API



□ Соблюдены правила API Design?



□ Обновлена спецификация?



\---



\## Database



□ Соблюдены правила Database Design?



□ Нет доступа к чужим данным?



\---



\## Events



□ Созданы необходимые Domain Events?



□ Нет лишних событий?



\---



\## Security



□ Проверяются права доступа?



□ Обновлены Permissions?



\---



\## Documentation



□ Документация обновлена?



□ Обновлен Platform Reference?



\---



\## AI



□ Claude Code сможет понять изменение?



□ Cursor сможет реализовать изменение без дополнительных объяснений?



\---



\# 33. Success Criteria



Platform Reference считается актуальным, если:



\- терминология едина во всей документации;

\- все архитектурные документы связаны между собой;

\- зависимости актуальны;

\- Navigation Map соответствует текущему состоянию проекта;

\- AI способен определить нужный документ менее чем за одну минуту.



\---



\# 34. Conclusion



Platform Reference является центральной картой архитектуры DevOS.



Документ обеспечивает единое понимание платформы для:



\- архитекторов;

\- разработчиков;

\- аналитиков;

\- AI-инструментов.



Все новые документы и изменения архитектуры должны быть согласованы с данным справочником.



Platform Reference не заменяет специализированную документацию, а обеспечивает единый вход в архитектурную базу знаний DevOS.
