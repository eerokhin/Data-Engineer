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

**2. Использовали ли Sensors?**

<details>
<summary><strong>Ответ на вопрос</strong></summary>

### Ответ

Да, использовал `Sensors` для ожидания наступления определённого события или готовности данных перед запуском следующих task.

Например, если DAG должен был обрабатывать данные только после того, как они появятся в определённом месте, можно было использовать `FileSensor` или другой подходящий Sensor.

Пример:

```python
from datetime import datetime

from airflow import DAG
from airflow.sensors.filesystem import FileSensor
from airflow.operators.python import PythonOperator


def process_data():
    print("Обрабатываем данные")


with DAG(
    dag_id="sensor_example",
    start_date=datetime(2026, 10, 1),
    schedule="0 11 * * *",
    catchup=False,
) as dag:

    wait_for_file = FileSensor(
        task_id="wait_for_file",
        filepath="/data/input/file.csv",
        poke_interval=60,
        timeout=60 * 60,
        mode="reschedule",
    )

    process = PythonOperator(
        task_id="process_data",
        python_callable=process_data,
    )

    wait_for_file >> process
```

В данном случае DAG сначала ждёт появления файла:

```text
wait_for_file
      ↓
   файл появился
      ↓
process_data
```

Если файл ещё не появился, Sensor продолжает ждать. После его появления task завершается успешно и запускается следующий task.

Также Sensor можно использовать не только для файлов — например, для ожидания появления данных в таблице, завершения другого DAG или наступления определённого события.

</details>



