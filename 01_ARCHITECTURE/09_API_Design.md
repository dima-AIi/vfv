# 09_API_Design.md



**Status:** Draft



**Version:** 1.0



**Category:** Architecture



\*\*Related Documents\*\*



\- 05\_Core\_Modules.md

\- 05\_DevOS\_Architecture\_Foundation.md

\- 05A\_Architecture\_Rules.md

\- 06\_System\_Design.md

\- 07\_Module\_Specification.md

\- 08\_Database\_Design.md



\---



\# 1. Executive Summary



Настоящий документ определяет единый стандарт проектирования API платформы DevOS.



API рассматривается не как набор HTTP-эндпоинтов, а как публичный контракт между компонентами системы.



Любая функциональность платформы должна быть доступна через документированный API независимо от пользовательского интерфейса.



Настоящий документ определяет:



\- архитектуру API;

\- правила проектирования ресурсов;

\- стандарты запросов и ответов;

\- безопасность;

\- версионирование;

\- обработку ошибок;

\- требования к производительности;

\- стандарты документирования.



Все модули DevOS обязаны соответствовать данным правилам.



\---



\# 2. Purpose



Документ создаёт единый стандарт разработки API.



Основные цели:



\- обеспечить единообразие всех модулей;

\- упростить генерацию OpenAPI;

\- сделать API предсказуемым;

\- обеспечить совместимость между модулями;

\- подготовить платформу к внешним интеграциям;

\- минимизировать технический долг.



\---



\# 3. Scope



Документ распространяется на:



\- REST API;

\- Internal API;

\- Public API;

\- Module API;

\- Integration API;

\- Webhooks.



Документ не распространяется на:



\- Event Bus;

\- GraphQL;

\- gRPC;

\- Frontend SDK.



\---



\# 4. API Design Principles



Все API DevOS проектируются согласно следующим принципам.



\---



\## Principle 1 — API First



Любая новая возможность сначала проектируется как API.



Только после утверждения API допускается реализация пользовательского интерфейса.



\### FACT



Практически все современные SaaS-платформы используют подход API First.



\### ANALYSIS



Это позволяет:



\- разрабатывать frontend независимо;

\- создавать мобильные приложения;

\- интегрироваться с внешними сервисами;

\- автоматизировать процессы.



\### ENGINEERING DECISION



API является первичным контрактом системы.



\---



\## Principle 2 — Resource Oriented



API описывает ресурсы, а не действия.



Правильно:



/customers



/projects



/tasks



Неправильно:



/createCustomer



/deleteTask



/getProjects



\---



\## Principle 3 — Stateless



Каждый запрос должен содержать всю необходимую информацию.



Сервер не хранит состояние клиента между запросами.



\---



\## Principle 4 — Consistency



Все модули используют единые соглашения:



\- одинаковые URL;

\- одинаковые ошибки;

\- одинаковую пагинацию;

\- одинаковую фильтрацию;

\- одинаковые DTO.



\---



\## Principle 5 — Security by Default



Любой endpoint считается закрытым, пока явно не определено обратное.



Публичный доступ разрешается только после архитектурного решения.



\---



\## Principle 6 — Backward Compatibility



Изменения API не должны ломать существующих клиентов.



Удаление полей и изменение контрактов допускается только при выпуске новой версии API.



\---



\## Principle 7 — Documentation First



Каждый endpoint должен быть документирован до начала реализации.



OpenAPI является обязательной частью процесса разработки.



\---



\# 5. API Architecture Overview



API является единственной публичной точкой входа в бизнес-возможности платформы.



```



Frontend



↓



API Gateway



↓



Authentication



↓



Authorization



↓



Platform Modules



↓



Business Modules



↓



Repositories



↓



Database



```



Пользователь никогда не взаимодействует напрямую с модулем или базой данных.



Все запросы проходят через единый API слой.



\---



\# 6. API Capability Mapping



Каждая Business Capability публикует собственный API-контракт.



| Business Capability | Module | API Prefix | Основные ресурсы |

|---------------------|--------|------------|------------------|

| Identity Management | Identity | /identity | users, sessions, credentials |

| Organization Management | Organization | /organizations | organizations, workspaces |

| Customer Management | CRM | /crm | customers, companies, contacts |

| Project Management | Projects | /projects | projects, milestones |

