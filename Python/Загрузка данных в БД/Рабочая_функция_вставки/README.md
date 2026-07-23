# **Тестовый скрипт для загрузки данных в БД postgreSQL**

Скрипт для загрузки данных в postgreSQL. Данные получены из HH API в виде JSON и сохранены в `.csv` файл в исходном виде и распарсенном.

В файле `main_test.py` вызываются все основные функции.

В файле `create_table.py` запросы для создания таблиц, которые вызываются в `main_test.py` циклом.

В файле `insert_in_postgresql.py` две функции для выполнения запросов `sql_query_execute()` и вставки данных в БД `insert_into_postgre()`.

После запуска в БД появляются две таблицы

![image](https://github.com/user-attachments/assets/af58896a-3dbb-48d0-9f7c-6007c978a2f6)

**Заметки:**

Важно при загрузке соблюдать типы колонок в БД и типы колонок в датафрейме который грузим, иначе будут ошибки.

Соблюдать экранирование символов, разные БД ведут себя по разному.

Привести значения в DataFrame к стандартным типам Python. Перед тем как передавать данные в `execute_values`, нужно преобразовать все значения в стандартные типы Python, такие как `int`, `float`, `str`, `datetime`, которые поддерживаются psycopg2. 

Когда создаёшь DataFrame, pandas под капотом использует `NumPy` для хранения данных. И чтобы эффективно обрабатывать большие массивы чисел, он применяет типы вроде `np.float64`, `np.int64`, `np.object_` и т.п. — это просто NumPy-аналог стандартных типов Python (`float`, `int` и т.д.), но с большей производительностью и поддержкой векторных операций.

Некоторые библиотеки для работы с базами данных (например, `sqlite3`, `psycopg2`, `sqlalchemy`) не всегда автоматически приводят `np.float64` к стандартному `float`, и возникает ошибка.

Сделал с помощью `df = df.astype(object)` перед тем как добавлять данные в БД.

Дата фрейм надо привести к виду, тоесть достать колонки и строки со значениями:

```
INSERT INTO users (id, name, email) VALUES (2, 'Пётр Смирнов', 'petr@example.com'), (3, 'Ольга Соколова', 'olga@example.com');
```

# **Отличие вставки через:**

```
insert_str = f"INSERT INTO {insert_table} ({t_columns}) VALUES %s"
```

и
```
insert_str = f"insert into {'insert_table'} ({t_columns}) values{t_values}"
```

✅ Первый способ (через %s):
```
insert_str = f"INSERT INTO {insert_table} ({t_columns}) VALUES %s"
```

Этот шаблон не вставляет сами значения напрямую в строку — он используется совместно с методом `execute_values()` из `psycopg2.extras` (или аналогичных инструментов), который безопасно подставляет значения.

Пример:
```
from psycopg2.extras import execute_values

insert_str = f"INSERT INTO {insert_table} ({t_columns}) VALUES %s"
execute_values(cursor, insert_str, t_values)
```

✅ Преимущества:

-Безопасность: защита от SQL-инъекций.

-Производительность: вставка сразу многих строк (bulk insert).

-Правильная экранизация: спецсимволы, кавычки, даты и т.д.

🚫 Второй способ (небезопасный, вручную подставленные значения):

```
insert_str = f"INSERT INTO {'insert_table'} ({t_columns}) VALUES{t_values}"
```

Здесь `t_values` — это уже вручную сгенерированная строка, например:

```
t_values = "(1, 'Alice'), (2, 'Bob')"
```

❗ Минусы:

-Уязвимость к SQL-инъекциям, если значения приходят откуда-то извне.

-Сложность с кавычками, датами, экранированием.

-Нет автоматической обработки типов (например, `None → NULL`).

-Нельзя использовать с `execute_values()` или параметрами — это уже "собранная" SQL-строка.


**SQL запросы**

```
DROP TABLE IF EXISTS sbxm_hr.rda_hh_application_resume_erohin

DROP TABLE IF EXISTS sbxm_hr.rda_hh_full_resume_erohin

select * from sbxm_hr.rda_hh_application_resume_erohin 

select * from sbxm_hr.rda_hh_full_resume_erohin
```



