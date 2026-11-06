# Как dbt определяет схему для создания моделей

## 1. Общий принцип

dbt определяет, в какой схеме создавать таблицу, на основании нескольких конфигураций:

1. `profiles.yml` — настройки подключения к базе данных и схема по умолчанию.
2. `dbt_project.yml` — настройки проекта, моделей, каталогов и путей.
3. `generate_schema_name.sql` — макрос, который определяет итоговое имя схемы.

В нашем HR Lakehouse используются две основные схемы:

- **Silver** — очищенные и подготовленные данные.
- **Gold** — аналитические витрины.

Каталог Trino — `iceberg`.

Итоговые таблицы создаются по следующему принципу:

```text
iceberg.silver.stg_employees
iceberg.gold.dm_employee_headcount
```

Где:
- `iceberg` — каталог Trino;
- `silver` / `gold` — схема;
- `stg_employees` / `dm_employee_headcount` — таблица.

---

## 2. Структура проекта dbt

```text
dbt/
│
├── dbt_project.yml
│
├── macros/
│   └── generate_schema_name.sql
│
├── models/
│   │
│   ├── sources.yml
│   ├── schema.yml
│   │
│   ├── silver/
│   │   ├── stg_employees.sql
│   │   ├── stg_departments.sql
│   │   ├── stg_positions.sql
│   │   ├── stg_employment_history.sql
│   │   └── stg_employee_events.sql
│   │
│   └── gold/
│       ├── dm_employee_headcount.sql
│       ├── dm_employee_turnover.sql
│       └── dm_employee_movements.sql
│
└── tests/
    ├── assert_dm_employee_turnover_unique_grain.sql
    ├── assert_dm_employee_headcount_unique_grain.sql
    ├── assert_dm_employee_movements_unique_event.sql
    └── ...
```

### Назначение основных файлов и папок

| Файл / папка | Назначение |
|---|---|
| `dbt_project.yml` | Основная конфигурация проекта dbt |
| `profiles.yml` | Подключение к Trino, каталог, схема по умолчанию |
| `models/` | SQL-модели для трансформации данных |
| `models/silver/` | Модели слоя Silver |
| `models/gold/` | Модели слоя Gold |
| `sources.yml` | Описание исходных источников данных |
| `schema.yml` | Описание моделей и общие тесты |
| `macros/` | Пользовательские Jinja-макросы |
| `tests/` | SQL-тесты, написанные вручную |

`profiles.yml` находится отдельно от проекта, обычно в `~/.dbt/profiles.yml`. В нашем случае — `C:\Users\<username>\.dbt\profiles.yml`.

---

## 3. Полная конфигурация dbt_project.yml

Файл `dbt_project.yml` — основной конфигурационный файл dbt-проекта.

Он определяет:
- имя и версию проекта;
- профиль подключения;
- расположение моделей, тестов, макросов и других ресурсов;
- каталоги, которые удаляются командой `dbt clean`;
- настройки материализации моделей;
- настройки схем для разных групп моделей.

Полное содержимое нашего файла:

```yaml
name: trino_iceberg_lab
version: '1.0.0'
config-version: 2

profile: hr_dbt

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

clean-targets:
  - "target"
  - "dbt_packages"

models:
  trino_iceberg_lab:
    +materialized: view

    silver:
      +schema: silver
      +materialized: table

    gold:
      +schema: gold
      +materialized: table
```

### Разбор параметров

| Параметр | Значение | Назначение |
|---|---|---|
| `name` | `trino_iceberg_lab` | Имя dbt-проекта |
| `version` | `1.0.0` | Версия проекта |
| `config-version` | `2` | Версия формата конфигурации dbt |
| `profile` | `hr_dbt` | Имя профиля из `profiles.yml` |
| `model-paths` | `models` | Папка SQL-моделей |
| `analysis-paths` | `analyses` | Папка аналитических SQL-файлов |
| `test-paths` | `tests` | Папка пользовательских тестов |
| `seed-paths` | `seeds` | Папка CSV-файлов для загрузки через dbt seed |
| `macro-paths` | `macros` | Папка Jinja-макросов |
| `snapshot-paths` | `snapshots` | Папка dbt snapshots |
| `clean-targets` | `target`, `dbt_packages` | Каталоги, удаляемые через `dbt clean` |

### Настройка моделей