| Task Management | Tasks | /tasks | tasks, checklists |

| Document Management | Documents | /documents | documents, folders |

| Notification Management | Notifications | /notifications | notifications |

| Automation | Automation | /automation | workflows, triggers |

| Analytics | Analytics | /analytics | dashboards, reports |



\---



\## Engineering Decision



Каждый модуль обязан публиковать отдельную группу API.



Модули не должны смешивать ресурсы других модулей.



Это обеспечивает слабую связанность платформы.



\---



\# 7. API Categories



Все API DevOS разделяются на несколько категорий.



\---



\## Public API



Используется внешними клиентами.



Особенности:



\- стабильные контракты;

\- обязательное версионирование;

\- полная документация;

\- долгосрочная поддержка.



\---



\## Internal API



Используется исключительно платформенными сервисами.



Может изменяться быстрее Public API, но также документируется.



\---



\## Administration API



Предназначен для настройки платформы.



Например:



\- управление пользователями;

\- настройка модулей;

\- лицензии;

\- Feature Flags;

\- аудит.



\---



\## Integration API



Используется внешними системами.



Примеры:



\- Telegram;

\- Slack;

\- GitHub;

\- Stripe;

\- Email Provider.



\---



\## Webhook API



Предназначен для исходящих уведомлений.



Поддерживает:



\- подпись запросов;

\- повторную отправку;

\- журнал доставки.

\# 8. Resource Naming Convention



\## Purpose



Все API платформы используют единый стиль именования ресурсов.



Это обеспечивает:



\- предсказуемость;

\- единообразие;

\- простую генерацию документации;

\- возможность автоматической генерации SDK.



\---



\## Base URL



Все публичные API имеют общий префикс.



```

/api/v1/

```



Примеры:



```

/api/v1/customers



/api/v1/projects



/api/v1/tasks



/api/v1/documents

```



\---



\## Resource Naming Rules



Используются:



\- существительные;

\- множественное число;

\- lowercase;

\- kebab-case при необходимости.



Правильно:



```

/customers



/projects



/project-templates



/knowledge-base

```



Неправильно:



```

/getCustomers



/createProject



/projectList



/deleteTask

```



\---



\## Nested Resources



Используются только при наличии сильной логической связи.



Пример:



```

/projects/{id}/tasks



/customers/{id}/contacts



/documents/{id}/versions

```



Глубина вложенности не должна превышать двух уровней.



\---



\## Actions



Если операция не является CRUD, используется отдельный подресурс.



Например:



```

POST



/projects/{id}/archive



/projects/{id}/restore



/documents/{id}/publish



/users/{id}/reset-password

```



\---



\## Engineering Decision



URL отражает бизнес-ресурс, а не техническую реализацию.



\---



\# 9. HTTP Method Standards



Каждый HTTP-метод имеет строго определенное назначение.



\---



\## GET



Получение данных.



Не изменяет состояние системы.



Идемпотентен.



\---



\## POST



Создание новой сущности.



Либо запуск бизнес-операции.



Например:



```

POST /customers



POST /automation/workflows/run

```



\---



\## PUT



Полная замена ресурса.



Используется редко.



\---



\## PATCH



Частичное изменение.



Предпочтительный способ обновления.



\---



\## DELETE



Логическое удаление.



Физическое удаление допускается только для служебных данных.



\---



\## OPTIONS



Получение информации о возможностях endpoint.



\---



\## HEAD



Получение только заголовков ответа.



\---



\## Engineering Decision



PATCH является основным методом обновления ресурсов.



\---



\# 10. Request Standards



Все запросы используют единый формат.



\---



\## Headers



Минимальный набор:



```

Authorization



Content-Type



Accept



X-Request-ID



X-Correlation-ID

```



\---



\## Organization Context



Для Multi-Tenant запросов контекст организации определяется:



\- JWT;

\- API Key;

\- Session.



Передача organization\_id вручную запрещена.



\---



\## Content-Type



По умолчанию:



```

application/json

```



Для файлов:



```

multipart/form-data

```



\---



\## Correlation ID



Каждый запрос получает уникальный идентификатор.



Он используется:



\- логированием;

\- аудитом;

\- трассировкой;

\- мониторингом.



\---



\## Validation



Валидация выполняется до передачи данных в бизнес-логику.



Проверяются:



\- типы;

\- обязательные поля;

\- диапазоны;

