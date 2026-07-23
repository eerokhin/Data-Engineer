# Наименование схемы в бд
# Схема загрузки
db_schema = 'sbxm_hr'

# Наименование таблиц
# Резюме после парсинга json-данных, используется для входного вектора ML-модели
resume_table = 'rda_hh_application_resume_erohin' 

# Резюме в json-формате, полученные от hh.ru
full_resume_table = 'rda_hh_full_resume_erohin' 


# Подключение к СУБД
# Параметры подключения
host = "localhost"
port = "5432"
database = "postgres"
user = "postgres"
password = "postgres"

# Создание подключения
postgre_connect = f"host={host} port={port} dbname={database} user={user} password={password}"