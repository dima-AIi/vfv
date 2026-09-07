# 10_Event_Architecture.md



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

\- 09\_API\_Design.md



\---



\# 1. Executive Summary



Настоящий документ определяет единый стандарт событийной архитектуры (Event-Driven Architecture) платформы DevOS.



В DevOS события являются основным механизмом взаимодействия между независимыми модулями платформы.



Любое существенное изменение состояния бизнес-домена должно выражаться в виде события.



События позволяют:



\- уменьшить связанность модулей;

\- автоматизировать бизнес-процессы;

\- строить Workflow Engine;

\- реализовывать систему уведомлений;

\- создавать журнал аудита;

\- интегрироваться с внешними сервисами;

\- масштабировать платформу без изменения существующих модулей.



Настоящий документ определяет:



\- архитектуру событий;

\- категории событий;

\- правила публикации;

\- правила обработки;

\- жизненный цикл;

\- требования к безопасности;

\- требования к надежности.



Все модули DevOS обязаны соответствовать данным правилам.



\---



\# 2. Purpose



Документ создаёт единый стандарт проектирования событийной модели платформы.



Основные цели:



\- обеспечить слабую связанность модулей;

\- стандартизировать обмен сообщениями;

\- обеспечить масштабируемость;

\- подготовить платформу к автоматизации;

\- обеспечить повторное использование событий;

\- минимизировать зависимость между сервисами.



\---



\# 3. Scope



Документ распространяется на:



\- Domain Events;

\- Integration Events;

\- System Events;

\- Workflow Events;

\- Notification Events;

\- Audit Events;

\- Event Bus.



Документ не распространяется на:



\- REST API;

\- Database Schema;

\- Frontend Events;

\- UI State;

\- Webhooks (описаны отдельно).



\---



\# 4. Event-Driven Principles



Все события DevOS проектируются согласно следующим принципам.



\---



\## Principle 1 — Business First



Событие описывает бизнес-факт.



Не техническое действие.



Правильно:



CustomerCreated



InvoicePaid



TaskCompleted



ProjectArchived



Неправильно:



InsertCustomer



ExecuteSQL



CallService



\---



\### FACT



Современные Enterprise-платформы используют бизнес-события как основу взаимодействия компонентов.



\### ANALYSIS



Бизнес практически не меняется.



Технологии меняются постоянно.



Поэтому события должны описывать именно бизнес.



\### ENGINEERING DECISION



Каждое событие обязано отражать произошедший бизнес-факт.



\---



\## Principle 2 — Loose Coupling



Модули не вызывают друг друга напрямую.



Они публикуют события.



Получатели самостоятельно принимают решение:



обрабатывать событие



или игнорировать.



\---



\## Principle 3 — Event Immutability



После публикации событие никогда не изменяется.



Исправление ошибок производится публикацией нового события.



\---



\## Principle 4 — Asynchronous Processing



По возможности события обрабатываются асинхронно.



Это уменьшает задержки пользовательских операций.



\---



\## Principle 5 — Reliability



Потеря события считается критической ошибкой платформы.



Все события должны быть доставлены подписчикам согласно выбранной стратегии доставки.



\---



\## Principle 6 — Idempotency



Повторная обработка одного события не должна изменять состояние системы повторно.



\---



\## Principle 7 — Observability



Каждое событие должно отслеживаться.



Платформа обязана знать:



\- кто создал событие;

\- когда;

\- каким модулем;

\- сколько подписчиков обработало событие;

\- возникли ли ошибки.



\---



\# 5. Event Architecture Overview



Общая модель взаимодействия модулей.



```



Business Action



↓



Domain Module



↓



Domain Event



↓



Event Bus



↓



Subscribers



↓



Business Services



↓



Automation



↓



Notifications



↓



Audit



```



Модули никогда не обращаются напрямую к внутренней логике других модулей.



Взаимодействие происходит через события либо публичный API.



\---



\# 6. Business Capability → Event Mapping



Каждая Capability публикует собственные бизнес-события.



| Capability | Module | Основные события |

|------------|---------|------------------|

| Identity Management | Identity | UserCreated, UserActivated, PasswordChanged |

| Organization Management | Organization | OrganizationCreated, OrganizationUpdated |

