# dbt Testing: Generic Tests и Singular Tests

## 1. Что такое тестирование в dbt

dbt позволяет проверять качество данных и корректность результатов трансформаций.

Тесты помогают выявлять:
- дублирующиеся записи;
- пропущенные значения (`NULL`);
- некорректные значения атрибутов;
- нарушения ссылочной целостности;
- нарушения бизнес-правил;
- ошибки в логике формирования аналитических витрин.

В dbt есть два основных типа тестов:

1. **Generic Tests** — универсальные тесты, настраиваемые через YAML.
2. **Singular Tests** — пользовательские SQL-тесты.

## 2. Как работают тесты dbt

Общий принцип работы:

1. dbt выполняет SQL-запрос проверки.
2. Запрос возвращает записи, нарушающие условие.
3. Если запрос вернул 0 строк — тест пройден (`PASS`).
4. Если запрос вернул одну или несколько строк — тест не пройден (`FAIL`).

Таким образом, тест в dbt — это SQL-запрос, который ищет некорректные данные.

---

## 3. Generic Tests

**Generic Tests** — стандартные универсальные проверки, которые настраиваются в YAML-файлах.

Разработчику не нужно самостоятельно писать SQL для каждой типовой проверки: dbt генерирует его на основании конфигурации теста.

### Основные Generic Tests

| Тест | Назначение |
|---|---|
| `unique` | Проверяет уникальность значений |
| `not_null` | Проверяет отсутствие NULL |
| `accepted_values` | Проверяет допустимые значения |
| `relationships` | Проверяет ссылочную целостность |

### Пример настройки

Файл `models/schema.yml`:

```yaml
version: 2

models:
  - name: stg_employees
    columns:
      - name: employee_id
        tests:
          - unique
          - not_null

      - name: status
        tests:
          - accepted_values:
              arguments:
                values: ['active', 'terminated']

      - name: department_id
        tests:
          - relationships:
              arguments:
                to: ref('stg_departments')
                field: department_id
```

### Разбор тестов

**unique**

Проверяет, что значения столбца не повторяются.

```yaml
- name: employee_id
  tests:
    - unique
```

**not_null**

Проверяет, что обязательное поле не содержит NULL.

```yaml
- name: employee_id
  tests:
    - not_null
```

**accepted_values**

Проверяет, что значения принадлежат заданному списку.

```yaml
- name: status
  tests:
    - accepted_values:
        arguments:
          values: ['active', 'terminated']
```

**relationships**

Проверяет ссылочную целостность между таблицами.

```yaml
- name: department_id
  tests:
    - relationships:
        arguments:
          to: ref('stg_departments')
          field: department_id
```

Например, каждый `department_id` сотрудника должен существовать в таблице подразделений.

### Какой SQL генерирует dbt

Для теста `not_null` логика проверки будет примерно такой:

```sql
SELECT employee_id
FROM iceberg.silver.stg_employees
WHERE employee_id IS NULL
```

Для `unique` логика примерно такая:

```sql
SELECT employee_id
FROM iceberg.silver.stg_employees
GROUP BY employee_id
HAVING COUNT(*) > 1
```

---

## 4. Singular Tests

**Singular Tests** — пользовательские тесты, которые разработчик самостоятельно пишет на SQL.

Используются, когда стандартных Generic Tests недостаточно и требуется проверить специфическую бизнес-логику.

Располагаются в директории:

```text
dbt/
  tests/
    assert_dm_employee_headcount_non_negative.sql
    assert_dm_employee_turnover_unique_grain.sql
    assert_dm_employee_movements_history_match.sql
```

### Пример 1. Проверка численности сотрудников

Файл `assert_dm_employee_headcount_non_negative.sql`:

```sql
SELECT *
FROM {{ ref('dm_employee_headcount') }}
WHERE headcount < 0
```

Проверяет, что численность сотрудников не может быть отрицательной.

### Пример 2. Проверка уникальности зерна витрины

Файл `assert_dm_employee_turnover_unique_grain.sql`:

```sql
SELECT
    department_id,
    report_month,
    COUNT(*) AS cnt
FROM {{ ref('dm_employee_turnover') }}
GROUP BY
    department_id,
    report_month
HAVING COUNT(*) > 1
```

Проверяет, что в витрине существует только одна запись на подразделение и месяц.

### Пример 3. Проверка обязательных полей

```sql
SELECT *
FROM {{ ref('dm_employee_movements') }}
WHERE employee_id IS NULL
   OR event_date IS NULL
   OR event_type IS NULL
```