```yaml
models:
  trino_iceberg_lab:
    +materialized: view

    silver:
      +schema: silver
      +materialized: table

    gold:
      +schema: gold
      +materialized: table
```

Здесь:

- `models` — настройки моделей.
- `trino_iceberg_lab` — имя проекта, к которому относятся настройки.
- `+materialized: view` — материализация по умолчанию для моделей проекта.
- `silver` и `gold` — настройки моделей в соответствующих папках.
- `+schema` — пользовательская схема, в которой нужно создавать модели.
- `+materialized: table` — создавать физические таблицы.

Настройки вложенных папок имеют приоритет над настройками родительского уровня.

Поэтому:

| Расположение модели | Материализация | Схема |
|---|---|---|
| `models/stg_example.sql` | view | схема по умолчанию |
| `models/silver/stg_employees.sql` | table | silver |
| `models/gold/dm_employee_headcount.sql` | table | gold |

**Важно:** папки `silver` и `gold` не создают схемы автоматически. Они позволяют dbt применить к находящимся в них моделям соответствующие настройки.

---

## 4. Настройки подключения — profiles.yml

Файл `profiles.yml` содержит параметры подключения dbt к Trino.

Наш профиль:

```yaml
hr_dbt:
  target: dev

  outputs:
    dev:
      type: trino
      method: none
      user: hr_user
      host: localhost
      port: 8080

      database: iceberg
      schema: silver

      threads: 4
      http_scheme: http
```

Разберём основные параметры:

| Параметр | Значение | Назначение |
|---|---|---|
| `type` | `trino` | Используем адаптер dbt-trino |
| `host` | `localhost` | Адрес Trino |
| `port` | `8080` | Порт Trino |
| `database` | `iceberg` | Каталог Trino |
| `schema` | `silver` | Схема по умолчанию |
| `target` | `dev` | Активное окружение |

`schema: silver` — это схема по умолчанию. Она используется, если для модели не задана собственная схема.

---

## 5. Что такое макросы в dbt

Макросы — это переиспользуемые фрагменты SQL и Jinja-кода, которые позволяют динамически формировать SQL и управлять поведением dbt.

По сути, макрос — это функция, которая:
- принимает аргументы;
- выполняет заданную логику;
- возвращает результат;
- может использоваться в разных моделях и механизмах dbt.

Макросы помогают:
- не дублировать одинаковый SQL;
- формировать SQL динамически;
- создавать общие правила обработки данных;
- переопределять стандартное поведение dbt.

Макросы пишутся на языке шаблонизации **Jinja**.

Пример простого макроса:

```sql
{% macro multiply_by_two(column_name) %}

    {{ column_name }} * 2

{% endmacro %}
```

Использование в модели:

```sql
SELECT
    employee_id,
    {{ multiply_by_two('salary') }} AS doubled_salary
FROM employees
```

После обработки Jinja dbt сформирует обычный SQL:

```sql
SELECT
    employee_id,
    salary * 2 AS doubled_salary
FROM employees
```

То есть макрос не выполняет SQL самостоятельно. Он генерирует SQL-код, который затем выполняет база данных.

---

## 6. Макрос generate_schema_name.sql

В нашем проекте используется специальный макрос:

```text
dbt/macros/generate_schema_name.sql
```

Он отвечает за определение итогового имени схемы, в которой dbt будет создавать модель.

### Зачем он нужен

По умолчанию dbt использует собственную логику формирования имени схемы.

Если в `profiles.yml` указано:

```yaml
schema: silver
```

А в `dbt_project.yml` для модели задано:

```yaml
+schema: gold
```

Стандартная логика dbt объединяет эти значения:

```text
silver_gold
```

Но в нашем проекте нужны отдельные схемы:

```text
iceberg.silver
iceberg.gold
```

Поэтому мы переопределили стандартный макрос `generate_schema_name`.

### Полный код макроса

```sql
{% macro generate_schema_name(custom_schema_name, node) -%}

    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}

{%- endmacro %}
```

### Подробный разбор кода

**1. Объявление макроса**

```sql
{% macro generate_schema_name(custom_schema_name, node) -%}
```

Создаётся макрос с именем `generate_schema_name`.

Он принимает два аргумента:

- `custom_schema_name` — пользовательское имя схемы, заданное для модели через `+schema`.
- `node` — объект dbt, содержащий информацию о текущей модели или другом ресурсе.

