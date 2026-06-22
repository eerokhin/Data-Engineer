# **В postgresql**

Предположим есть датафрейм

```python
import pandas as pd

resumes_id_list_all = [['aaa111', 111111, 'test1', 'test_11', 10011, 'active', 'data'],  
                       ['aaa222', 22222, 'test2', 'test_22', 10012, 'active', 'data2']]

df_resumes_list = pd.DataFrame(resumes_id_list_all, columns=['resume_id', 'owner_id', 'url', 'url_w_contacts', 'vacancy_code', 'search_status', 't_changed_dttm']).drop_duplicates()
```

![image](https://github.com/user-attachments/assets/6d9a74e0-9b2a-4427-b8a5-975ca8e1ff52)

```python
#Получаем список кортежей
#Кортеж (tuple) — неизменяемый тип данных. my_tuple = (1, 2, 3)
#Множество (set) — изменяемый тип данных. my_set = {1, 2, 3}

df = df_resumes_list
tuples = list(set([tuple(x) for x in df.to_numpy()]))
tuples


#[('aaa222', 22222, 'test2', 'test_22', 10012, 'active', 'data2'),
#('aaa111', 111111, 'test1', 'test_11', 10011, 'active', 'data')]
```

```python
columns = ', '.join(list(df.columns))

#resume_id, owner_id, url, url_w_contacts, vacancy_code, search_status, t_changed_dttm
```

```python
column_cnt = len(df.columns)

#7
```

Делаем подключение к БД

```python
import psycopg2

# Подключение к базе данных (параметры подключения нужно заменить на свои)
conn = psycopg2.connect(dbname="your_db", user="your_user", password="your_password", host="localhost")
cursor = conn.cursor()

# Подготовка запроса
db_schema = 'schema'
db_table = 'tablica'
query = "INSERT INTO {0}.{1}({2}) VALUES ({3})".format(db_schema, db_table, columns, ','.join(['%s'] * column_cnt))
#INSERT INTO schema.tablica(resume_id, owner_id, url, url_w_contacts, vacancy_code, search_status, t_changed_dttm) VALUES (%s,%s,%s,%s,%s,%s,%s)


# Вставка данных
cursor.executemany(query, tuples)

# Подтверждение изменений и закрытие соединения
conn.commit()
cursor.close()
conn.close()
```

**Результат:** Запрос будет выполнен, и данные из DataFrame будут вставлены в таблицу. Для каждой строки DataFrame будет выполнена вставка в таблицу с подставленными значениями.

Вставка выполняется с использованием метода `executemany()`.

`executemany()` — N отдельных запросов (1 на каждую строку)

`cursor.executemany(query, tuples)`

**Подготовить список кортежей, где каждый кортеж содержит значение каждой строки.**

Допустим, `tuples = [(...), (...), ..., (...)]` — 10 000 строк.

Что делает `executemany()`?

Это эквивалентно:
```
INSERT INTO ... VALUES (...);
INSERT INTO ... VALUES (...);
...
#И так 10 000 раз
```

Итог: 10 000 отдельных запросов.

Лучше использовать пакетную вставку(батч)

Пакетная вставка данных (или batch insert), это означает, что несколько строк данных из DataFrame будут вставлены в таблицу в рамках одного SQL-запроса, а не каждый ряд отдельно. Это позволяет значительно ускорить вставку, так как уменьшается количество запросов к базе данных.

Метод `execute_values`  — это оптимальное решение для массовой вставки.

Метод `execute_values` может превосходить executemany() по скорости до шестидесяти раз.

# **Методы**

| Что ты делаешь                                              | Сколько SQL-запросов | Комментарий                                                |
|-------------------------------------------------------------|-----------------------|-------------------------------------------------------------|
| `cursor.execute("INSERT ... VALUES (...)")`                 | 1                     | Вставляется 1 строка                                        |
| `cursor.execute("INSERT ... VALUES (...), (...), (...)")`   | 1                     | Вставляется сразу много строк (батч)                        |
| Цикл с `cursor.execute(...)` по одной строке                | N                     | Плохо по производительности                                 |
| `cursor.executemany(...)`                                   | N                     | 1 запрос на каждую строку                                   |
| `execute_values(...)` *(PostgreSQL only)*                   | Меньше запросов       | 1 запрос на батч, внутри много строк                        |



| Метод                                           | Что передавать                         | Пример данных                                    | Комментарий                                                              |
|-------------------------------------------------|----------------------------------------|--------------------------------------------------|--------------------------------------------------------------------------|
| `cursor.execute(query, tuple)`                  | Кортеж                                 | `('user_1', 25, 'Москва')`                       | Вставляется одна строка                                                  |
| `cursor.executemany(query, list_of_tuples)`     | Список кортежей (`List[Tuple]`)        | `[('user_1', 25), ('user_2', 30)]`               | Каждый кортеж → отдельный запрос → много SQL-запросов                    |
| `execute_values(cursor, query, list_of_tuples)` | Список кортежей (`List[Tuple]`)        | `[('user_1', 25), ('user_2', 30)]`               | Один SQL-запрос со множеством `VALUES (...)` — быстро и эффективно       |
| `cursor.execute(query)` без параметров          | Строка с подставленными значениями     | `"INSERT INTO t (a, b) VALUES ('user_1', 25)"`   | Все значения уже в query — можно собирать вручную через `.join()`        |
| `cursor.execute(query, dict)`                   | Словарь с именованными параметрами     | `{'name': 'user_1', 'age': 25}`                  | Используется с именованными плейсхолдерами: `VALUES (%(name)s, %(age)s)` |

# **Что значит VALUES %s?**

Когда используется VALUES %s в таком виде:
```
query = "INSERT INTO table_name (col1, col2) VALUES %s"
execute_values(cursor, query, [('user1', 25), ('user2', 30)])
```

Это специальный синтаксис библиотеки psycopg2.extras.execute_values. Она сама разворачивает список в:
```
INSERT INTO table_name (col1, col2) VALUES 
('user1', 25),
('user2', 30);
```

Передаём просто список кортежей — `[(...), (...)]`, а библиотека превращает это в полноценный SQL. Это работает только с `execute_values` (PostgreSQL).

**executemany**

```
query = "INSERT INTO users (name, age) VALUES (%s, %s, %s)"

cursor.executemany(query, [('Alice', 30, 1),('Bob', 25, 5),])
```

`%s, %s, %s` — потому что мы вставляем три отдельных значения на каждую строку.

Для каждой строки из списка выполняется отдельный INSERT.

**`execute_values`**

```
query = "INSERT INTO users (name, age) VALUES %s"

execute_values(cursor, query, [('Alice', 30),('Bob', 25),])
```

Только один `%s` — потому что `execute_values` подставляет сразу всю часть (...), (...) в одном запросе.

Всё идёт одним большим INSERT, а не много маленьких.

# **Важно!!!!!**

При работе с PostgreSQL не забывать делать conn.commit(), Иначе в БД данные не появятся и будет пустая таблица.

В Hadoop Impala это не требуется.

**Почему commit() нужен в PostgreSQL:**

PostgreSQL поддерживает транзакции по умолчанию. Когда выполняешь запросы, они обрабатываются в рамках транзакции, и изменения не сохраняются в базе до тех пор, пока не будет выполнен commit(). Это позволяет, например, отменить все изменения, если что-то пошло не так, с помощью rollback().

Если ты не вызывать commit(), то изменения будут сохранены только в текущем сеансе, но не в базе данных, и они исчезнут после закрытия соединения.

**Почему commit() не нужен для Impala:**

Impala — это более "псевдокластерная" СУБД, и она использует другой механизм для выполнения запросов. Impala не поддерживает стандартные транзакции, как PostgreSQL. Все запросы выполняются немедленно, и изменения сохраняются сразу же после выполнения запроса.

Это может быть удобнее в некоторых случаях, но не дает той же надежности, как транзакции в PostgreSQL, где ты можешь контролировать, что именно и когда будет сохранено.

**Если вставляю в Impala**

`execute_values` не работает — но можно собрать строку из `VALUES (...), (...), ...` с помощью `.join()` и вставить через `cursor.execute()`.

```
insert_str = "insert into schema.table (col1, col2, col3) values ('gjghj', 1234, null), ('fkfkhj', 4444, null), ('cvfdg', 9865, null), ('hghhg', 9632, null)"
cursor.execute(insert_str)
```