Проверяет заполненность обязательных атрибутов кадрового события.

### Как работают Singular Tests

dbt выполняет SQL из файла.

- Если запрос вернул 0 строк — `PASS`.
- Если запрос вернул строки — `FAIL`.

Важно: в Singular Test не нужно писать `ASSERT`, `IF` или самостоятельно возвращать статус. Достаточно SQL-запроса, который находит нарушения.

---

## 5. Generic Tests vs Singular Tests

| Критерий | Generic Tests | Singular Tests |
|---|---|---|
| Где находятся | YAML-файлы | `tests/*.sql` |
| Формат | YAML-конфигурация | SQL |
| SQL | Генерирует dbt | Пишет разработчик |
| Назначение | Типовые проверки | Бизнес-правила |
| Примеры | `unique`, `not_null` | Проверка зерна витрины |
| Повторное использование | Можно применять к разным моделям и столбцам | Обычно отдельный SQL-тест под конкретную проверку |

**Главное отличие:**

- Generic — готовый шаблон проверки, который настраивается через YAML.
- Singular — самостоятельный SQL-запрос для проверки конкретного условия.

---

## 6. Где хранятся тесты в проекте

Пример структуры:

```text
dbt/
├── dbt_project.yml
├── models/
│   ├── schema.yml
│   ├── sources.yml
│   ├── silver/
│   │   ├── stg_employees.sql
│   │   └── stg_departments.sql
│   └── gold/
│       ├── dm_employee_headcount.sql
│       └── dm_employee_turnover.sql
└── tests/
    ├── assert_dm_employee_headcount_non_negative.sql
    ├── assert_dm_employee_turnover_unique_grain.sql
    └── assert_dm_employee_movements_history_match.sql
```

Generic Tests объявляются в YAML рядом с описаниями моделей и их столбцов.

Singular Tests хранятся отдельными SQL-файлами в директории `tests`.

---

## 7. Запуск тестов

Выполнить все тесты проекта:

```bash
dbt test
```

Запустить тесты конкретной модели:

```bash
dbt test --select stg_employees
```

Запустить только Singular Tests:

```bash
dbt test --select test_type:singular
```

Запустить только Generic Tests:

```bash
dbt test --select test_type:generic
```

Сначала собрать модели, затем выполнить тесты:

```bash
dbt build
```

`dbt build` выполняет сборку выбранных ресурсов с учётом зависимостей: модели, тесты, seeds и snapshots, если они входят в выбранный набор.

---

## 8. Практическое применение в HR Lakehouse

В проекте HR Lakehouse использовал оба типа тестирования.

### Silver — Generic Tests

Проверки качества подготовленных данных:

- уникальность идентификаторов сотрудников;
- отсутствие NULL в обязательных полях;
- допустимые значения статусов;
- наличие подразделений в справочнике;
- ссылочная целостность между HR-сущностями.

### Gold — Singular Tests

Проверки бизнес-логики аналитических витрин:

- уникальность зерна `department_id + report_month`;
- отсутствие отрицательной численности;
- корректность обязательных атрибутов кадровых событий;
- допустимость типов событий;
- согласованность кадровых перемещений с историей трудоустройства.

### Результат

В проекте реализовано 35 проверок качества данных:

- 24 Generic Tests на уровне Silver;
- 11 Singular Tests на уровне Gold.

Результат полного запуска:

```text
PASS=35
WARN=0
ERROR=0
SKIP=0
NO-OP=0
TOTAL=35
```

Все 35 проверок завершились успешно.

---

## 9. Что рассказать на собеседовании

В dbt использовал два типа тестирования: Generic и Singular.

Generic Tests применял для стандартных проверок качества данных — уникальности ключей, отсутствия NULL, допустимых значений и ссылочной целостности. Они описываются в YAML, а SQL для них генерирует dbt.

Singular Tests использовал для проверки специфической бизнес-логики витрин. Это отдельные SQL-запросы, которые возвращают записи с нарушениями. Например, проверка уникальности зерна витрины или отсутствие отрицательной численности сотрудников.

Всего реализовал 35 проверок: 24 на Silver и 11 на Gold. Все тесты успешно прошли.

---

## 10. Ключевая мысль

**Generic Tests** отвечают на вопрос: «Соответствуют ли данные стандартным требованиям качества?»

**Singular Tests** отвечают на вопрос: «Соблюдается ли конкретное бизнес-правило, которое мы заложили в модель?»
