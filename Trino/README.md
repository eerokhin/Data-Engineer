# Trino — архитектура и принципы работы

## 1. Что такое Trino

**Trino** — распределённый SQL query engine для выполнения аналитических запросов к большим объёмам данных, находящихся в различных источниках.

Trino позволяет обращаться к разнородным системам через единый SQL-интерфейс:

- PostgreSQL
- MySQL
- Apache Iceberg
- Hive
- Kafka
- ClickHouse
- S3-совместимые хранилища через табличные форматы и коннекторы

Основная идея: не нужно переносить все данные в одну базу, чтобы выполнять над ними аналитические SQL-запросы.

Trino подключается к источникам через коннекторы, получает метаданные и выполняет запросы, в том числе объединяя данные из разных систем.

### Важно

Trino — это не классическая реляционная СУБД.

Он:
- не предназначен для OLTP-нагрузок;
- не является самостоятельным хранилищем данных;
- не обязан физически хранить таблицы;
- выполняет SQL-запросы к внешним источникам;
- может распределять вычисления между несколькими серверами.

---

## 2. Архитектура Trino

Trino использует распределённую архитектуру.

Кластер состоит из двух основных типов узлов:

- Coordinator
- Worker

```text
                  User / DBeaver
                        |
                        | SQL
                        v
                +---------------+
                |   Coordinator |
                |               |
                | Parse SQL     |
                | Plan Query    |
                | Optimize      |
                | Schedule      |
                +---------------+
                        |
              Distribute Tasks
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
    +-----------+ +-----------+ +-----------+
    |  Worker 1 | |  Worker 2 | |  Worker 3 |
    |           | |           | |           |
    | Execute   | | Execute   | | Execute   |
    | Tasks     | | Tasks     | | Tasks     |
    +-----------+ +-----------+ +-----------+
          |             |             |
          +-------------+-------------+
                        |
                        v
                 Data Sources
              /       |       \
             v        v        v
        PostgreSQL  MinIO    Other DBs
                    Iceberg
```

### Coordinator

Coordinator — управляющий узел кластера.

Отвечает за:
- получение SQL-запросов от клиентов;
- синтаксический разбор SQL;
- построение плана выполнения;
- оптимизацию запроса;
- распределение задач между Worker;
- управление выполнением запросов;
- возврат результатов клиенту.

Coordinator не должен выполнять всю вычислительную работу за кластер.

### Worker

Worker — вычислительный узел.

Отвечает за:
- чтение данных из источников через коннекторы;
- обработку данных;
- фильтрацию и преобразования;
- JOIN и агрегации;
- передачу промежуточных результатов другим Worker.

В зависимости от конфигурации Worker могут выполнять разные части одного SQL-запроса параллельно.

### Node

Node — отдельный запущенный процесс Trino в кластере.

Один кластер может содержать:
- один Coordinator;
- несколько Worker.

Для небольших тестовых окружений один экземпляр Trino может одновременно выполнять роли Coordinator и Worker.

---

## 3. Connector и Catalog

Одна из главных особенностей Trino — возможность подключать разные источники данных.

Для этого используются Connector и Catalog.

### Connector

Connector — компонент, который обеспечивает взаимодействие Trino с конкретным источником данных.

По смыслу похож на JDBC-драйвер, но предоставляет Trino более широкий интерфейс для работы с метаданными, чтением и, если поддерживается, записью данных.

Примеры:
- PostgreSQL Connector;
- Iceberg Connector;
- Hive Connector;
- MySQL Connector;
- Kafka Connector.

### Catalog

Catalog — конфигурация подключения к источнику данных.

В ней указываются:
- используемый Connector;
- адрес источника;
- параметры подключения;
- учётные данные;
- дополнительные настройки.

Catalog создаётся через properties-файл в каталоге конфигурации Trino.

Например:

`etc/catalog/postgres.properties`

```properties
connector.name=postgresql

connection-url=jdbc:postgresql://postgres:5432/hr_source
connection-user=${ENV:POSTGRES_USER}
connection-password=${ENV:POSTGRES_PASSWORD}
```

Имя файла определяет имя Catalog.

В данном случае Catalog называется `postgres`.

Другой пример:

`etc/catalog/iceberg.properties`

```properties
connector.name=iceberg
```

Это только минимальный фрагмент: для полноценного подключения Iceberg также необходимы настройки каталога метаданных и файлового хранилища.

### Пример нескольких Catalog

```text
                   Trino
                     |
        +------------+------------+
        |            |            |
        v            v            v
    postgres      iceberg       mysql
        |            |            |
        v            v            v
    PostgreSQL     Iceberg       MySQL
                   Connector
                      |
                      v
                   MinIO/S3
```

Trino может одновременно работать с несколькими Catalog, даже если они используют разные Connector.

---

## 4. Schema и Table

Структура объектов Trino:

```text
Trino
  |
  +-- Catalog
        |
        +-- Schema
              |
              +-- Table
              +-- View
              +-- Materialized View
```

