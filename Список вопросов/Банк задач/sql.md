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



select
    c.client_id,
    c.client_name
from clients c
where not exists (/*Оставь строки из основной таблицы, для которых не нашлось соответствующей строки в другой таблице*/
    select 1
    from credits cr
    where cr.client_id = c.client_id);
</details> ```


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

select a.id, a.fio, a.city
from t1 a
join t2 b 
on a.id = b.id
</details> ```
