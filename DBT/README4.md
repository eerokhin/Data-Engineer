# Практика dbt: создание модели, тестирование и зависимости

В рамках практического знакомства с dbt реализован небольшой ETL/ELT-процесс на примере таблицы заказов.

Цель — разобраться, как dbt работает с источниками данных, SQL-моделями, Jinja, тестами качества данных и зависимостями между моделями.

В качестве источника используется PostgreSQL, для хранения результатов трансформаций — Apache Iceberg через Trino.

## 1. Архитектура примера

Используем следующий стек:

- PostgreSQL — источник данных.
- Trino — SQL-движок и интерфейс доступа к данным.
- Apache Iceberg — формат хранения аналитических таблиц.
- dbt Core — управление SQL-трансформациями и тестированием.

Общий процесс:

```text
PostgreSQL
    |
    | dbt source()
    v
public.dbt_demo_orders
    |
    | TRIM(), UPPER()
    v
iceberg.silver.stg_orders
    |
    | dbt ref()
    v
iceberg.silver.dm_orders_summary
```

На первом этапе данные очищаются и нормализуются. На втором — формируется агрегированная модель с количеством заказов, общей и средней суммой по статусам.

## 2. Создание исходной таблицы

В PostgreSQL создана таблица `dbt_demo_orders`.

```sql
CREATE TABLE dbt_demo_orders (
    order_id INTEGER PRIMARY KEY,
    customer_name VARCHAR(100),
    amount NUMERIC(10, 2),
    order_status VARCHAR(30),
    order_date DATE
);

INSERT INTO dbt_demo_orders VALUES
(1, '  Ivan Petrov  ', 1500.00, 'COMPLETED', '2026-10-01'),
(2, 'Anna Smith', 2500.50, 'completed', '2026-10-02'),
(3, '  John Brown', 800.00, 'PENDING', '2026-10-03'),
(4, 'Maria Green  ', 3200.00, 'CANCELLED', '2026-10-04'),
(5, 'Alex White', 1200.00, 'completed', '2026-10-05');
```

В исходных данных намеренно оставлены проблемы качества:

- пробелы в начале и конце имён;
- разный регистр значений `order_status`.

Это позволяет на практике проверить работу SQL-трансформаций и тестов dbt.

## 3. Объявление источника в dbt

Файл: `dbt/models/sources.yml`

```yaml
version: 2

sources:
  - name: bronze
    database: iceberg
    schema: bronze
    tables:
      - name: employees
      - name: departments
      - name: positions
      - name: employment_history
      - name: employee_events

  - name: demo
    database: postgres
    schema: public
    tables:
      - name: dbt_demo_orders
```

В проекте уже существовал источник `bronze`, поэтому новый источник `demo` добавлен в тот же список `sources`.

**Что здесь важно:**

- `name: demo` — логическое имя источника внутри dbt.
- `database: postgres` — каталог Trino, через который доступен PostgreSQL.
- `schema: public` — схема PostgreSQL.
- `tables` — перечень доступных исходных таблиц.

Объявление источника позволяет обращаться к нему через `source()`.

Проверка обнаружения источников:

```powershell
dbt ls --project-dir .\dbt --resource-type source
```

В результате dbt обнаружил шесть источников, включая `demo.dbt_demo_orders`.

## 4. Создание staging-модели

Файл: `dbt/models/stg_orders.sql`

```sql
{{ config(materialized='table') }}

SELECT
    order_id,
    TRIM(customer_name) AS customer_name,
    amount,
    UPPER(TRIM(order_status)) AS order_status,
    order_date
FROM {{ source('demo', 'dbt_demo_orders') }}
```

**Разберём основные элементы.**

### config()

```sql
{{ config(materialized='table') }}
```

Определяет способ материализации модели.

В данном случае dbt создаёт физическую таблицу, а не представление.

Основные варианты материализации:

| Тип | Описание |
|---|---|
| view | Представление в базе данных |
| table | Физическая таблица |
| incremental | Инкрементальное обновление модели |
| ephemeral | SQL-модель, встраиваемая в другие модели как CTE |

### source()

```sql
{{ source('demo', 'dbt_demo_orders') }}
```

Обращение к ранее объявленному источнику.

dbt подставляет фактическое имя таблицы на основании `sources.yml`.

### SQL-трансформации

```sql
TRIM(customer_name) AS customer_name
```

Удаляет пробелы в начале и конце имени.

```sql
UPPER(TRIM(order_status)) AS order_status
```

Удаляет пробелы и приводит статус к верхнему регистру.

Таким образом, staging-модель отвечает за первичную очистку и стандартизацию исходных данных.

