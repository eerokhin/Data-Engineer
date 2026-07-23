## Функция загрузки датафрейма в Hadoop/Impala

**1 Вариант**

Создадим тестовую таблицу в Impala

```
DROP TABLE IF EXISTS sbxm_hr.ees_test_table_for_python
/
CREATE TABLE IF NOT EXISTS sbxm_hr.ees_test_table_for_python(
    id INT,
    name STRING,
    age DECIMAL(28,6),
    salary DECIMAL(28,6),
    t_changed_dttm TIMESTAMP
)
STORED AS parquet
```

Сама функция вставки

```python
import pandas as pd
import numpy as np
import re
from datetime import datetime
from impala.dbapi import connect

#Тестовые данные
df = pd.DataFrame({
    "id": [1, 2, 3],
    "name": ["O'Reilly", "Петр", None],
    "age": [25, np.nan, 30],
    "salary": [150000.5, 200000.0, None]
})

def insert_into_hadoop(df, schema, table, connection):

    ''' Загрузка данных через создание строки и использование insert into'''

    # Записываем названия столбцов в одну строку, т.е. делаем в виде списка
    # Для того чтобы записать их потом в список полей таблицы: insert table name (cols)
    db_schema = schema
    resume_table = table
    insert_table = db_schema + '.' + resume_table

    conn = connection
    cursor = conn.cursor()

    for x in range(0, len(df), 500):
        resume_slice = df[x:x+500]
        t_columns = ', '.join(resume_slice.columns.to_list()) + ', t_changed_dttm'

        # Делаем список из строк
        # И записываем как кортеж, потому что у него есть круглые скобки ()
        # Которые потребуются для values()
        t_values = []
        for i in range(len(resume_slice)):
            row = resume_slice.iloc[i].to_list()
            current_time_x = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            row.append(current_time_x)
            t_values.append(f'{tuple(row)}')

        t_values = ', '.join(t_values)
        t_values = re.sub(r"None", 'null', str(t_values))
        t_values = re.sub(r"nan", 'null', str(t_values))
        t_values = re.sub(r"<Na>", 'null', str(t_values))
        insert_str = f"insert into {insert_table} ({t_columns}) values{t_values}"
        print(insert_str)
        cursor.execute(insert_str)
    conn.close()

hadoop_connection = connect(host='hdp-ppp', port=22222, use_ssl='true', auth_mechanism='GSSAPI')
insert_into_hadoop(df=df, schema="sbxm_hr", table="ees_test_table_for_python", connection=hadoop_connection)

#Сформированный запрос на втсавку
# insert into sbxm_hr.ees_test_table_for_python (id, name, age, salary, t_changed_dttm) 
# values
# (1, "O'Reilly", 25.0, 150000.5, '2026-07-23 22:28:49'), 
# (2, 'Петр', null, 200000.0, '2026-07-23 22:28:49'), 
# (3, null, 30.0, null, '2026-07-23 22:28:49')
```

Результат

| id | name       |    age |   salary | t_changed_dttm      |
| -: | :--------- | -----: | -------: | :------------------ |
|  1 | `O'Reilly` |   25 | 150000,5 | 2026-07-23 22:28:49 |
|  2 | Петр       | `NULL` | 200000 | 2026-07-23 22:28:49 |
|  3 | `NULL`     |   30 |   `NULL` | 2026-07-23 22:28:49 |


**2 вариант**

```python
import pandas as pd
import numpy as np
from datetime import datetime
from impala.dbapi import connect

#Тестовые данные
df = pd.DataFrame({
    "id": [1, 2, 3],
    "name": ["O'Reilly", "Петр", None],
    "age": [25, np.nan, 30],
    "salary": [150000.5, 200000.0, None]
})

def insert_into_hadoop(df, schema, table, connection):

    """
    Формирование INSERT INTO для Impala.
    (Исправленная версия без <NA>/nan/None проблем)
    """

    insert_table = f"{schema}.{table}"
    # cursor = connection.cursor()
    def format_value(x):

        # NULL
        if pd.isna(x):
            return "NULL"

        # строки
        if isinstance(x, str):
            return "'" + x.replace("'", "\\'") + "'"

        # datetime
        if isinstance(x, datetime):
            return f"'{x.strftime('%Y-%m-%d %H:%M:%S')}'"

        # pandas timestamp
        if isinstance(x, pd.Timestamp):
            return f"'{x.strftime('%Y-%m-%d %H:%M:%S')}'"

        # float → убираем .0
        if isinstance(x, float):
            if x.is_integer():
                return str(int(x))
            return str(x)

        return str(x)

    for x in range(0, len(df), 500):
        resume_slice = df.iloc[x:x + 500].copy()
        t_columns = ", ".join(resume_slice.columns.to_list()) + ", t_changed_dttm"
        print("Столбцы:", t_columns)
        t_values = []
        for i in range(len(resume_slice)):
            row = resume_slice.iloc[i].to_list()
            current_time_x = datetime.now()
            row.append(current_time_x)
            clean_row = [format_value(v) for v in row]
            t_values.append(f"({', '.join(clean_row)})")
        values_sql = ", ".join(t_values)
        insert_str = f"INSERT INTO {insert_table} ({t_columns}) VALUES {values_sql};"
        #print("\nСформированный SQL:\n")
        #print(insert_str)
        #print("=" * 120)
        cursor.execute(insert_str)
    connection.close()

hadoop_connection = connect(host='hdp-ppp', port=22222, use_ssl='true', auth_mechanism='GSSAPI')
insert_into_hadoop(df=df, schema="sbxm_hr", table="ees_test_table_for_python", connection=hadoop_connection)
```

Результат

| id | name       |    age |   salary | t_changed_dttm      |
| -: | :--------- | -----: | -------: | :------------------ |
|  1 | `O'Reilly` |   25 | 150000,5 | 2026-07-23 22:28:49 |
|  2 | Петр       | `NULL` | 200000 | 2026-07-23 22:28:49 |
|  3 | `NULL`     |   30 |   `NULL` | 2026-07-23 22:28:49 |
