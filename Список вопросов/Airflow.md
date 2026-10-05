**1. Какие DAG'и разрабатывали?**

<details>
<summary><strong>Ответ на вопрос</strong></summary>

### Ответ

Разрабатывал DAG'и для ETL-процессов. В основном это загрузка и обработка данных с использованием Python и SQL с последующей записью в Hadoop/Impala.

Например, был DAG для загрузки данных из API: Python-код получал данные, выполнял необходимые преобразования, после чего данные загружались в Hadoop и становились доступны через Impala.

Также разрабатывал DAG'и для формирования и обновления витрин: сначала выполнялись подготовительные SQL-операции, затем расчёт витрины, а после — контроль успешности выполнения.

При этом использовал зависимости между task'ами, параметры расписания, `Retry`, `catchup`, `Sensors` и `SLA`, а также различные операторы Airflow. В основном работал с `PythonOperator` и SQL-задачами.

Что означают термины:

- Зависимости между task'ами — определяют порядок выполнения задач. Например, `load_data >> build_mart` означает, что `build_mart` запустится после успешного выполнения `load_data`.
- Параметры расписания (`schedule`) — определяют, когда и как часто запускается `DAG`. Например, `schedule="0 11 * * *"` — каждый день в `11:00`.
- `Retry` — повторное выполнение `task` после ошибки. Настраивается через `retries`.
- `catchup` — определяет, нужно ли Airflow создавать запуски за пропущенные периоды после включения или изменения `DAG`. Например, `catchup=False` отключает такие запуски.
- `Sensors` — специальные `task`, которые ждут наступления определённого события или выполнения условия, например появления файла или данных.
- `SLA (Service Level Agreement)` — ограничение по времени, за которое `task` должен быть выполнен. Позволяет контролировать задержки выполнения.
- Операторы (`Operators`) — определяют, какое действие должен выполнять `task`. Например, `PythonOperator` запускает `Python`-функцию, а `SQL`-оператор выполняет `SQL`-запрос.
- `PythonOperator` — оператор для выполнения Python-кода.
- `SQL`-задачи — `task`, предназначенные для выполнения `SQL`-запросов, например загрузки данных или формирования витрины.

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

**3. Использовали ли Retry?**


<details>
<summary><strong>Ответ на вопрос</strong></summary>

### Ответ

Да, использовал `Retry`. Он применяется, если отдельный `task` завершился с ошибкой и его нужно автоматически выполнить повторно.

В `task` задаются два основных параметра:

* `retries` — количество дополнительных попыток после первой ошибки;
* `retry_delay` — время ожидания между попытками.

Например:

```python
PythonOperator(
    task_id="load_data",
    python_callable=load_data,
    retries=3,
    retry_delay=timedelta(minutes=5),
)
```

В данном случае при ошибке Airflow подождёт 5 минут и повторит выполнение task. Максимально будет выполнено 3 дополнительные попытки.

```text
Первая попытка
      ↓
    ERROR
      ↓
  5 минут
      ↓
  Retry #1
      ↓
    ERROR
      ↓
  5 минут
      ↓
  Retry #2
      ↓
  SUCCESS
```

`Retry` — это сам механизм повторного запуска task после ошибки. Отдельного параметра `retry` в DAG указывать не нужно.

</details>

**4. Использовали ли SLA?**

<details>
<summary><strong>Ответ на вопрос</strong></summary>

### Ответ

Да, использовал `SLA` для контроля времени выполнения `task`.

`SLA` позволяет задать максимальное ожидаемое время выполнения задачи. Если `task` не укладывается в заданный `SLA`, Airflow фиксирует нарушение `SLA` и может отправить соответствующее уведомление.

Например:

```python
from datetime import timedelta

PythonOperator(
    task_id="load_data",
    python_callable=load_data,
    sla=timedelta(minutes=30),
)
```

В данном случае ожидается, что `task` должен завершиться в пределах `30` минут.

Если задача выполняется дольше установленного `SLA`, это считается **SLA miss**. Увидеть нарушение `SLA` можно в `Browse → SLA Misses`

Важно: `SLA` **не останавливает выполнение task** после истечения времени. Он используется именно для контроля и уведомления о нарушении времени выполнения.

```text
Task запущен
     ↓
  30 минут
     ↓
SLA превышен
     ↓
SLA miss / уведомление
     ↓
Task продолжает выполняться
```

### Для чего использовать

Например, если ежедневная загрузка данных обычно занимает `20` минут, можно установить `SLA` в `30` минут. Если загрузка стала выполняться значительно дольше, это будет сигналом, что с процессом возникла проблема.

</details>


**5. Как реализуете зависимости между задачами?**

<details>
<summary><strong>Ответ на вопрос</strong></summary>

### Ответ