| CRM | CRM | CustomerCreated, CustomerUpdated, CustomerArchived |

| Projects | Projects | ProjectCreated, ProjectStarted, ProjectCompleted |

| Tasks | Tasks | TaskCreated, TaskAssigned, TaskCompleted |

| Documents | Documents | DocumentUploaded, DocumentPublished, DocumentArchived |

| Notifications | Notifications | NotificationQueued, NotificationSent, NotificationFailed |

| Automation | Automation | WorkflowStarted, WorkflowCompleted |

| Analytics | Analytics | ReportGenerated, DashboardUpdated |



\---



\## Engineering Decision



Каждый модуль является владельцем только собственных событий.



Другие модули не имеют права публиковать события чужого домена.



\---



\# 7. Event Categories



Все события платформы разделяются на несколько категорий.



\---



\## Domain Events



Главные бизнес-события.



Примеры:



CustomerCreated



InvoicePaid



ProjectCompleted



TaskAssigned



Именно Domain Events являются основой архитектуры DevOS.



\---



\## Integration Events



Используются для взаимодействия с внешними системами.



Например:



CRMUpdated



GitHubIssueCreated



TelegramMessageReceived



PaymentConfirmed



\---



\## Internal Events



Используются исключительно внутри платформы.



Примеры:



CacheInvalidated



IndexUpdated



SessionExpired



\---



\## Workflow Events



Используются системой автоматизации.



Например:



WorkflowStarted



StepCompleted



WorkflowFailed



WorkflowCancelled



\---



\## Notification Events



Используются модулем уведомлений.



Например:



EmailQueued



PushDelivered



TelegramSent



SMSFailed



\---



\## Audit Events



Используются системой аудита.



Например:



UserLoggedIn



PermissionChanged



ConfigurationUpdated



SensitiveDataAccessed



\---



\## Engineering Decision



Каждое событие принадлежит только одной категории.



Категория определяет правила хранения, доставки и обработки.

\# 8. Event Naming Convention



\## Purpose



Единое соглашение об именовании событий обеспечивает:



\- предсказуемость;

\- читаемость;

\- автоматическую генерацию документации;

\- простую интеграцию между модулями;

\- отсутствие дублирования событий.



\---



\## Naming Rules



Каждое событие именуется по следующей схеме:



```

<Entity><BusinessAction>

```



Примеры:



```

CustomerCreated



CustomerUpdated



CustomerArchived



ProjectStarted



ProjectCompleted



TaskAssigned



InvoicePaid



DocumentUploaded



UserInvited

```



\---



\## Naming Principles



Используются:



\- PascalCase;

\- существительные и глаголы прошедшего времени;

\- бизнес-термины.



\---



\## Forbidden Names



Запрещается использовать:



```

CreateCustomer



CustomerEvent



InsertCustomer



TaskAction



ExecuteWorkflow



RunJob

```



\---



\## Engineering Decision



Имя события должно описывать уже произошедший бизнес-факт.



\---



\# 9. Event Structure



\## Purpose



Все события платформы используют единый формат.



Это обеспечивает совместимость между всеми модулями DevOS.



\---



\## Standard Event Structure



```json

{

&#x20; "eventId": "evt\_01H...",

&#x20; "eventType": "CustomerCreated",

&#x20; "version": "1.0",

&#x20; "timestamp": "2026-01-15T10:30:00Z",

&#x20; "organizationId": "org\_001",

&#x20; "aggregateId": "customer\_123",

&#x20; "payload": {},

&#x20; "metadata": {}

}

```



\---



\## Required Fields



Каждое событие обязано содержать:



| Field | Description |

|---------|-------------|

| eventId | Уникальный идентификатор события |

| eventType | Тип события |

| version | Версия контракта события |

| timestamp | Время публикации |

| organizationId | Организация-владелец |

| aggregateId | Идентификатор бизнес-сущности |

| payload | Полезная нагрузка |

| metadata | Служебная информация |



\---



\## Payload Principles



Payload содержит только данные, необходимые подписчикам.



Не допускается:



\- передача ORM-объектов;

\- внутренних моделей;

\- технических зависимостей.



\---



\## Engineering Decision



Контракт события считается публичным API между модулями и должен поддерживать обратную совместимость.