\- форматы;

\- ограничения.



\---



\## Engineering Decision



Контроллер не содержит бизнес-валидации.



Он только принимает запрос и проверяет корректность входных данных.



\---



\# 11. Response Standards



Все успешные ответы используют единый формат.



```

{

&#x20; "data": {},

&#x20; "meta": {},

&#x20; "links": {}

}

```



\---



\## Data



Содержит основной результат.



\---



\## Meta



Дополнительная информация.



Например:



```

pagination



filters



execution\_time



version

```



\---



\## Links



Используются для HATEOAS или навигации.



\---



\## Empty Responses



Для успешных операций без результата используется:



HTTP 204 No Content



\---



\## Collections



Пример:



```

{

&#x20; "data": \[

&#x20;   {},

&#x20;   {}

&#x20; ],

&#x20; "meta": {

&#x20;   "page": 1,

&#x20;   "pageSize": 25,

&#x20;   "total": 150

&#x20; }

}

```



\---



\## Engineering Decision



Все API возвращают одинаковую структуру ответа независимо от модуля.



\---



\# 12. DTO Standards



Передача данных между слоями выполняется исключительно через DTO.



\---



\## Types



Каждый ресурс имеет:



Create DTO



Update DTO



Response DTO



Filter DTO



List DTO



Detail DTO



\---



\## Rules



DTO:



\- не содержит бизнес-логики;

\- не зависит от ORM;

\- не является Entity;

\- используется как контракт API.



\---



\## Naming Convention



Примеры:



```

CreateCustomerDto



UpdateProjectDto



TaskResponseDto



CustomerFilterDto



ProjectListDto

```



\---



\## Engineering Decision



Entity никогда не возвращается напрямую через API.



\---



\# 13. Validation Rules



Валидация выполняется на нескольких уровнях.



\---



\## Layer 1



Transport Validation



Типы данных.



\---



\## Layer 2



Business Validation



Проверка бизнес-правил.



\---



\## Layer 3



Database Constraints



Контроль целостности.



\---



\## Validation Principles



Ошибки должны быть:



\- понятными;

\- детализированными;

\- предсказуемыми;

\- одинаковыми во всех модулях.



\---



\# 14. Error Model



Все ошибки используют единую структуру.



```

{

&#x20; "error": {

&#x20;   "code": "CUSTOMER\_NOT\_FOUND",

&#x20;   "message": "Customer not found.",

&#x20;   "details": \[],

&#x20;   "requestId": "...",

&#x20;   "timestamp": "..."

&#x20; }

}

```



\---



\## Error Categories



Validation



Authentication



Authorization



Business



Conflict



System



External Integration



Rate Limit



\---



\## HTTP Status Mapping



200 OK



201 Created



204 No Content



400 Bad Request



401 Unauthorized



403 Forbidden



404 Not Found



409 Conflict



422 Unprocessable Entity



429 Too Many Requests



500 Internal Server Error



503 Service Unavailable



\---



\## Engineering Decision



Коды ошибок являются частью публичного API-контракта и должны оставаться стабильными между версиями API.

\# 15. Pagination Strategy



\## Purpose



Все endpoint, возвращающие коллекции данных, обязаны поддерживать единый механизм пагинации.



Пагинация необходима для:



\- обеспечения высокой производительности;

\- предотвращения чрезмерной нагрузки;

\- улучшения пользовательского опыта;

\- поддержки больших объемов данных.



\---



\## Supported Pagination Types



\### Offset Pagination



Используется по умолчанию.



Пример:



```

GET /api/v1/customers?page=1\&pageSize=25

```



\---



\### Cursor Pagination



Используется для больших таблиц и бесконечной прокрутки.



Пример:



```

GET /api/v1/tasks?cursor=eyJpZCI6...

```



\---



\## Pagination Metadata



Каждый ответ должен содержать:



```json

{

&#x20; "meta": {

&#x20;   "page": 1,

&#x20;   "pageSize": 25,

&#x20;   "totalItems": 420,

&#x20;   "totalPages": 17,

&#x20;   "hasNext": true,

&#x20;   "hasPrevious": false

&#x20; }

}

```



\---



\## Engineering Decision



Максимальный размер страницы ограничивается на уровне платформы.



По умолчанию:



\- pageSize = 25

\- maximumPageSize = 100



\---



