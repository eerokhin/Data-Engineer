**1. Какие DAG'и разрабатывали?**

<details>
<summary><strong>Ответ на вопрос</strong></summary>

### Ответ

Разрабатывал DAG'и для ETL-процессов. В основном это загрузка и обработка данных с использованием Python и SQL с последующей записью в Hadoop/Impala.

Например, был DAG для загрузки данных из API: Python-код получал данные, выполнял необходимые преобразования, после чего данные загружались в Hadoop и становились доступны через Impala.

Также разрабатывал DAG'и для формирования и обновления витрин: сначала выполнялись подготовительные SQL-операции, затем расчёт витрины, а после — контроль успешности выполнения.

При этом использовал зависимости между task'ами, параметры расписания, `Retry`, `catchup`, `Sensors` и `SLA`, а также различные операторы Airflow. В основном работал с `PythonOperator` и SQL-задачами.

Пример DAG:

```text
get_data_from_api
        ↓
save_raw_data
        ↓
load_to_impala
        ↓
build_mart
```

Пример реализации:

```python
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator


def get_data_from_api():
    # Получение данных из API
    print("Получаем данные из API")


def save_raw_data():
    # Сохранение полученных данных
    print("Сохраняем raw-данные")


with DAG(
    dag_id="api_to_impala_mart",
    start_date=datetime(2026, 10, 1),
    schedule="0 11 * * *",
    catchup=False,
    tags=["etl", "impala"],
) as dag:

    get_data = PythonOperator(
        task_id="get_data_from_api",
        python_callable=get_data_from_api,
    )

    save_data = PythonOperator(
        task_id="save_raw_data",
        python_callable=save_raw_data,
    )

    load_to_impala = SQLExecuteQueryOperator(
        task_id="load_to_impala",
        conn_id="impala",
        sql="""
            INSERT INTO dwh.raw_data
            SELECT *
            FROM staging.raw_data;
        """,
    )

    build_mart = SQLExecuteQueryOperator(
        task_id="build_mart",
        conn_id="impala",
        sql="""
            INSERT INTO dwh.employee_mart
            SELECT
                employee_id,
                name,
                department,
                updated_at
            FROM dwh.raw_data;
        """,
    )

    get_data >> save_data >> load_to_impala >> build_mart
```

В данном DAG:

* `PythonOperator` используется для выполнения Python-кода;
* `SQLExecuteQueryOperator` — для выполнения SQL;
* `>>` задаёт последовательность выполнения task;
* `schedule="0 11 * * *"` — запуск каждый день в 11:00;
* `catchup=False` — отключает создание пропущенных запусков за прошлые даты.

Дополнительно в DAG'ах могут использоваться:

* `Retry` — повторный запуск task при ошибке;
* `Sensors` — ожидание наступления определённого события или готовности данных;
* `SLA` — контроль времени выполнения задачи.

Можно кратко сказать:

> «Разрабатывал DAG'и для ETL-процессов. Например, данные получались из API с помощью Python, затем сохранялись в staging, загружались в Hadoop/Impala и после этого формировалась целевая витрина. Между task были настроены зависимости, расписание и retries. Также использовал Sensors и SLA.»

</details>