dbt передаёт эти аргументы автоматически при вызове макроса.

В нашей реализации `node` не используется, но он присутствует в сигнатуре, потому что стандартный макрос dbt принимает этот аргумент.

**2. Проверка пользовательской схемы**

```sql
{%- if custom_schema_name is none -%}
```

Проверяем, задана ли для модели собственная схема.

Если `custom_schema_name` равен `none`, значит пользовательская схема не определена.

**3. Использование схемы по умолчанию**

```sql
{{ target.schema }}
```

Если пользовательская схема отсутствует, возвращаем `target.schema`.

`target` — специальный объект dbt с информацией о текущем подключении и окружении.

`target.schema` — схема по умолчанию из активного профиля в `profiles.yml`.

В нашем случае:

```text
target.schema = silver
```

**4. Если пользовательская схема задана**

```sql
{%- else -%}
    {{ custom_schema_name | trim }}
```

Если схема задана, возвращаем её имя.

Фильтр `trim` удаляет пробелы в начале и конце строки.

Например:

```text
" gold " → "gold"
```

**5. Завершение условия и макроса**

```sql
{%- endif -%}

{%- endmacro %}
```

`endif` закрывает условие, `endmacro` завершает объявление макроса.

### Что означают специальные символы Jinja

| Синтаксис | Назначение |
|---|---|
| `{% ... %}` | Выполнение управляющей конструкции: условие, цикл, объявление макроса |
| `{{ ... }}` | Вывод значения или результата выражения |
| `{# ... #}` | Комментарий Jinja |
| `-` около `%}` или `{{` | Удаление лишних пробелов и переносов строк |

Например:

```sql
{{ target.schema }}
```

означает: подставить значение `target.schema` в итоговый SQL.

А:

```sql
{% if custom_schema_name is none %}
```

означает: выполнить проверку условия при компиляции dbt.

---

## 7. Как работает макрос на практике

Рассмотрим две модели.

### Пример 1. Модель Silver

Файл:

```text
models/silver/stg_employees.sql
```

Настройка:

```yaml
silver:
  +schema: silver
  +materialized: table
```

dbt передаёт в макрос:

```text
custom_schema_name = silver
target.schema = silver
```

Макрос проверяет:

```text
custom_schema_name is none?
```

Ответ: нет.

Поэтому возвращает:

```text
silver
```

Итоговая таблица:

```text
iceberg.silver.stg_employees
```

### Пример 2. Модель Gold

Файл:

```text
models/gold/dm_employee_headcount.sql
```

Настройка:

```yaml
gold:
  +schema: gold
  +materialized: table
```

dbt передаёт в макрос:

```text
custom_schema_name = gold
target.schema = silver
```

Макрос проверяет:

```text
custom_schema_name is none?
```

Ответ: нет.

Возвращает:

```text
gold
```

Итоговая таблица:

```text
iceberg.gold.dm_employee_headcount
```

### Пример 3. Модель без пользовательской схемы

Допустим, модель находится непосредственно в `models/` и не имеет собственного `+schema`.

Тогда:

```text
custom_schema_name = none
target.schema = silver
```

Макрос возвращает:

```text
silver
```

Итоговая таблица будет создана в схеме по умолчанию.

---

## 8. Полная последовательность формирования имени таблицы

```text
                 dbt run
                    |
                    v
           dbt находит SQL-модель
                    |
                    v
             dbt_project.yml
                    |
                    v
       Определяет настройки модели
                    |
                    v
          Получает +schema: gold
                    |
                    v
        generate_schema_name.sql
                    |
                    v
       Возвращает итоговую схему gold
                    |
                    v
              profiles.yml
                    |
                    v
        Получает каталог iceberg
                    |
                    v
        Формирует полное имя таблицы
                    |
                    v
       iceberg.gold.dm_employee_headcount
                    |
                    v
           Выполняет SQL в Trino
                    |
                    v
           Создаёт таблицу Iceberg
```

---

## 9. Как проверить результат

Все SQL-команды ниже выполняются в DBeaver через подключение к Trino.

### Посмотреть таблицы Silver

```sql
SHOW TABLES FROM iceberg.silver;
```

### Посмотреть таблицы Gold

```sql
SHOW TABLES FROM iceberg.gold;
```

### Посмотреть структуру таблицы

