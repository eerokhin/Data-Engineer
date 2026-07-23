import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import pandas as pd

def insert_into_postgre(df, schema, table, connection):
    '''
    Загрузка данных через создание строки и использование insert into
    '''
    db_schema = schema
    resume_table = table
    insert_table = db_schema + '.' + resume_table
    conn = psycopg2.connect(connection)
    cursor = conn.cursor()

    # Обработка данных по частям (batching)
    for x in range(0, len(df), 500):
        resume_slice = df[x:x+500]
        # Добавляем столбец t_changed_dttm к списку столбцов
        t_columns = ', '.join(resume_slice.columns.to_list()) + ', t_changed_dttm'
        # Делаем список из строк, добавляем значение для t_changed_dttm
        t_values = []
        for i in range(len(resume_slice)):
            row = resume_slice.iloc[i].to_list()
            current_time_x = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            row.append(current_time_x)  # Добавляем текущее время для t_changed_dttm

            # Заменяем None и NaN на null
            row = [None if pd.isna(value) or value is None else value for value in row]
            t_values.append(tuple(row))  # Добавляем строку как кортеж

        # Формируем запрос для массовой вставки
        insert_str = f"INSERT INTO {insert_table} ({t_columns}) VALUES %s"
        
        # Используем execute_values для массовой вставки
        execute_values(cursor, insert_str, t_values)

    conn.commit()    
    conn.close()   



def sql_query_execute(query, connection):
    """
    Выполнение запроса к базе данных с обработкой исключений
    """
    conn = psycopg2.connect(connection)
    cursor = conn.cursor()
    cursor.execute(query)      
    
    try:
        # если запрос является SELECT'ом, то возвращаем полученные данные
        if query.split()[0].lower() in ('select', 'with'):
            result_data = cursor.fetchall() 
        else:
            conn.commit()
            result_data = None

    except Exception as error:
        print(error)
        result_data = None
    #finally:
        #cursor.close()
        #conn.close()

    return result_data