### Запуск модели

```powershell
dbt run --project-dir .\dbt --select stg_orders
```

Результат:

```text
Done. PASS=1 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=1
```

Создана таблица:

```text
iceberg.silver.stg_orders
```

Проверка результата в DBeaver через Trino:

```sql
SELECT *
FROM iceberg.silver.stg_orders
ORDER BY order_id;
```

## 5. Компиляция SQL

Для просмотра SQL, который генерирует dbt, использовалась команда:

```powershell
dbt compile --project-dir .\dbt --select stg_orders
```

Исходная модель содержит Jinja:

```sql
FROM {{ source('demo', 'dbt_demo_orders') }}
```

После компиляции получается обычный SQL:

```sql
FROM "postgres"."public"."dbt_demo_orders"
```

Таким образом, dbt заменяет Jinja-выражения реальными именами объектов Trino.

Скомпилированный файл:

```text
dbt/target/compiled/trino_iceberg_lab/models/stg_orders.sql
```

Важно различать:

- исходный SQL — модель, которую разрабатывает инженер;
- compiled SQL — результат обработки Jinja и конфигураций;
- materialized table — физический результат выполнения модели.

`dbt compile` генерирует SQL, но не создаёт таблицу и не выполняет трансформацию.

## 6. Generic Tests — стандартные тесты качества данных

Для проверки качества модели в `dbt/models/schema.yml` добавлена конфигурация:

```yaml
  - name: stg_orders
    description: "Cleaned staging model for customer orders"

    columns:
      - name: order_id
        description: "Unique order identifier"
        tests:
          - unique
          - not_null

      - name: customer_name
        tests:
          - not_null

      - name: order_status
        tests:
          - accepted_values:
              arguments:
                values:
                  - COMPLETED
                  - PENDING
                  - CANCELLED
```

В dbt Generic Tests — это готовые типовые проверки, которые можно применять к моделям и их колонкам.

Использованные проверки:

| Тест | Назначение |
|---|---|
| unique | Проверяет отсутствие дубликатов |
| not_null | Проверяет отсутствие NULL |
| accepted_values | Проверяет соответствие значения заданному списку |

Например:

```yaml
- name: order_id
  tests:
    - unique
    - not_null
```

означает, что идентификатор заказа должен быть уникальным и обязательным для заполнения.

Проверка:

```powershell
dbt test --project-dir .\dbt --select stg_orders
```

Результат:

```text
Done. PASS=4 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=4
```

Все четыре Generic Tests успешно прошли.

## 7. Singular Test — пользовательская проверка бизнес-правила

Помимо готовых тестов dbt позволяет создавать собственные проверки на SQL.

Файл:

```text
dbt/tests/assert_stg_orders_positive_amount.sql
```

Содержимое:

```sql
SELECT *
FROM {{ ref('stg_orders') }}
WHERE amount <= 0
```

Это Singular Test.

**Принцип работы:**

- Тест выполняет SQL-запрос.
- Запрос ищет записи, нарушающие бизнес-правило.
- Если запрос возвращает ноль строк — тест проходит.
- Если найдены записи — тест завершается ошибкой.

В нашем примере проверяется, что сумма каждого заказа должна быть положительной.

Здесь используется `ref('stg_orders')`, потому что тест проверяет результат другой dbt-модели.

После добавления Singular Test общее количество проверок для `stg_orders` стало равно пяти:

- 4 Generic Tests;
- 1 Singular Test.

## 8. Проверка обнаружения некорректных данных

Чтобы проверить работу Data Quality, намеренно изменили исходные данные в PostgreSQL:

```sql
UPDATE dbt_demo_orders
SET order_status = 'UNKNOWN'
WHERE order_id = 5;
```

Затем выполнили:

```powershell
dbt build --project-dir .\dbt --select stg_orders
```

Результат:

```text
PASS=5 WARN=0 ERROR=1 SKIP=0 NO-OP=0 TOTAL=6
```

Тест `accepted_values` завершился ошибкой.

Ключевое сообщение:

```text
Got 1 result, configured to fail if != 0
```

Это означает, что проверочный SQL нашёл одну запись с недопустимым статусом.

При этом остальные проверки прошли успешно.

**Важный момент:** dbt не исправляет некорректные данные автоматически. Он обнаруживает нарушение правил качества и сообщает о нём.

После этого исходные данные были восстановлены:

```sql
UPDATE dbt_demo_orders
SET order_status = 'COMPLETED'
WHERE order_id = 5;
```

Повторно выполнили:

```powershell
dbt build --project-dir .\dbt --select stg_orders
```

Результат:

```text
PASS=6 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=6
```