Зависимости между task'ами задаю с помощью операторов `>>`.

Например:

```python
get_data >> transform_data >> load_to_impala >> build_mart
```

Это означает, что задачи будут выполняться последовательно:

```text
get_data
    ↓
transform_data
    ↓
load_to_impala
    ↓
build_mart
```

Следующий task запускается только после успешного выполнения предыдущего.

Также можно задавать зависимости между несколькими задачами:

```python
get_users >> build_users_mart
get_departments >> build_users_mart
```

В этом случае `build_users_mart` начнёт выполняться только после успешного завершения **обеих** задач:

```text
get_users ───────┐
                 ↓
             build_users_mart
                 ↑
get_departments ─┘
```

Можно использовать и более сложную структуру:

```python
get_data >> [transform_users, transform_departments]

[transform_users, transform_departments] >> build_mart
```

Здесь сначала выполняется `get_data`, затем две задачи могут выполняться независимо друг от друга, а после их успешного завершения запускается `build_mart`.

Таким образом, зависимости позволяют описать порядок выполнения task'ов и определить, какие задачи должны завершиться перед запуском следующих.

</details>

**6. Как организован мониторинг pipeline?**

<details>
<summary><strong>Ответ на вопрос</strong></summary>

### Ответ

Мониторинг `pipeline` в основном выполняется средствами Airflow.

В `Airflow` можно отслеживать состояние `DAG` и отдельных `task`'ов, время их выполнения, ошибки и количество попыток.

Основные механизмы:

* **Статусы task'ов** — `success`, `failed`, `running`, `up_for_retry` и другие;
* **Retry** — автоматический повторный запуск `task` при ошибке;
* **SLA** — контроль соблюдения установленного времени выполнения;
* **Логи** — просмотр логов каждого `task` для поиска причины ошибки;
* **Sensors** — ожидание готовности данных или наступления определённого события;
* **Контроль качества данных** — отдельные `task` после загрузки могут проверять наличие данных, количество записей и другие условия.

Для уведомления о проблемах могут использоваться:

* **Email-рассылки** — уведомление об ошибках, нарушении `SLA` и других событиях;
* **Таблица мониторинга в БД** — хранение информации о запусках, статусах, времени выполнения и количестве обработанных записей;
* **Логирование через Python** — запись дополнительной информации о ходе выполнения скрипта.

Например, `pipeline` может выглядеть так:

```text
get_data
    ↓
load_to_impala
    ↓
build_mart
    ↓
check_data
```

Если `build_mart` завершился с ошибкой, Airflow фиксирует ошибку и сохраняет логи. Если настроен `Retry`, `task` будет автоматически перезапущен.

Если все попытки завершились ошибкой, `task` получает статус `failed`. После этого можно отправить уведомление о проблеме.

### Подробнее про Email

Уведомления об ошибках можно реализовать через `callback`.

Например:

```python
def send_failure_email(context):
    # отправка email
    pass


with DAG(
    dag_id="example",
    on_failure_callback=send_failure_email,
):
    ...
```

Callback будет вызван, когда произойдёт соответствующее событие, например ошибка `task` или успех или еще что-то.

Airflow передаёт в `context` информацию о текущем выполнении, из которой можно получить `DAG`, `task`, дату запуска, информацию об ошибке и другие данные.

На основе этой информации формируется уведомление и отправляется email через настроенный механизм отправки почты Airflow.

Callback также можно задавать непосредственно для отдельного `task`.

### Подробнее про логирование через Python

Для записи дополнительной информации о ходе выполнения используется стандартный Python `logging`:

```python
import logging

logger = logging.getLogger(__name__)

def load_data():
    logger.info("Начинаем загрузку")

    data = get_data()

    logger.info("Получено записей: %s", len(data))

    save_data(data)

    logger.info("Загрузка завершена")
```

Эти сообщения попадают в логи `task` и доступны через интерфейс Airflow.

При возникновении ошибки можно использовать:

```python
logger.exception("Ошибка при загрузке данных")
```

### Подробнее про таблицу мониторинга

Можно создать отдельную таблицу в БД, например:

```sql
CREATE TABLE pipeline_monitoring (
    dag_id          VARCHAR(255),
    task_id         VARCHAR(255),
    run_date        TIMESTAMP,
    status          VARCHAR(50),
    start_time      TIMESTAMP,
    end_time        TIMESTAMP,
    duration_sec    INTEGER,
    rows_processed  BIGINT
);
```

После выполнения `task` в неё можно записывать информацию о запуске:

```text
dag_id          = employee_mart
task_id         = build_mart
status          = success
duration_sec    = 850
rows_processed  = 125430
```

Такую таблицу можно использовать для построения дополнительного мониторинга и отчётности.

</details>