### Catalog

Логическое подключение к источнику данных.

### Schema

Логическая группа таблиц внутри Catalog.

### Table

Таблица, доступная через Trino.

Полное имя таблицы:

```sql
catalog.schema.table
```

Примеры:

```sql
-- PostgreSQL
SELECT *
FROM postgres.public.customers;

-- Iceberg
SELECT *
FROM iceberg.lab.test_orders;
```

---

## 5. Как Trino выполняет SQL-запрос

Когда пользователь отправляет SQL, Trino преобразует его в распределённый план выполнения.

Упрощённая последовательность:

```text
SQL Query
    |
    v
Parsing
    |
    v
Analysis
    |
    v
Logical Plan
    |
    v
Optimization
    |
    v
Distributed Plan
    |
    v
Stages
    |
    v
Tasks
    |
    v
Splits
    |
    v
Drivers
    |
    v
Operators
    |
    v
Result
```

### Parsing

Проверка синтаксиса SQL.

### Analysis

Проверка таблиц, колонок, типов данных и доступных объектов.

### Optimization

Оптимизатор старается построить эффективный план выполнения.

В частности, может применяться:
- Predicate Pushdown;
- Projection Pushdown;
- Join Reordering;
- Dynamic Filtering;
- Cost-Based Optimization.

### Distributed Plan

Trino разбивает запрос на части, которые могут выполняться параллельно.

Для этого используются следующие понятия.

| Компонент | Назначение |
|---|---|
| Query | Выполняемый SQL-запрос |
| Stage | Логическая часть распределённого плана |
| Task | Исполняемая единица Stage на Worker |
| Split | Часть данных, которую нужно обработать |
| Driver | Последовательность операторов обработки |
| Operator | Конкретная операция над данными |
| Exchange | Передача данных между Stage |

### Stage

Stage — часть распределённого плана запроса.

Например, один Stage может читать данные, другой — выполнять JOIN, третий — агрегировать результат.

### Task

Task — исполняемая единица Stage, распределённая по Worker.

### Split

Split — часть набора данных, которую Trino может обрабатывать независимо от других частей.

Например, таблица может состоять из множества Parquet-файлов. Connector предоставляет Trino информацию о доступных частях данных, которые могут быть обработаны параллельно.

### Driver

Driver — последовательность операторов, которая обрабатывает данные.

### Operator

Operator выполняет конкретную операцию:

- Table Scan;
- Filter;
- Project;
- Join;
- Aggregation;
- Sort.

### Exchange

Exchange отвечает за передачу промежуточных данных между Stage и Worker.

Например, при JOIN данные могут перераспределяться между Worker по ключу соединения.

---

## 6. Как Trino работает с разными источниками

Trino не требует, чтобы данные физически находились в одном хранилище.

Например, есть:

- таблица customers в PostgreSQL;
- таблица orders в Iceberg на MinIO.

Можно выполнить:

```sql
SELECT
    c.customer_id,
    c.customer_name,
    o.order_id,
    o.amount
FROM postgres.public.customers c
JOIN iceberg.lab.orders o
    ON c.customer_id = o.customer_id;
```

Упрощённо процесс выглядит так:

1. Trino получает запрос.
2. Coordinator определяет, какие Catalog участвуют.
3. Connector получает информацию о таблицах и доступных данных.
4. Оптимизатор строит план выполнения.
5. Worker читают данные из PostgreSQL и Iceberg.
6. Trino выполняет JOIN.
7. Результат возвращается клиенту.

Важно: фактический план и место выполнения отдельных операций зависят от возможностей Connector и оптимизатора.

---

## 7. Predicate Pushdown и Projection Pushdown

Это важные механизмы оптимизации.

### Predicate Pushdown

Перенос фильтрации ближе к источнику данных.

Например:

```sql
SELECT *
FROM postgres.public.orders
WHERE order_date >= DATE '2026-01-01';
```

Если Connector и источник поддерживают pushdown, фильтрация может выполняться непосредственно в PostgreSQL.

Вместо передачи всех строк Trino получает только подходящие данные.

### Projection Pushdown

Чтение только необходимых колонок.

Например:

```sql
SELECT
    customer_id,
    amount
FROM iceberg.lab.orders;
```

Если формат и Connector позволяют, Trino читает только нужные колонки из Parquet, а не всю таблицу.

Это особенно полезно при работе с широкими таблицами.

---

## 8. Trino и Iceberg

Trino — движок выполнения SQL-запросов.

Apache Iceberg — табличный формат, который управляет состоянием таблиц, метаданными и файлами данных.

MinIO — объектное хранилище, в котором физически находятся файлы.

Вместе они образуют часть Lakehouse-архитектуры.

```text
                  DBeaver
                     |
                     v
                   Trino
                     |
                     v
              Iceberg Connector
                     |
          +----------+----------+
          |                     |
          v                     v
    Nessie Catalog          MinIO / S3
    Table Metadata          Data Files
                            Metadata Files
```

