import pandas as pd
from insert_in_postgresql import insert_into_postgre, sql_query_execute
from params import *
from create_table import *




# 1.Создание таблиц в БД
for query in create_table_query_list:
    sql_query_execute(query, postgre_connect)

#2.Вставка данных
df = pd.read_csv('C:/Users/erohi/Desktop/python/insert_in_postgre/df_result.csv')
df_full = pd.read_csv('C:/Users/erohi/Desktop/python/insert_in_postgre/full_resume_df.csv')

df = df.astype(object)

insert_into_postgre(df_full, db_schema, full_resume_table, postgre_connect)
insert_into_postgre(df, db_schema, resume_table, postgre_connect)