\# 16. Filtering Strategy



\## Purpose



Все коллекции должны поддерживать фильтрацию.



\---



\## Principles



Фильтрация должна быть:



\- единообразной;

\- расширяемой;

\- независимой от реализации ORM.



\---



\## Examples



```

GET /customers?status=active



GET /projects?priority=high



GET /tasks?assignedUser=123



GET /documents?category=contract

```



\---



\## Range Filters



Поддерживаются диапазоны.



```

createdAfter



createdBefore



updatedAfter



updatedBefore



amountMin



amountMax

```



\---



\## Boolean Filters



```

isActive=true



isArchived=false

```



\---



\## Multi Value Filters



```

status=open,completed



category=crm,sales

```



\---



\## Engineering Decision



Названия параметров фильтрации должны совпадать между всеми модулями.



\---



\# 17. Sorting Strategy



Все коллекции поддерживают сортировку.



\---



\## Syntax



```

sort=name



sort=-createdAt



sort=status,-priority

```



\---



\## Rules



По умолчанию используется сортировка:



```

createdAt DESC

```



Если явно не указано другое.



\---



\## Engineering Decision



Сортировка допускается только по заранее определенному набору полей.



\---



\# 18. Search Strategy



DevOS поддерживает несколько уровней поиска.



\---



\## Simple Search



По одному текстовому полю.



```

search=john

```



\---



\## Full Text Search



Используется PostgreSQL Full Text Search.



\---



\## Advanced Search



Комбинация:



\- фильтров;

\- диапазонов;

\- сортировки;

\- полнотекстового поиска.



\---



\## Search Requirements



Поиск обязан учитывать:



\- организацию;

\- права пользователя;

\- статус записи;

\- архивные записи.



\---



\# 19. Field Selection



Для уменьшения объема передаваемых данных клиент может запрашивать только необходимые поля.



Пример:



```

GET /customers?fields=id,name,email

```



\---



\## Rules



Поля перечисляются через запятую.



Недоступные поля игнорируются либо возвращают ошибку в зависимости от уровня безопасности.



\---



\## Engineering Decision



Field Selection обязателен для крупных сущностей.



\---



\# 20. Resource Expansion



Позволяет получать связанные данные одним запросом.



\---



\## Example



```

GET /projects/{id}?expand=owner



GET /customers/{id}?expand=contacts



GET /documents/{id}?expand=versions

```



\---



\## Rules



Глубина вложенности ограничивается.



По умолчанию:



не более двух уровней.



\---



\## Engineering Decision



Expansion используется только для чтения и не изменяет модель данных.



\---



\# 21. API Versioning Strategy



Все публичные API должны поддерживать версионирование.



\---



\## URL Versioning



Используется следующий формат:



```

/api/v1/



/api/v2/

```



\---



\## Version Lifecycle



Каждая версия проходит этапы:



\- Development

\- Stable

\- Deprecated

\- Sunset

\- Removed



\---



\## Backward Compatibility



Новая версия не должна нарушать работу существующих клиентов.



\---



\## Deprecation Policy



При удалении endpoint:



\- публикуется предупреждение;

\- указывается срок прекращения поддержки;

\- предоставляется путь миграции.



\---



\## Engineering Decision



Версионирование является обязательным только для Public API.



\---



\# 22. Authentication



Все защищенные endpoint требуют прохождения аутентификации.



\---



\## Supported Methods



\- JWT Access Token

\- Refresh Token

\- OAuth2

\- API Keys

\- Service Accounts



\---



\## Authentication Flow



Client



↓



Identity Module



↓



Token Validation



↓



Request Context



↓



Business Module



\---



\## Token Requirements



Токены содержат:



\- User ID

\- Organization ID

\- Roles

\- Permissions

\- Expiration



\---



\# 23. Authorization



После успешной аутентификации выполняется проверка прав доступа.



\---



\## Authorization Model



Используется RBAC.



User



↓



Role



↓



Permission



↓



Resource



\---



\## Permission Check



Каждый endpoint обязан определить:



\- необходимое разрешение;

\- область действия;

\- допустимые операции.



\---



\## Organization Scope



Пользователь никогда не может выйти за пределы своей организации.



\---



\## Engineering Decision



Authorization является обязательной частью каждого защищенного endpoint.



\---



\# 24. Idempotency