В нашем проекте:
- Trino выполняет SQL;
- Iceberg управляет таблицами;
- Nessie используется как каталог метаданных Iceberg;
- MinIO хранит Parquet-файлы и Iceberg metadata.

### Как выглядит Iceberg-таблица

```text
warehouse/
    lab/
        test_orders/
            data/
                *.parquet

            metadata/
                *.metadata.json
                snap-*.avro
                manifest-*.avro
```

Parquet — формат хранения данных.

Iceberg — табличный формат, который управляет файлами данных и метаданными таблицы.

Nessie — каталог, который позволяет Trino находить и изменять состояние Iceberg-таблиц.

---

## 9. Trino — не ETL-инструмент

Trino хорошо подходит для:
- аналитических запросов;
- объединения данных из разных источников;
- чтения больших таблиц;
- агрегаций;
- аналитики поверх Data Lake и Lakehouse.

Но Trino не заменяет инструменты оркестрации и полноценные ETL-платформы.

В типичной архитектуре:

| Инструмент | Назначение |
|---|---|
| Airflow | Оркестрация процессов |
| Trino | SQL-запросы и аналитические вычисления |
| Iceberg | Табличный формат Lakehouse |
| MinIO / S3 | Объектное хранилище |
| Nessie | Каталог и управление состоянием таблиц |
| dbt | SQL-трансформации и тестирование моделей |
| PostgreSQL | Реляционная база данных |

Например, Airflow может запускать dbt-модели, которые выполняют SQL-трансформации через Trino и записывают результат в Iceberg.

---

## 10. Основные команды Trino SQL

### Просмотр Catalog

```sql
SHOW CATALOGS;
```

### Просмотр Schema

```sql
SHOW SCHEMAS FROM iceberg;
```

### Просмотр таблиц

```sql
SHOW TABLES FROM iceberg.lab;
```

### Просмотр структуры таблицы

```sql
DESCRIBE iceberg.lab.test_orders;
```

### Просмотр DDL

```sql
SHOW CREATE TABLE iceberg.lab.test_orders;
```

### Чтение данных

```sql
SELECT *
FROM iceberg.lab.test_orders;
```

### Создание Schema

```sql
CREATE SCHEMA iceberg.bronze
WITH (
    location = 's3://warehouse/bronze/'
);
```

### Создание таблицы

```sql
CREATE TABLE iceberg.bronze.orders (
    order_id BIGINT,
    customer_id BIGINT,
    amount DECIMAL(10, 2)
)
WITH (
    format = 'PARQUET'
);
```

### Получение плана выполнения

```sql
EXPLAIN
SELECT *
FROM iceberg.lab.test_orders;
```

### Анализ выполнения

```sql
EXPLAIN ANALYZE
SELECT *
FROM iceberg.lab.test_orders;
```

---

## 11. Trino в нашем Lakehouse-проекте

Используем следующий стек:

- Trino 484
- Apache Iceberg
- MinIO
- Project Nessie
- PostgreSQL
- dbt Core
- Docker Compose

Архитектура:

```text
                 Data Sources
                      |
               +------+------+
               |             |
               v             v
           PostgreSQL     Source Files
               |             |
               +------+------+
                      |
                      v
                MinIO / S3
                      |
                      v
                Iceberg Tables
                      |
                 Nessie Catalog
                      |
                      v
                    Trino
                      |
               +------+------+
               |             |
               v             v
             DBeaver         dbt
                               |
                               v
                         SQL Models
                               |
                               v
                         Iceberg Tables
```

Trino выступает SQL-движком, через который мы читаем и преобразуем данные в Lakehouse.

---

## 12. Ключевые выводы

1. Trino — распределённый SQL query engine, а не база данных.
2. Coordinator управляет выполнением запросов.
3. Worker выполняют вычислительные задачи.
4. Connector обеспечивает взаимодействие с источником данных.
5. Catalog содержит конфигурацию подключения к источнику.
6. Schema организует таблицы внутри Catalog.
7. Полное имя таблицы имеет вид `catalog.schema.table`.
8. Trino может объединять данные из разных источников в одном SQL-запросе.
9. Stage, Task, Split, Driver и Operator — элементы модели выполнения распределённого запроса.
10. Iceberg управляет таблицами и их метаданными, MinIO хранит файлы, Nessie управляет каталогом таблиц.

## Полезные ссылки

- [Trino Documentation](https://trino.io/docs/current/)
- [Trino Concepts](https://trino.io/docs/current/overview/concepts.html)
- [Trino Architecture](https://trino.io/docs/current/overview/concepts.html#architecture)
- [Trino Connectors](https://trino.io/docs/current/connector.html)
- [Trino Iceberg Connector](https://trino.io/docs/current/connector/iceberg.html)
- [Trino PostgreSQL Connector](https://trino.io/docs/current/connector/postgresql.html)
- [Проект](https://github.com/eerokhin/trino-iceberg-lab)