```sql
DESCRIBE iceberg.gold.dm_employee_headcount;
```

### Проверить данные

```sql
SELECT *
FROM iceberg.gold.dm_employee_headcount
LIMIT 10;
```

### Посмотреть скомпилированный SQL

В PowerShell из корня проекта:

```powershell
dbt compile --project-dir .\dbt --select dm_employee_headcount
```

Скомпилированные файлы находятся в:

```text
dbt/target/compiled/
```

В них можно посмотреть SQL после обработки Jinja и макросов.

---

## 10. Итог: кто за что отвечает

| Компонент | Ответственность |
|---|---|
| `profiles.yml` | Подключение к Trino, каталог и схема по умолчанию |
| `dbt_project.yml` | Конфигурация проекта и групп моделей |
| `+schema` | Пользовательская схема для группы моделей |
| `+materialized` | Способ материализации модели |
| `generate_schema_name.sql` | Формирование итогового имени схемы |
| `target.schema` | Схема по умолчанию активного подключения |
| `custom_schema_name` | Схема, заданная в конфигурации модели |
| `node` | Контекст текущей модели или другого ресурса dbt |
| `dbt run` | Компиляция и выполнение моделей |

**Коротко на примере нашего проекта:**

1. dbt находит модель `dm_employee_headcount.sql`.
2. Из `dbt_project.yml` получает `+schema: gold`.
3. Передаёт значение `gold` в `generate_schema_name`.
4. Макрос возвращает `gold`.
5. Из `profiles.yml` берётся каталог `iceberg`.
6. dbt формирует имя `iceberg.gold.dm_employee_headcount`.
7. Trino выполняет SQL и создаёт таблицу Iceberg.

Таким образом, `generate_schema_name` — это механизм, который позволяет централизованно управлять правилами формирования схем для всех моделей dbt-проекта.

# Как dbt определяет схему для создания моделей

## 11. Файл sources.yml — описание источников данных

### Что такое sources.yml

` sources.yml ` — YAML-файл, в котором dbt описывает внешние источники данных, используемые проектом.

Источник (Source) — это таблица, которая существует до выполнения dbt-моделей и не создаётся самим dbt.

Например, в нашем HR Lakehouse данные сначала загружаются из PostgreSQL в Bronze. dbt использует таблицы Bronze как источники для построения Silver-моделей.

Схема потока:

```text
PostgreSQL
    |
    v
Trino catalog: postgres
    |
    v
Bronze (Iceberg)
    |
    v
sources.yml
    |
    v
Silver models
    |
    v
Gold models
```

### Где находится файл

```text
dbt/
└── models/
    ├── sources.yml
    ├── schema.yml
    ├── silver/
    └── gold/
```

### Пример sources.yml из нашего проекта

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
```

### Разбор конфигурации

| Параметр | Назначение |
|---|---|
| `version: 2` | Версия формата YAML-конфигурации dbt |
| `sources` | Список описываемых источников |
| `name: bronze` | Логическое имя источника внутри dbt |
| `database: iceberg` | Каталог Trino |
| `schema: bronze` | Схема, в которой находятся таблицы |
| `tables` | Перечень таблиц источника |
| `name: employees` | Имя конкретной таблицы |

Важно различать:

- `name: bronze` — логическое имя источника в dbt.
- `database: iceberg` — реальный каталог Trino.
- `schema: bronze` — реальная схема Trino.
- `tables.name: employees` — реальная таблица.

### Как dbt использует sources.yml

Само описание источника не загружает данные и не создаёт таблицы.

Оно позволяет dbt ссылаться на исходные таблицы через функцию `source()`.

Например, модель:

```sql
SELECT
    employee_id,
    first_name,
    last_name,
    email
FROM {{ source('bronze', 'employees') }}
```

Здесь:

```sql
{{ source('bronze', 'employees') }}
```

означает:

- `bronze` — значение `name` из блока `sources`;
- `employees` — значение `name` из списка `tables`.

После компиляции dbt подставит полное имя таблицы:

```sql
SELECT
    employee_id,
    first_name,
    last_name,
    email