Для операций создания критически важных сущностей поддерживается идемпотентность.



\---



\## Supported Operations



\- Payments

\- Imports

\- External Integrations

\- Automation

\- Webhooks



\---



\## Idempotency Key



Используется заголовок:



```

Idempotency-Key

```



\---



\## Engineering Decision



Повторная отправка одинакового запроса не должна приводить к повторному созданию ресурса.



\---



\# 25. Rate Limiting



Платформа защищает API от чрезмерной нагрузки.



\---



\## Supported Limits



По IP.



По пользователю.



По API Key.



По организации.



\---



\## Standard Response



При превышении лимита возвращается:



```

429 Too Many Requests

```



с информацией о времени следующей попытки.



\---



\## Engineering Decision



Конкретные значения лимитов определяются конфигурацией платформы и могут отличаться для различных тарифов и типов клиентов.

\# 26. File Upload API



\## Purpose



Все операции загрузки файлов должны использовать единый механизм независимо от бизнес-модуля.



Файлы рассматриваются как отдельный ресурс платформы и управляются модулем \*\*Files\*\*.



\---



\## Upload Process



Стандартный процесс загрузки:



```

Client

&#x20;   ↓

Upload Request

&#x20;   ↓

Validation

&#x20;   ↓

Virus Scan (optional)

&#x20;   ↓

Storage Provider

&#x20;   ↓

File Metadata

&#x20;   ↓

Response

```



\---



\## Supported Content Types



\- Images

\- Documents

\- PDF

\- Archives

\- Audio

\- Video



Типы файлов определяются политикой безопасности платформы.



\---



\## Upload Methods



Поддерживаются:



\- Multipart Upload

\- Chunk Upload

\- Direct Storage Upload (S3 Compatible)



\---



\## File Metadata



Каждый файл содержит:



\- id

\- filename

\- original\_name

\- mime\_type

\- size

\- checksum

\- storage\_provider

\- created\_at

\- uploaded\_by

\- organization\_id



\---



\## Engineering Decision



Файл никогда не хранится непосредственно в бизнес-модуле.



Все модули используют единый File Service.



\---



\# 27. Bulk Operations



\## Purpose



API должно поддерживать массовые операции без необходимости выполнять тысячи отдельных запросов.



\---



\## Supported Operations



\- Bulk Create

\- Bulk Update

\- Bulk Delete

\- Bulk Restore

\- Bulk Archive

\- Bulk Import

\- Bulk Export



\---



\## Rules



Каждая массовая операция должна:



\- выполняться асинхронно при больших объемах;

\- возвращать идентификатор задачи;

\- поддерживать журнал выполнения;

\- быть идемпотентной.



\---



\## Response Example



```json

{

&#x20; "jobId": "job\_01H...",

&#x20; "status": "processing"

}

```



\---



\## Engineering Decision



Операции, изменяющие более 100 записей, рекомендуется выполнять через фоновые задачи.



\---



\# 28. Webhook Design



\## Purpose



DevOS поддерживает отправку событий внешним системам.



\---



\## Supported Events



Например:



\- CustomerCreated

\- ProjectCreated

\- TaskCompleted

\- InvoicePaid

\- UserInvited



\---



\## Delivery Principles



Webhook должен:



\- подписываться цифровой подписью;

\- поддерживать повторные попытки доставки;

\- вести журнал отправок;

\- поддерживать отключение отдельных подписок.



\---



\## Retry Strategy



Рекомендуемая схема:



1\. 1 минута

2\. 5 минут

3\. 15 минут

4\. 1 час

5\. 24 часа



После исчерпания попыток событие помечается как Failed.



\---



\## Engineering Decision



Webhook не должен блокировать выполнение основной бизнес-операции.



\---



\# 29. OpenAPI Standards



\## Purpose



Каждый публичный endpoint обязан быть описан в спецификации OpenAPI.



\---



\## Requirements



Для каждого endpoint документируются:



\- Summary

\- Description

\- Parameters

\- Request Body

\- Response

\- Error Responses

\- Security Requirements

\- Examples



\---



\## Version



Используется OpenAPI 3.x.



\---



\## Automation



Спецификация должна генерироваться автоматически на основе исходного кода и использоваться для публикации интерактивной документации.



\---



\## Engineering Decision



OpenAPI является официальным контрактом Public API.



\---



\# 30. API Documentation Rules



