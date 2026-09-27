# Банк задач для собеседований по SQL

В этом разделе собраны практические задачи, которые часто встречаются на собеседованиях.

### Задача с собеседования в ВТБ

1) Найти всех клиентов, у которых вообще нет кредитов (несколькими способами)

-- clients
| client_id | client_name |
|-----------|-------------|
| 1         | Анна        |
| 2         | Борис       |
| 3         | Вера        |

-- credits
| credit_id | client_id | status |
|-----------|-----------|--------|
| 101       | 1         | OPEN   |
| 102       | 1         | CLOSED |
| 103       | 3         | OPEN   |


<details>
<summary>Решение</summary>

```sql
select a.client_id
from clients a
left join credits b
on a.client_id = b.client_id
where b.client_id IS NULL;


/*2 Вариант*/
select
    c.client_id,
    c.client_name
from clients c
where not exists (/*Оставь строки из основной таблицы, для которых не нашлось соответствующей строки в другой таблице*/
    select 1
    from credits cr
    where cr.client_id = c.client_id);
 ```

</details>


2) Какой запрос написать для преобразования?

-- source_data
| id | key  | value       |
|----|------|-------------|
| 1  | fio  | Иван Иванов |
| 1  | city | Москва      |
| 2  | fio  | Анна Петрова|
| 2  | city | Казань      |

-- нужно получить
| id | fio          | city   |
|----|--------------|--------|
| 1  | Иван Иванов  | Москва |
| 2  | Анна Петрова | Казань |

<details>
<summary>Решение</summary>

```sql
with t1 as(
select a.id, a.value as fio
from source_data a
where a.key = 'fio'),

t2 as(
select a.id, a.value as city
from source_data a
where a.key = 'city')

select a.id, a.fio, b.city
from t1 a
join t2 b 
on a.id = b.id

/*2 Вариант*/
select
    id,
    MAX(CASE WHEN key = 'fio' THEN value END) AS fio,
    MAX(CASE WHEN key = 'city' THEN value END) AS city
from source_data
group by id;
```

</details> 

### Задача

Структура данных

| № | Столбец       | Пример                  | Описание                                  |
|---|---------------|-------------------------|-------------------------------------------|
| 1 | `store_id`    | `'store1'`              | Идентификатор магазина                    |
| 2 | `receipt_id`  | `'10000001'`            | Идентификатор чека                        |
| 3 | `receipt_dttm`| `'2020-12-01 14:21:46'` | Дата и время чека                         |
| 4 | `user_id`     | `'id9000'`              | Идентификатор пользователя или кассира    |
| 5 | `plu_id`      | `1234`                  | Идентификатор товара                      |
| 6 | `value`       | `124.95`                | Стоимость товарной позиции                |
| 7 | `quantity`    | `2`                     | Количество товара                         |
| 8 | `discount`    | `0.2`                   | Размер скидки                             |

Вид данных

```sql
-- store_id, receipt_id, receipt_dttm, user_id, plu_id, value, quantity, discount
-- ('store1', '10000001', '2020-12-01 14:21:46', 'id9000', 1234, 124.95, 2, 0.2)
-- ('store1', '10000001', '2020-12-01 14:21:46', 'id9000', 2222, 155.05, 4, 1.5)
-- ('store2', '10000008', '2020-12-02 13:11:06', 'id1961', 4200, 314.00, 1, 0.5)
-- ('store2', '10000009', '2020-12-31 13:11:06', 'id1965', 4200, 314.00, 1, 0.5)
```

Условие

```sql
-- За декабрь 2020 года необходимо:
-- 1. Посчитать сумму каждого чека.
-- 2. Учитывать только чеки минимум с двумя товарными позициями.
-- 3. Учитывать только чеки на сумму от 250 рублей.
```

<details>
<summary>Решение</summary>

```sql
SELECT
    store_id,
    receipt_id,
    receipt_dttm,
    SUM(value * quantity - discount) AS receipt_sum,
    COUNT(*) AS position_count
FROM receipts
WHERE receipt_dttm >= '2020-12-01 00:00:00'
  AND receipt_dttm < '2021-01-01 00:00:00'
GROUP BY
    store_id,
    receipt_id,
    receipt_dttm
HAVING COUNT(*) >= 2
   AND SUM(value * quantity - discount) >= 250;
```

</details> 