FROM iceberg.bronze.employees
```

То есть `source()` — это специальная функция dbt, которая связывает SQL-модель с описанным источником.

### Зачем использовать source(), а не писать имя таблицы напрямую

Можно написать:

```sql
SELECT *
FROM iceberg.bronze.employees
```

Но лучше:

```sql
SELECT *
FROM {{ source('bronze', 'employees') }}
```

Преимущества:

1. dbt понимает, от какой исходной таблицы зависит модель.
2. dbt строит граф зависимостей (DAG).
3. Можно проверять доступность и свежесть источников.
4. При генерации документации отображается lineage.
5. Если расположение источника меняется, достаточно обновить его описание в одном месте.

### Дополнительные возможности sources.yml

В dbt можно задавать проверки источников и freshness.

Пример:

```yaml
version: 2

sources:
  - name: bronze
    database: iceberg
    schema: bronze

    tables:
      - name: employees
        description: "Исходные данные сотрудников"

      - name: departments
        description: "Справочник подразделений"
```

Также можно задавать:

- `description` — описание источника или таблицы;
- `columns` — описание колонок;
- `loaded_at_field` — колонку времени загрузки;
- `freshness` — правила проверки актуальности данных;
- `tests` — проверки источников.

Например, freshness:

```yaml
sources:
  - name: bronze
    database: iceberg
    schema: bronze

    tables:
      - name: employees
        loaded_at_field: _ingested_at
        freshness:
          warn_after:
            count: 24
            period: hour
          error_after:
            count: 48
            period: hour
```

В этом случае dbt сможет проверять, насколько давно обновлялись данные в таблице.

Для выполнения проверки используется:

```powershell
dbt source freshness --project-dir .\dbt
```

Важно: для freshness нужна корректная колонка времени загрузки. В нашем Bronze-слое `_ingested_at` как раз выполняет эту роль.

---

## 12. Файл schema.yml — описание моделей и тестирование данных

### Что такое schema.yml

`schema.yml` — YAML-файл, в котором dbt описывает модели, их колонки, документацию и проверки качества данных.

В отличие от `sources.yml`, который описывает внешние таблицы, `schema.yml` обычно описывает модели, созданные самим dbt.

В нашем проекте он используется для:
- описания Silver-моделей;
- описания колонок;
- определения первичных ключей с помощью тестов уникальности и отсутствия NULL;
- проверки обязательных полей;
- проверки допустимых значений;
- проверки связей между таблицами.

### Где находится файл

```text
dbt/
└── models/
    ├── sources.yml
    ├── schema.yml
    ├── silver/
    └── gold/
```

### Пример schema.yml из нашего проекта

Ниже показан принцип его организации на примере модели сотрудников. Это иллюстративный фрагмент, а не полный перечень всех 24 проверок нашего проекта.

```yaml
version: 2

models:
  - name: stg_employees
    description: "Подготовленная таблица сотрудников"

    columns:
      - name: employee_id
        description: "Уникальный идентификатор сотрудника"
        data_tests:
          - unique
          - not_null

      - name: first_name
        description: "Имя сотрудника"
        data_tests:
          - not_null

      - name: last_name
        description: "Фамилия сотрудника"
        data_tests:
          - not_null

      - name: employment_status
        description: "Текущий статус трудоустройства"
        data_tests:
          - not_null
          - accepted_values:
              arguments:
                values:
                  - active
                  - terminated
```

### Разбор конфигурации

| Параметр | Назначение |
|---|---|
| `version: 2` | Версия формата YAML-конфигурации dbt |
| `models` | Список моделей dbt |
| `name` | Имя SQL-модели без расширения `.sql` |
| `description` | Описание модели или колонки |
| `columns` | Список колонок модели |
| `data_tests` | Проверки качества данных для колонки |

### Какие тесты использованы

**1. unique**

Проверяет, что значения колонки уникальны.

Например, `employee_id` должен встречаться только один раз.

Упрощённая логика проверки:

```sql
SELECT
    employee_id,
    COUNT(*) AS cnt
FROM iceberg.silver.stg_employees
GROUP BY employee_id
HAVING COUNT(*) > 1
```

Если запрос возвращает строки, тест падает.

**2. not_null**

Проверяет, что в колонке нет NULL.

Упрощённая логика:

```sql
SELECT *
FROM iceberg.silver.stg_employees
WHERE employee_id IS NULL
```

Если найдены строки, тест падает.

**3. accepted_values**

Проверяет, что значения принадлежат разрешённому списку.

Например, статус сотрудника может быть только:

```text
active
terminated
```

Если встречается другое значение, тест падает.

**4. relationships**

Проверяет ссылочную целостность между моделями.

Например, каждый `department_id` в истории трудоустройства должен существовать в справочнике подразделений.

Пример:

```yaml
- name: department_id
  data_tests:
    - relationships:
        arguments:
          to: ref('stg_departments')
          field: department_id