\---



\# 10. Event Metadata



\## Purpose



Metadata содержит информацию, необходимую для трассировки, мониторинга и аудита.



\---



\## Standard Metadata



```json

{

&#x20; "correlationId": "...",

&#x20; "requestId": "...",

&#x20; "userId": "...",

&#x20; "sourceModule": "CRM",

&#x20; "environment": "production"

}

```



\---



\## Required Metadata



Каждое событие должно содержать:



\- Correlation ID;

\- Request ID;

\- Source Module;

\- User ID (если применимо);

\- Environment;

\- Event Version.



\---



\## Correlation ID



Correlation ID объединяет цепочку связанных событий.



Пример:



```

CustomerCreated



↓



WorkflowStarted



↓



NotificationSent



↓



AuditRecorded

```



Все события цепочки имеют одинаковый Correlation ID.



\---



\## Engineering Decision



Все распределённые операции должны поддерживать сквозную трассировку.



\---



\# 11. Event Lifecycle



\## Purpose



Каждое событие проходит единый жизненный цикл.



\---



\## Lifecycle Stages



```

Business Action



↓



Event Creation



↓



Validation



↓



Publication



↓



Delivery



↓



Processing



↓



Completion



↓



Archive

```



\---



\## Validation



Перед публикацией выполняется проверка:



\- структуры;

\- версии;

\- обязательных полей;

\- безопасности;

\- размера сообщения.



\---



\## Publication



После успешной проверки событие публикуется в Event Bus.



\---



\## Delivery



Event Bus доставляет событие подписчикам.



\---



\## Processing



Каждый подписчик независимо обрабатывает событие.



Ошибки одного подписчика не должны влиять на остальных.



\---



\## Archive



После обработки событие может быть сохранено для:



\- аудита;

\- аналитики;

\- повторной обработки;

\- восстановления истории.



\---



\## Engineering Decision



Событие считается завершённым только после обработки всеми обязательными подписчиками либо помещения в Dead Letter Queue.



\---



\# 12. Event Bus Architecture



\## Purpose



Event Bus обеспечивает слабую связанность между модулями платформы.



\---



\## Architecture



```

Publisher



↓



Event Bus



↓



Subscriptions



↓



Consumers



↓



Business Services

```



\---



\## Responsibilities



Event Bus отвечает за:



\- публикацию событий;

\- маршрутизацию;

\- доставку;

\- повторные попытки;

\- журналирование;

\- мониторинг.



\---



\## Publisher Rules



Издатель:



\- публикует событие;

\- не знает подписчиков;

\- не ожидает ответа;

\- не зависит от обработчиков.



\---



\## Subscriber Rules



Подписчик:



\- самостоятельно принимает решение об обработке;

\- не влияет на других подписчиков;

\- обязан быть идемпотентным.



\---



\## Engineering Decision



Межмодульное взаимодействие должно осуществляться через Event Bus, если отсутствует необходимость в синхронном ответе.



\---



\# 13. Delivery Guarantees



\## Purpose



Платформа должна гарантировать надёжную доставку событий.



\---



\## Supported Strategies



\### At Most Once



Максимальная производительность.



Допускается потеря сообщения.



Используется редко.



\---



\### At Least Once



Сообщение может быть доставлено повторно.



Потеря сообщения недопустима.



Основная стратегия DevOS.



\---



\### Exactly Once



Используется только там, где это действительно необходимо.



Например:



\- финансовые операции;

\- лицензирование;

\- критические бизнес-процессы.



\---



\## Engineering Decision



По умолчанию DevOS использует стратегию \*\*At Least Once\*\*, а ответственность за корректную повторную обработку лежит на подписчиках.

\# 14. Idempotency Strategy



\## Purpose



Поскольку DevOS использует стратегию доставки \*\*At Least Once\*\*, каждый обработчик событий обязан поддерживать идемпотентность.



Повторная обработка одного и того же события не должна изменять состояние системы повторно.



\---



\## Idempotency Rules



Каждый Consumer обязан:



\- проверять уникальность события;

\- использовать `eventId` как ключ идемпотентности;

\- безопасно игнорировать уже обработанные события;

\- журналировать повторную доставку.



\---



\## Example