Документация должна быть достаточной для использования API без обращения к исходному коду.



\---



\## Required Sections



Каждый endpoint описывает:



\- Purpose

\- URL

\- Method

\- Authentication

\- Permissions

\- Request

\- Response

\- Error Codes

\- Examples

\- Related Resources



\---



\## Examples



Каждый endpoint обязан содержать примеры:



\- успешного запроса;

\- успешного ответа;

\- типичной ошибки.



\---



\## Engineering Decision



Документация развивается одновременно с API и считается частью продукта.



\---



\# 31. API Testing Strategy



\## Testing Levels



\### Unit Tests



Проверяют отдельные компоненты.



\---



\### Integration Tests



Проверяют взаимодействие между слоями приложения.



\---



\### Contract Tests



Проверяют соответствие реализации спецификации API.



\---



\### End-to-End Tests



Проверяют пользовательские сценарии через API.



\---



\## Test Requirements



Каждый публичный endpoint должен иметь:



\- позитивные сценарии;

\- негативные сценарии;

\- проверку прав доступа;

\- проверку валидации;

\- проверку ошибок.



\---



\## Engineering Decision



Новый endpoint не считается завершенным без автоматических тестов.



\---



\# 32. Performance Guidelines



\## Response Time Targets



Рекомендуемые значения:



\- Simple GET < 200 ms

\- Complex Search < 500 ms

\- Bulk Operations — асинхронно

\- File Upload — потоковая обработка



\---



\## Caching



Допускается использование:



\- HTTP Cache Headers

\- ETag

\- Conditional Requests

\- Application Cache



При этом кэш не должен нарушать требования безопасности и актуальности данных.



\---



\## Payload Optimization



Следует:



\- использовать пагинацию;

\- избегать избыточных данных;

\- поддерживать выбор полей;

\- использовать сжатие ответов.



\---



\## Engineering Decision



Производительность рассматривается как архитектурное требование, а не этап последующей оптимизации.



\---



\# 33. API Development Checklist



Перед реализацией нового endpoint необходимо убедиться, что:



\- определен бизнес-сценарий;

\- выбран существующий модуль;

\- согласован URL;

\- определены DTO;

\- реализована валидация;

\- определены права доступа;

\- предусмотрены ошибки;

\- написаны тесты;

\- обновлена документация OpenAPI;

\- добавлены примеры запросов и ответов.



\---



\# 34. Decision Impact



Настоящий документ определяет единый стандарт разработки API для DevOS.



Все существующие и будущие модули обязаны соответствовать данным правилам.



Изменения API, нарушающие настоящий документ, допускаются только через архитектурное решение (ADR).



\---



\# 35. Related Documents



\- 05\_Core\_Modules.md

\- 05\_DevOS\_Architecture\_Foundation.md

\- 05A\_Architecture\_Rules.md

\- 06\_System\_Design.md

\- 07\_Module\_Specification.md

\- 08\_Database\_Design.md

\- 10\_Event\_Architecture.md

\- 11\_Security\_Model.md



\---



\# 36. Open Questions



Требуют дальнейшей проработки:



\- поддержка GraphQL в будущем;

\- политика долгосрочной поддержки версий API;

\- генерация клиентских SDK;

\- ограничения Public API для бесплатных тарифов;

\- стратегия API Gateway при микросервисной архитектуре.



\---



\# 37. Decision Log



| Version | Decision | Rationale |

|---------|----------|-----------|

| 1.0 | API First | Единый контракт между модулями |

| 1.0 | REST как основной стиль | Широкая совместимость и зрелость |

| 1.0 | OpenAPI обязателен | Автоматизация документации и SDK |

| 1.0 | PATCH как основной метод обновления | Частичное изменение ресурсов |

| 1.0 | Единая структура ошибок | Предсказуемость и единообразие |



\---



\# 38. Research Quality



\## Sources



Документ основан на:



\- предыдущих исследованиях DevOS;

\- принципах REST;

\- OpenAPI Specification;

\- практиках проектирования корпоративных API;

\- анализе современных SaaS-платформ.



\---



\## Confidence Level



Высокий.



Все ключевые решения подтверждены исследованиями и согласованы с архитектурными документами DevOS.



\---



\# 39. Change History



| Version | Changes |

|---------|---------|

| 1.0 | Первое утвержденное издание документа |