Все проверки прошли успешно.

## 9. Создание агрегированной модели

Создана вторая модель:

```text
dbt/models/dm_orders_summary.sql
```

Содержимое:

```sql
{{ config(materialized='table') }}

SELECT
    order_status,
    COUNT(*) AS orders_count,
    SUM(amount) AS total_amount,
    ROUND(AVG(amount), 2) AS avg_amount
FROM {{ ref('stg_orders') }}
GROUP BY order_status
```

Модель формирует агрегированную статистику по статусам заказов:

- количество заказов;
- общая сумма заказов;
- средняя сумма заказа.

### Что такое ref()

```sql
{{ ref('stg_orders') }}
```

`ref()` используется для обращения к другой dbt-модели.

В отличие от `source()`, который обращается к внешнему источнику данных, `ref()` связывает модели внутри проекта dbt.

Кроме подстановки физического имени таблицы, `ref()` сообщает dbt о зависимости между моделями.

В нашем случае:

```text
stg_orders → dm_orders_summary
```

Это позволяет dbt автоматически определить порядок выполнения зависимых моделей.

### Компиляция второй модели

```powershell
dbt compile --project-dir .\dbt --select dm_orders_summary
```

Скомпилированный SQL:

```sql
SELECT
    order_status,
    COUNT(*) AS orders_count,
    SUM(amount) AS total_amount,
    ROUND(AVG(amount), 2) AS avg_amount
FROM "iceberg"."silver"."stg_orders"
GROUP BY order_status
```

dbt заменил `ref('stg_orders')` на физическое имя таблицы Iceberg.

## 10. Запуск зависимых моделей

Для запуска выбранной модели вместе со всеми её upstream-зависимостями использовалась команда:

```powershell
dbt run --project-dir .\dbt --select +dm_orders_summary
```

Символ `+` перед именем модели означает, что dbt должен включить её upstream-зависимости.

В результате dbt выполнил:

```text
1 of 2 START sql table model silver.stg_orders
1 of 2 OK created sql table model silver.stg_orders

2 of 2 START sql table model silver.dm_orders_summary
2 of 2 OK created sql table model silver.dm_orders_summary
```

Результат:

```text
Done. PASS=2 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=2
```

Созданы две физические таблицы:

```text
iceberg.silver.stg_orders
iceberg.silver.dm_orders_summary
```

В данном учебном примере `dm_orders_summary` оставлена в схеме Silver. Файл расположен непосредственно в `models/`, поэтому к нему применяется конфигурация корневого каталога моделей. Перемещение и изменение конфигурации для этого упражнения не выполнялись.

## 11. dbt run, dbt test и dbt build

В ходе практики использовались три основные команды.

| Команда | Назначение |
|---|---|
| dbt run | Выполняет модели |
| dbt test | Запускает тесты качества данных |
| dbt build | Строит выбранные ресурсы и запускает связанные тесты |

Примеры:

```powershell
# Построить одну модель
dbt run --project-dir .\dbt --select stg_orders

# Запустить тесты модели
dbt test --project-dir .\dbt --select stg_orders

# Построить модель и выполнить её тесты
dbt build --project-dir .\dbt --select stg_orders

# Построить модель вместе с upstream-зависимостями
dbt run --project-dir .\dbt --select +dm_orders_summary
```

Важное различие: `dbt test` не пересобирает модель. Если исходные данные изменились, а модель материализована как таблица, сначала нужно обновить модель, например через `dbt run` или `dbt build`.

## 12. Что изучено в ходе практики

В результате упражнения на небольшом примере разобраны следующие возможности dbt:

1. Объявление внешних источников через `sources.yml`.
2. Обращение к источникам через `source()`.
3. Создание SQL-моделей.
4. Использование Jinja и `config()`.
5. Материализация моделей в физические таблицы.
6. Компиляция Jinja в обычный SQL.
7. Использование `ref()` для построения зависимостей.
8. Generic Tests для типовых проверок качества данных.
9. Singular Tests для пользовательских бизнес-правил.
10. Обнаружение некорректных данных через Data Quality.
11. Запуск моделей с учётом зависимостей.
12. Различия между `dbt run`, `dbt test` и `dbt build`.

## Итог

На примере небольшой таблицы заказов реализован полноценный учебный процесс трансформации данных:

**PostgreSQL → dbt staging → dbt aggregation → Iceberg.**

Практика помогла понять, как dbt организует SQL-трансформации, связывает модели между собой, компилирует Jinja-выражения и обеспечивает контроль качества данных с помощью тестов.

Это локальный учебный пример, предназначенный для изучения dbt Core и интеграции с Trino и Apache Iceberg.