```

CustomerCreated



↓



CRM Consumer



↓



Customer Exists?



↓



YES → Ignore



NO → Create Customer

```



\---



\## Engineering Decision



Все Consumers обязаны быть идемпотентными независимо от используемого брокера сообщений.



\---



\# 15. Event Ordering Strategy



\## Purpose



Некоторые бизнес-процессы требуют строгого порядка обработки событий.



\---



\## Ordered Events



Строгий порядок обязателен для:



\- финансовых операций;

\- изменения прав доступа;

\- изменения состояния Workflow;

\- изменения жизненного цикла документов.



\---



\## Unordered Events



Допускается произвольный порядок обработки для:



\- аналитики;

\- уведомлений;

\- журналирования;

\- индексации поиска.



\---



\## Aggregate Ordering



Порядок гарантируется только внутри одной Aggregate Root.



Пример:



```

CustomerCreated



↓



CustomerUpdated



↓



CustomerArchived

```



\---



\## Engineering Decision



Глобальный порядок событий не гарантируется.



Гарантируется только порядок внутри одной бизнес-сущности.



\---



\# 16. Retry Strategy



\## Purpose



Ошибки обработки событий считаются нормальной частью распределенной системы.



DevOS использует механизм повторных попыток.



\---



\## Retry Policy



Рекомендуемая последовательность:



```

Attempt 1



↓



1 minute



↓



Attempt 2



↓



5 minutes



↓



Attempt 3



↓



15 minutes



↓



Attempt 4



↓



1 hour



↓



Dead Letter Queue

```



\---



\## Retry Rules



Повторная попытка допускается только для временных ошибок.



Примеры:



\- временная недоступность базы данных;

\- недоступность внешнего API;

\- сетевые ошибки.



\---



\## Non-Retry Errors



Не требуют повторной обработки:



\- нарушение схемы события;

\- отсутствие обязательных данных;

\- ошибка бизнес-валидации;

\- неизвестная версия события.



\---



\## Engineering Decision



Количество попыток определяется конфигурацией платформы.



\---



\# 17. Dead Letter Queue



\## Purpose



События, которые невозможно обработать после всех попыток, помещаются в отдельную очередь.



\---



\## DLQ Responsibilities



Dead Letter Queue используется для:



\- анализа ошибок;

\- повторной обработки;

\- диагностики;

\- восстановления после исправления причины ошибки.



\---



\## Required Metadata



Каждая запись DLQ содержит:



\- Event ID;

\- Event Type;

\- Consumer;

\- Error Message;

\- Retry Count;

\- Timestamp.



\---



\## Engineering Decision



Удаление сообщений из DLQ вручную запрещено.



Каждое сообщение должно быть либо восстановлено, либо закрыто архитектурным решением.



\---



\# 18. Event Versioning



\## Purpose



Контракты событий могут развиваться без нарушения совместимости.



\---



\## Version Rules



Каждое событие содержит:



```

version

```



\---



\## Backward Compatibility



Допускается:



\- добавление новых необязательных полей;

\- расширение metadata.



Не допускается:



\- удаление обязательных полей;

\- изменение смысла существующих данных;

\- изменение имени события.



\---



\## Deprecation



При изменении контракта:



1\. создается новая версия;

2\. старая поддерживается ограниченное время;

3\. публикуется план миграции.



\---



\## Engineering Decision



Контракт события рассматривается как публичный интерфейс платформы.



\---



\# 19. Event Security



\## Purpose



События могут содержать чувствительную информацию.



Публикация данных должна соответствовать требованиям безопасности.



\---



\## Security Principles



Запрещается публиковать:



\- пароли;

\- секретные ключи;

\- токены;

\- персональные данные без необходимости;

\- внутренние технические объекты.



\---



\## Sensitive Data



Если событие требует передачи чувствительных данных:



\- используется шифрование;

\- применяется маскирование;

\- ограничивается круг подписчиков.



\---



\## Access Control



Подписчики получают только те события, которые разрешены архитектурой платформы.



\---



\## Engineering Decision



Безопасность событий проверяется до публикации в Event Bus.



\---



\# 20. Event Observability



\## Purpose



Каждое событие должно быть полностью наблюдаемым.



\---



\## Monitoring



