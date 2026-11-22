## PostgreSQL: EXPLAIN и EXPLAIN ANALYZE

В PostgreSQL есть два способа посмотреть план выполнения SQL-запроса.

### 1. EXPLAIN

```sql
EXPLAIN
SELECT *
FROM employees e
JOIN departments d
    ON e.department_id = d.department_id;
```

Показывает **предполагаемый план выполнения**, который выбрал оптимизатор.

Запрос фактически не выполняется. PostgreSQL выводит предполагаемые операции, стоимость выполнения (`cost`) и оценочное количество строк (`rows`).

### 2. EXPLAIN ANALYZE

```sql
EXPLAIN ANALYZE
SELECT *
FROM employees e
JOIN departments d
    ON e.department_id = d.department_id;
```

Показывает **фактический план выполнения**. PostgreSQL действительно выполняет запрос и собирает статистику.

Основные показатели:
- `actual time` — фактическое время выполнения операции.
- `actual rows` — фактическое количество полученных строк.
- `loops` — количество повторений операции.

<img width="703" height="408" alt="photo_2026-11-22_14-00-46" src="https://github.com/user-attachments/assets/e3299a73-53c5-4aaa-aa88-0b8056ffca91" />

### Главное отличие

| EXPLAIN | EXPLAIN ANALYZE |
|---|---|
| Показывает предполагаемый план | Показывает фактическое выполнение |
| Не выполняет обычный SELECT | Выполняет запрос |
| Показывает оценочные показатели | Показывает фактические показатели |

**Зачем это нужно?**

С помощью `EXPLAIN ANALYZE` можно увидеть, какой физический алгоритм JOIN выбрал PostgreSQL (`Nested Loop`, `Hash Join`, `Merge Join`), и оценить эффективность выполнения запроса.

**Важно:** `EXPLAIN ANALYZE` выполняет запрос. При использовании с `UPDATE`, `DELETE` и другими изменяющими операциями нужно соблюдать осторожность.