```

Логика:

```text
stg_employment_history.department_id
                  |
                  v
       stg_departments.department_id
```

Если в истории есть подразделение, которого нет в справочнике, тест обнаружит проблему.

### Как dbt выполняет тесты

Команда:

```powershell
dbt test --project-dir .\dbt
```

dbt:

1. Загружает YAML-конфигурации.
2. Находит описанные тесты.
3. Генерирует SQL-запросы для проверок.
4. Выполняет запросы через Trino.
5. Анализирует результаты.

Правило простое:

- `PASS` — нарушений не обнаружено;
- `FAIL` — тест обнаружил проблемные строки;
- `ERROR` — тест не смог выполниться из-за ошибки.

В нашем проекте:

```text
PASS=35
WARN=0
ERROR=0
SKIP=0
NO-OP=0
TOTAL=35
```

Это означает, что все 35 настроенных проверок прошли успешно.

---

## 13. Чем sources.yml отличается от schema.yml

| Критерий | sources.yml | schema.yml |
|---|---|---|
| Назначение | Описание внешних источников | Описание моделей dbt |
| Что описывает | Таблицы, существующие до dbt | Результаты работы dbt |
| Основные конструкции | `sources`, `tables` | `models`, `columns` |
| Ссылка в SQL | `source()` | `ref()` |
| Документация | Да | Да |
| Тесты | Да | Да |
| Проверка freshness | Да | Нет, не через обычное описание модели |

Главное отличие:

```sql
-- Ссылка на внешний источник
SELECT *
FROM {{ source('bronze', 'employees') }}
```

```sql
-- Ссылка на модель dbt
SELECT *
FROM {{ ref('stg_employees') }}
```

`source()` используется для внешних источников, а `ref()` — для моделей dbt.

---

## 14. Как source() и ref() формируют DAG

DAG (Directed Acyclic Graph) — направленный ациклический граф зависимостей.

dbt анализирует функции `source()` и `ref()` и понимает, какие объекты должны быть построены раньше других.

В нашем проекте:

```text
PostgreSQL
    |
    v
Bronze (Iceberg)
    |
    | source('bronze', 'employees')
    v
stg_employees (Silver)
    |
    | ref('stg_employees')
    v
dm_employee_headcount (Gold)
```

Например, если Gold-модель использует:

```sql
FROM {{ ref('stg_employees') }}
```

dbt понимает, что сначала должна быть построена `stg_employees`, а затем зависимая от неё модель.

Это позволяет dbt автоматически определять порядок выполнения моделей.

---

## 15. Как проверить и посмотреть документацию

### Проверить модели и тесты

PowerShell, из корня проекта:

```powershell
dbt test --project-dir .\dbt
```

### Построить документацию

```powershell
dbt docs generate --project-dir .\dbt
```

### Запустить локальный сервер документации

```powershell
dbt docs serve --project-dir .\dbt
```

В документации можно посмотреть:
- список моделей;
- описание таблиц и колонок;
- зависимости между моделями;
- lineage;
- информацию об источниках.

---

## 16. Итоговая структура конфигурации dbt

| Файл | За что отвечает |
|---|---|
| `profiles.yml` | Подключение к Trino и схема по умолчанию |
| `dbt_project.yml` | Настройки проекта и моделей |
| `sources.yml` | Описание внешних источников |
| `schema.yml` | Описание моделей, колонок и тестов |
| `generate_schema_name.sql` | Формирование итогового имени схемы |
| `models/*.sql` | SQL-трансформации |
| `tests/*.sql` | Пользовательские SQL-тесты |
| `macros/*.sql` | Переиспользуемая логика Jinja |

**Коротко:**

- `sources.yml` говорит dbt, откуда брать исходные данные.
- `schema.yml` говорит dbt, что представляют собой модели и как проверять их качество.
- `source()` создаёт зависимость от внешней таблицы.
- `ref()` создаёт зависимость от другой dbt-модели.
- `dbt test` выполняет проверки качества.
- `dbt docs` формирует документацию и визуализирует зависимости.