Для каждого события фиксируются:



\- время публикации;

\- время обработки;

\- длительность обработки;

\- статус;

\- подписчики;

\- ошибки.



\---



\## Logging



Журнал содержит:



\- Event ID;

\- Correlation ID;

\- Consumer;

\- Processing Time;

\- Result.



\---



\## Metrics



Платформа собирает:



\- Events Published;

\- Events Processed;

\- Failed Events;

\- Retry Count;

\- DLQ Count;

\- Average Processing Time.



\---



\## Distributed Tracing



Все события одной бизнес-операции объединяются Correlation ID.



\---



\## Engineering Decision



Любое событие должно быть доступно для трассировки от момента публикации до завершения обработки.



\---



\# 21. Automation Pipeline



\## Purpose



События являются основным механизмом запуска автоматизации.



\---



\## Automation Flow



```

Business Event



↓



Workflow Engine



↓



Conditions



↓



Actions



↓



Notifications



↓



Integrations



↓



Analytics

```



\---



\## Example



```

CustomerCreated



↓



Create Welcome Task



↓



Send Email



↓



Notify Manager



↓



Create CRM Activity



↓



Update Dashboard

```



\---



\## Workflow Rules



Автоматизация должна:



\- быть независимой от бизнес-модуля;

\- использовать только события;

\- не изменять исходное событие;

\- публиковать собственные события после выполнения.



\---



\## Engineering Decision



Workflow Engine никогда не обращается напрямую к внутренней логике других модулей.



Все взаимодействие осуществляется через API или публикацию новых событий.



\---



\# 22. Event Catalog



\## Purpose



Event Catalog является централизованным каталогом всех событий платформы.



Каждый модуль обязан зарегистрировать публикуемые события.



\---



\## Identity Module



\- UserCreated

\- UserUpdated

\- UserActivated

\- UserDeactivated

\- PasswordChanged



\---



\## Organization Module



\- OrganizationCreated

\- OrganizationUpdated

\- OrganizationArchived



\---



\## CRM Module



\- CustomerCreated

\- CustomerUpdated

\- CustomerArchived

\- ContactAdded



\---



\## Projects Module



\- ProjectCreated

\- ProjectStarted

\- ProjectCompleted

\- ProjectArchived



\---



\## Tasks Module



\- TaskCreated

\- TaskAssigned

\- TaskCompleted

\- TaskCancelled



\---



\## Documents Module



\- DocumentUploaded

\- DocumentPublished

\- DocumentArchived

\- DocumentDeleted



\---



\## Automation Module



\- WorkflowStarted

\- WorkflowCompleted

\- WorkflowFailed



\---



\## Notifications Module



\- NotificationQueued

\- NotificationSent

\- NotificationDelivered

\- NotificationFailed



\---



\## Analytics Module



\- DashboardUpdated

\- ReportGenerated

\- MetricsCalculated



\---



\## Engineering Decision



Создание нового события допускается только после проверки существующего Event Catalog во избежание дублирования бизнес-событий.

\# 23. Event Testing Strategy



\## Purpose



Все механизмы обработки событий должны быть покрыты автоматическими тестами.



Цель тестирования:



\- гарантировать корректную публикацию событий;

\- обеспечить совместимость между модулями;

\- исключить потерю сообщений;

\- проверить устойчивость платформы к ошибкам.



\---



\## Testing Levels



\### Unit Tests



Проверяют:



\- создание события;

\- структуру payload;

\- правила валидации;

\- сериализацию.



\---



\### Integration Tests



Проверяют:



\- публикацию события;

\- получение события подписчиками;

\- корректность взаимодействия нескольких модулей.



\---



\### Contract Tests



Проверяют соответствие структуры события утвержденному контракту.



Любое нарушение схемы считается ошибкой архитектуры.



\---



\### Replay Tests



Проверяют возможность повторного воспроизведения событий.



Используются для:



\- восстановления системы;

\- повторного расчета аналитики;

\- тестирования новых обработчиков.



\---



\### Failure Tests



Проверяются сценарии:



\- отказ подписчика;

\- отказ брокера сообщений;

\- переполнение очереди;

\- повторная доставка;

\- попадание события в Dead Letter Queue.



\---



\### Performance Tests



Измеряются:



\- скорость публикации;

\- время доставки;

\- время обработки;

\- производительность при высокой нагрузке.



\---



\## Engineering Decision



Каждый новый Consumer обязан сопровождаться полным набором автоматических тестов до ввода в эксплуатацию.



\---



\# 24. Performance Guidelines



\## Purpose



Событийная архитектура должна обеспечивать высокую производительность и возможность горизонтального масштабирования.



\---



\## Design Principles



Обработчики должны:



\- выполнять минимально необходимую работу;

\- избегать длительных синхронных операций;

\- использовать асинхронную обработку;

\- публиковать новые события вместо прямых вызовов модулей.



\---



\## Queue Management



Очереди должны поддерживать:



\- горизонтальное масштабирование;

\- автоматическое распределение нагрузки;

\- контроль размера очередей;

\- мониторинг задержек.



\---



\## Batch Processing



Для массовых операций допускается пакетная обработка событий.



Например:



\- импорт клиентов;

\- генерация отчетов;

\- массовые уведомления.



\---



\## Monitoring Metrics



Платформа должна отслеживать:



\- Events Per Second (EPS);

\- Average Processing Time;

\- Queue Length;

\- Retry Count;

\- DLQ Size;

\- Consumer Latency.



\---



\## Engineering Decision



Производительность событийной системы является архитектурным требованием и контролируется непрерывно.



\---



\# 25. Event Development Checklist



Перед публикацией нового события необходимо убедиться, что:



✓ событие отражает бизнес-факт;



✓ событие отсутствует в Event Catalog;



✓ определена категория события;



✓ выбрано корректное имя;



✓ определена версия;



✓ описан payload;



✓ заполнены metadata;



✓ проверены требования безопасности;



✓ реализована идемпотентность;



✓ добавлены автоматические тесты;



✓ обновлена документация;



✓ зарегистрировано событие в Event Catalog.



\---



\# 26. Decision Impact



Настоящий документ определяет единый стандарт событийной архитектуры DevOS.



Все существующие и будущие модули обязаны использовать данный стандарт при публикации и обработке событий.



Любое отклонение допускается только после утверждения соответствующего Architecture Decision Record (ADR).



\---



\# 27. Related Documents



\- 05\_Core\_Modules.md

\- 05\_DevOS\_Architecture\_Foundation.md

\- 05A\_Architecture\_Rules.md

\- 06\_System\_Design.md

\- 07\_Module\_Specification.md

\- 08\_Database\_Design.md

\- 09\_API\_Design.md

\- 11\_Security\_Model.md

\- 12\_Product\_Roadmap.md



\---



\# 28. Open Questions



Следующие вопросы требуют дальнейшей проработки:



\- выбор конкретного брокера сообщений (RabbitMQ, Kafka, NATS и др.);

\- стратегия хранения исторических событий;

\- применение Event Sourcing для отдельных модулей;

\- поддержка распределенных транзакций;

\- политика долгосрочного хранения Event Catalog.



\---



\# 29. Decision Log



| Version | Decision | Rationale |

|---------|----------|-----------|

| 1.0 | Business Events как основа архитектуры | Снижение связанности модулей |

| 1.0 | Event Bus как основной механизм взаимодействия | Масштабируемость платформы |

| 1.0 | At Least Once по умолчанию | Надежность доставки |

| 1.0 | Event Catalog обязателен | Исключение дублирования событий |

| 1.0 | Workflow запускается событиями | Независимость автоматизации |

| 1.0 | Идемпотентность обязательна | Корректная повторная обработка |



\---



\# 30. Research Quality



\## Sources



Документ основан на:



\- предыдущих исследованиях DevOS;

\- Enterprise Integration Patterns;

\- Domain-Driven Design;

\- Event-Driven Architecture;

\- анализе современных SaaS-платформ;

\- лучших практиках построения распределенных систем.



\---



\## Confidence Level



Высокий.



Архитектурные решения согласованы с:



\- моделью Business Capability;

\- модульной архитектурой DevOS;

\- Database Design;

\- API Design;

\- Architecture Rules.



\---



\# 31. Change History



| Version | Changes |

|---------|---------|

| 1.0 | Первое утвержденное издание документа |
