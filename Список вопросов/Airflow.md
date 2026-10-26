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

Информацию о текущем выполнении `DAG` и `task` можно получить из `context`, который `Airflow` передаёт в `Python`-функцию или `callback`.

Например:

```python
def write_monitoring(context):
    dag_id = context["dag"].dag_id
    task_id = context["task_instance"].task_id
```

После этого полученные данные можно записать в БД с помощью `SQL INSERT`.

```text
context
   ↓
получаем dag_id, task_id и другую информацию
   ↓
формируем INSERT
   ↓
записываем данные в pipeline_monitoring
```

Такую таблицу можно использовать для построения дополнительного мониторинга и отчётности.

</details>

**7. Из каких основных частей состоит AirFlow?**

<details>
<summary><strong>Ответ на вопрос</strong></summary>

### Ответ

Основные компоненты Airflow:

* **Scheduler** — планировщик. Читает расписание и зависимости `DAG` и определяет, какие `task` и когда нужно запустить.

* **Executor** — определяет, как и где будут выполняться `task`. Основные варианты:

  * `SequentialExecutor` — последовательно, по одной задаче;
  * `LocalExecutor` — несколько задач параллельно на одной машине;
  * `CeleryExecutor` — распределяет задачи между несколькими `worker`'ами;
  * `KubernetesExecutor` — запускает задачи в отдельных Kubernetes Pod.

* **Worker** — объекты или процессы, которые выполняют задачи, назначенные исполнителем. Воркеры могут быть частью планировщика или отдельным компонентом. Их роль и наличие зависят от выбранного исполнителя. Например, при использовании `SequentialExecutor` или `LocalExecutor` `worker'ы` — часть процесса. В случае с `CeleryExecutor` они могут быть отдельными процессами или даже машинами.

* **Metadata Database** — служебная БД Airflow. Хранит статусы `task`, историю запусков, информацию о `DAG`, `Connections`, `Variables`, `XCom` и другие служебные данные.

* **Webserver** — веб-интерфейс Airflow. Через него можно запускать `DAG`, смотреть статусы `task`, логи и историю выполнения.

Дополнительно:

* **Triggerer** — обрабатывает отложенные (`deferrable`) задачи, чтобы они не занимали `worker` во время ожидания.
* **DAG Processor** — разбирает Python-файлы с `DAG` и подготавливает их структуру для Airflow.
* **Plugins** — позволяют расширять функциональность Airflow.

### Как компоненты взаимодействуют

Планировщик (Scheduler) или выделенный DAG-процессор считывает `Python`-файлы из папки `DAG_FOLDER` и сериализует их структуру в Базу метаданных.

Планировщик проверяет расписания. Если пришло время запустить `DAG`, он создаёт `DAG Run` и ставит задачи в очередь.

Исполнитель (`Executor`) получает задачи от планировщика и отправляет их в брокер сообщений (`Redis/RabbitMQ`).

Воркеры слушают брокера, забирают задачи и выполняют код.

По завершении задачи воркер обновляет статус в Базе метаданных.

Веб-сервер читает Базу метаданных и отображает актуальную информацию пользователю.

Воркеры записывают логи в указанное хранилище (локальная файловая система, `S3`, `GCS`), откуда веб-сервер может их прочитать.

### Что важно запомнить

**Scheduler** — когда запускать.
**Executor** — как выполнять.
**Worker** — выполняет.
**Metadata DB** — хранит состояние.
**Webserver** — показывает информацию в UI.
**Triggerer** — обслуживает отложенные задачи.

</details>

**8. Какие операторы вы знаете?**

<details>
<summary><strong>Ответ на вопрос</strong></summary>

### Ответ

**Operator** — это шаблон, который определяет, какую работу будет выполнять `task`.

Основные операторы:

* **`PythonOperator`** — выполнение Python-функции.

```python
PythonOperator(
    task_id="load_data",
    python_callable=load_data,
)
```

* **`SQLExecuteQueryOperator`** — выполнение SQL-запросов в подключённой БД.

```python
SQLExecuteQueryOperator(
    task_id="build_mart",
    conn_id="source_db",
    sql="SELECT * FROM staging.employee;",
)
```

* **`BashOperator`** — выполнение команд и shell-скриптов.

```python
BashOperator(
    task_id="run_script",
    bash_command="python /opt/airflow/dags/scripts/load_data.py",
)
```

* **`BranchPythonOperator`** — выбор одной из веток DAG в зависимости от результата Python-функции.

```text
             check_data
             /        \
            ↓          ↓
      process_data   skip_data
```

* **`EmailOperator`** — отправка email.

* **`EmptyOperator`** — ничего не выполняет и используется для организации структуры и ветвления DAG.

### Что использовал

В основном использовал:

* `PythonOperator` — для Python-логики и работы с API;
* SQL-операторы — для выполнения SQL и формирования витрин.

Также знаком с `BashOperator`, `BranchPythonOperator` и `EmptyOperator`.

### Важно

`Operator` определяет, **как выполняется конкретный task**.

Например:

```python
load_data = PythonOperator(
    task_id="load_data",
    python_callable=load_data_func,
)
```

Здесь `PythonOperator` — класс оператора, а `load_data` — конкретный `task`, созданный на его основе.

</details>

**9. Что такое сенсор и для чего он нужен?**

<details>
<summary><strong>Ответ на вопрос</strong></summary>

### Ответ

**Sensor** — это специальный тип `task`, который **ждёт наступления определённого условия или события**, прежде чем продолжить выполнение DAG.

Например, если следующий этап обработки можно запускать только после появления файла:

```text
wait_for_file
      ↓
process_data
      ↓
build_mart
```

`Sensor` будет периодически проверять, появился ли нужный файл.

Пример:

```python
from datetime import datetime

from airflow import DAG
from airflow.sensors.filesystem import FileSensor
from airflow.operators.python import PythonOperator


def process_file():
    print("Файл найден, начинаем обработку")


with DAG(
    dag_id="sensor_example",
    start_date=datetime(2026, 10, 1),
    schedule=None,
    catchup=False,
) as dag:

    wait_for_file = FileSensor(
        task_id="wait_for_file",
        filepath="/opt/airflow/data/input.csv",
        poke_interval=30,
        timeout=60 * 10,
        mode="reschedule",
    )

    process = PythonOperator(
        task_id="process_file",
        python_callable=process_file,
    )

    wait_for_file >> process
```

Здесь:

* `filepath` — файл, появления которого ждём;
* `poke_interval` — как часто проверять условие;
* `timeout` — максимальное время ожидания;
* `mode="reschedule"` — после проверки Sensor освобождает worker и будет запущен снова позже.

### Принцип работы

```text
Sensor запустился
       ↓
Условие выполнено?
   ↙           ↘
  Нет           Да
   ↓             ↓
Ждём         Sensor → success
   ↓                       ↓
повторная проверка      следующий task
```

Например:

```text
wait_for_file
      ↓
   FileSensor
      ↓
файл появился?
      ↓
   SUCCESS
      ↓
process_data
```

Sensor нужен, когда **нельзя просто сразу запускать следующий task**, потому что сначала необходимо дождаться внешнего события: появления файла, готовности данных, завершения другого процесса и т.д.

### Sensor vs обычный task

Обычный `task` выполняет работу:

```text
load_data → загружает данные
```

Sensor в основном **ждёт**:

```text
wait_for_data → ждёт, пока данные станут доступны
```

</details>

**10. Таска в AirFlow упала с ошибкой, как сделать так, чтобы несмотря на ошибку, следующая таска запустилась?**

<details>
<summary><strong>Ответ на вопрос</strong></summary>

### Ответ

Для этого используется параметр **`trigger_rule`**.

По умолчанию у `task` используется:

```python
from airflow.utils.trigger_rule import TriggerRule

trigger_rule=TriggerRule.ALL_SUCCESS
```

То есть следующая `task` запустится только если все upstream-задачи завершились успешно.

Если нужно запустить `task` независимо от того, успешно или с ошибкой завершилась предыдущая, можно использовать:

```python
trigger_rule=TriggerRule.ALL_DONE
```

Пример:

```python
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule

task_1 = PythonOperator(
    task_id="task_1",
    python_callable=some_function,
)

task_2 = PythonOperator(
    task_id="task_2",
    python_callable=another_function,
    trigger_rule=TriggerRule.ALL_DONE,
)

task_1 >> task_2
```

В этом случае:

```text
task_1
   ↓
 ┌───────┐
 │       │
SUCCESS  FAILED
 │       │
 └───┬───┘
     ↓
  task_2
```

`task_2` запустится в обоих случаях.

### Когда это используется

Например, для финального `task`, который должен выполняться независимо от результата предыдущих задач:

```text
load_data
    ↓
build_mart
    ↓
send_notification
```

Если `build_mart` упал, `send_notification` всё равно может запуститься и отправить уведомление об ошибке.

Другой пример — очистка временных файлов:

```text
load_data
    ↓
cleanup
```

Даже если `load_data` завершился с ошибкой, `cleanup` должен выполниться.

### Другие основные `trigger_rule`

```python
TriggerRule.ALL_SUCCESS   # все upstream успешны
TriggerRule.ALL_DONE      # все upstream завершились
TriggerRule.ONE_SUCCESS   # хотя бы один upstream успешен
TriggerRule.ONE_FAILED    # хотя бы один upstream упал
TriggerRule.NONE_FAILED   # ни один upstream не упал
TriggerRule.NONE_SKIPPED  # ни один upstream не пропущен
```

Важно: `ALL_DONE` означает, что upstream-задачи **завершили выполнение**, независимо от их результата. Это не означает, что они завершились успешно.

</details>

**11. Как в AirFlow в зависимости от условия продолжить обработку по нужной ветке ДАГа?**

<details>
<summary><strong>Ответ на вопрос</strong></summary>

### Ответ

Для этого используется **`BranchPythonOperator`**.

Он позволяет в зависимости от условия выбрать, **по какой ветке DAG продолжить выполнение**.

`BranchPythonOperator` вызывает Python-функцию, которая должна вернуть `task_id` следующей задачи.

Полный пример:

```python id="7k2m4p"
from datetime import datetime

from airflow import DAG
from airflow.operators.python import BranchPythonOperator, PythonOperator


def check_data():
    data_exists = True

    if data_exists:
        return "process_data"
    else:
        return "skip_data"


def process_function():
    print("Обрабатываем данные")


def skip_function():
    print("Данных нет, пропускаем обработку")


with DAG(
    dag_id="branching_example",
    start_date=datetime(2026, 10, 1),
    schedule=None,
    catchup=False,
) as dag:

    check = BranchPythonOperator(
        task_id="check_data",
        python_callable=check_data,
    )

    process_data = PythonOperator(
        task_id="process_data",
        python_callable=process_function,
    )

    skip_data = PythonOperator(
        task_id="skip_data",
        python_callable=skip_function,
    )

    check >> [process_data, skip_data]
```

Логика DAG:

```text
             check_data
                  ↓
           ┌──────┴──────┐
           ↓             ↓
    process_data      skip_data
```

Если `check_data()` возвращает:

```python id="2yq6fr"
return "process_data"
```

то:

```text
check_data → process_data
```

а `skip_data` будет пропущена (`skipped`).

Если возвращает:

```python id="6j5t8w"
return "skip_data"
```

то:

```text
check_data → skip_data
```

а `process_data` будет пропущена.

### Важный момент

Функция, переданная в `BranchPythonOperator`, должна вернуть **`task_id` существующей downstream-задачи**:

```python id="7p8q1z"
return "process_data"
```

Здесь `"process_data"` соответствует:

```python id="8n4v6s"
process_data = PythonOperator(
    task_id="process_data",
    ...
)
```

То есть `BranchPythonOperator` **не выполняет обработку данных сам**, а только определяет, какую ветку DAG запустить.

</details>

**12. Что такое XCOM?**

<details>
<summary><strong>Ответ на вопрос</strong></summary>

### Ответ

**XCom (Cross-Communication)** — механизм Airflow для передачи **небольших значений между task**.

Например, одна task получила путь к файлу, а следующей task нужно этот путь получить.

### Пример

Полный DAG:

```python id="q7v3nk"
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator


def get_file():
    return "/data/input.csv"


def process_file(**context):
    file_path = context["ti"].xcom_pull(
        task_ids="get_file"
    )

    print(f"Обрабатываем файл: {file_path}")


with DAG(
    dag_id="xcom_example",
    start_date=datetime(2026, 10, 1),
    schedule=None,
    catchup=False,
) as dag:

    get_data = PythonOperator(
        task_id="get_file",
        python_callable=get_file,
    )

    process = PythonOperator(
        task_id="process_file",
        python_callable=process_file,
    )

    get_data >> process
```

### Как это работает

Первая task:

```python id="j2m8rf"
def get_file():
    return "/data/input.csv"
```

возвращает:

```text
/data/input.csv
```

Airflow автоматически сохраняет возвращаемое значение в **XCom**.

Следующая task получает его:

```python id="2r7h4k"
file_path = context["ti"].xcom_pull(
    task_ids="get_file"
)
```

Здесь:

```text id="k9m2qw"
task_ids="get_file"
          ↓
Airflow ищет XCom,
который записала task get_file
          ↓
"/data/input.csv"
```

Общая схема:

```text id="p5v8cx"
get_file
    │
    │ return "/data/input.csv"
    ↓
  XCom
    │
    │ xcom_pull()
    ↓
process_file
```

### Важно

XCom предназначен для передачи **небольших значений**, например:

* ID;
* пути к файлу;
* даты;
* небольших параметров;
* количества обработанных строк.

Не стоит передавать через XCom большие объёмы данных, например DataFrame на миллионы строк.

Для больших данных используется внешнее хранилище:

```text id="u3k7pd"
Task 1
   ↓
HDFS / S3 / БД
   ↓
Task 2
```

А через XCom можно передать только путь или идентификатор:

```text id="z6n4rs"
Task 1
   ↓
XCom: "/data/file.parquet"
   ↓
Task 2
   ↓
читает файл из HDFS/S3
```

**Коротко**

> XCom — механизм Airflow для передачи небольших значений между task. Например, одна task может передать следующей путь к файлу, ID или другой небольшой параметр. Большие объёмы данных через XCom не передают.

</details>

**13. Какие базы данных используется в Airflow?**

<details>
<summary><strong>Ответ на вопрос</strong></summary>

### Ответ

Airflow использует **Metadata Database** — служебную базу данных, в которой хранится информация о работе самого Airflow.

В ней хранятся:

* DAG и DAG Run;
* Task Instance и их статусы;
* история запусков;
* Connections;
* Variables;
* XCom.

В качестве Metadata Database можно использовать:

* **PostgreSQL**;
* **MySQL**.

Для локальной разработки также может использоваться **SQLite**.

Например, если Airflow работает с PostgreSQL:

```text id="c7m2pa"
              Airflow
                 │
                 ↓
            PostgreSQL
                 │
          Metadata Database
```

Airflow записывает туда информацию о выполнении DAG:

```text id="p8v4kx"
DAG запустился
      ↓
Task выполняется
      ↓
статус → running
      ↓
Task завершилась
      ↓
статус → success / failed
```

При этом **бизнес-данные туда не складываются**.

Например, если DAG загружает данные в Impala, сами данные находятся в Impala/Hadoop, а информация о выполнении этого DAG — в Metadata Database Airflow.

### Коротко

> В Airflow используется Metadata Database — служебная БД для хранения информации о DAG, task, их статусах, Connections, Variables, XCom и истории запусков. В production обычно используют PostgreSQL или MySQL, а SQLite подходит в основном для локальной разработки.

</details>


**14. Чем отличается Celery Executor и local executor?**

<details>
<summary><strong>Ответ на вопрос</strong></summary>

### Ответ

Главное отличие **`LocalExecutor`** и **`CeleryExecutor`** — в том, где выполняются задачи.

### LocalExecutor

`LocalExecutor` запускает задачи **на той же машине, где работает Airflow**.

При этом задачи могут выполняться **параллельно в отдельных процессах**.

```text
                 Airflow
                    │
             LocalExecutor
          ┌─────────┼─────────┐
          ↓         ↓         ↓
       Task 1    Task 2    Task 3
          │         │         │
          └─────────┴─────────┘
              одна машина
```

Например, если на сервере Airflow есть 8 CPU, несколько task могут одновременно выполняться на этом сервере.

### CeleryExecutor

`CeleryExecutor` позволяет распределять задачи **между несколькими worker-машинами**.

Схема выглядит примерно так:

```text
                 Airflow
                    │
             CeleryExecutor
                    │
              Message Broker
             (Redis / RabbitMQ)
                    │
        ┌───────────┼───────────┐
        ↓           ↓           ↓
    Worker 1    Worker 2    Worker 3
        ↓           ↓           ↓
     Task 1      Task 2      Task 3
```

Scheduler передаёт задачу Executor, Executor отправляет её в очередь, а свободный worker забирает задачу и выполняет её.

### Основное отличие

|                      | LocalExecutor              | CeleryExecutor                  |
| -------------------- | -------------------------- | ------------------------------- |
| Где выполняются task | На одной машине            | На нескольких worker            |
| Параллельность       | Да                         | Да                              |
| Масштабирование      | Ограничено одной машиной   | Можно добавлять worker          |
| Broker               | Не нужен                   | Нужен, например Redis/RabbitMQ  |
| Подходит для         | Небольших/средних нагрузок | Больших распределённых нагрузок |

### Пример

Допустим, у нас 100 task:

```text
LocalExecutor:

Airflow Server
├── Task 1
├── Task 2
├── Task 3
├── ...
└── Task 100
```

Все они выполняются на одном сервере, насколько позволяют его ресурсы и настройки параллельности.

С `CeleryExecutor`:

```text
                Airflow
                   ↓
                Celery
                   ↓
             ┌─────┴─────┐
             ↓     ↓     ↓
          Worker1 Worker2 Worker3
             ↓     ↓     ↓
           Task  Task   Task
```

Можно добавить новые worker, и задачи будут распределяться между ними.

### Коротко

> `LocalExecutor` выполняет задачи параллельно на одной машине с Airflow. `CeleryExecutor` позволяет распределять задачи между несколькими worker-машинами через очередь сообщений, например Redis или RabbitMQ. Поэтому CeleryExecutor лучше подходит для масштабирования.

</details>


**15. Что такое PythonSensor?**

<details>
<summary><strong>Ответ на вопрос</strong></summary>

# PythonSensor в Apache Airflow

`PythonSensor` — это сенсор Airflow, который периодически вызывает Python-функцию и ждёт, пока она вернёт `True`.

**Основная задача:** дождаться выполнения определённого условия перед запуском следующих задач DAG.

Например, перед сборкой витрины в Impala нужно дождаться, пока все исходные таблицы будут готовы.

## 1. Как работает PythonSensor

```text
         PythonSensor
               |
               v
    Вызов функции check_sources()
               |
               v
       Все источники готовы?
          /          \
        Нет            Да
         |              |
         v              v
   Ожидание          Успешное
   следующей         завершение
   проверки              |
         |                v
         +----------> update_mart
```

Функция проверки должна возвращать:
- `False` — условие пока не выполнено, нужно продолжать ожидание.
- `True` — условие выполнено, сенсор завершается успешно.

## 2. Пример PythonSensor

```python
from datetime import datetime

from airflow import DAG
from airflow.sensors.python import PythonSensor
from airflow.operators.python import PythonOperator


def check_sources():
    """
    Проверить готовность исходных таблиц.

    True  — все источники готовы.
    False — хотя бы один источник не готов.
    """
    return False  # Здесь должна быть реальная проверка


def update_mart():
    print("Начинаем обновление витрины")


with DAG(
    dag_id="example_python_sensor",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
) as dag:

    wait_for_sources = PythonSensor(
        task_id="wait_for_sources",
        python_callable=check_sources,
        poke_interval=3600,
        timeout=86400,
        mode="reschedule",
    )

    update = PythonOperator(
        task_id="update_mart",
        python_callable=update_mart,
    )

    wait_for_sources >> update
```

В этом примере `check_sources()` всегда возвращает `False`, поэтому сенсор будет ждать до истечения тайм-аута.

В рабочем DAG вместо заглушки нужно реализовать проверку готовности источников.

## 3. Разбор параметров

```python
wait_for_sources = PythonSensor(
    task_id="wait_for_sources",
    python_callable=check_sources,
    poke_interval=3600,
    timeout=86400,
    mode="reschedule",
)
```

| Параметр | Значение | Объяснение |
|---|---|---|
| `task_id` | `"wait_for_sources"` | Идентификатор задачи в DAG |
| `python_callable` | `check_sources` | Функция, которая проверяет условие |
| `poke_interval` | `3600` | Интервал между проверками — 1 час |
| `timeout` | `86400` | Максимальное время ожидания — 24 часа |
| `mode` | `"reschedule"` | Освобождение слота выполнения между проверками |

### `task_id`

Имя задачи, которое отображается в интерфейсе Airflow и используется при настройке зависимостей.

### `python_callable`

Функция, которую Airflow вызывает при проверке условия.

```python
def check_sources():
    return True
```

Если функция вернёт `True`, сенсор завершится успешно.

Если вернёт `False`, сенсор продолжит ожидание.

### `poke_interval`

Интервал между проверками в секундах.

```python
poke_interval=3600
```

3600 секунд = 60 минут = 1 час.

### `timeout`

Максимальное время ожидания в секундах.

```python
timeout=86400
```

86400 секунд = 24 часа.

Если условие не выполнено в течение допустимого времени, сенсор завершится с ошибкой тайм-аута.

### `mode="reschedule"`

Определяет поведение сенсора между проверками.

- `poke` — сенсор остаётся выполняющейся задачей и удерживает рабочий слот между проверками.
- `reschedule` — после неудачной проверки Airflow переводит задачу в состояние ожидания следующего запуска, освобождая слот выполнения.

**Рабочий слот** — доступная единица выполнения задачи в инфраструктуре Airflow. Количество доступных слотов зависит от настроек исполнителя и ограничений пула.

`reschedule` особенно полезен, когда сенсор может ждать часами.

## 4. Что происходит в течение суток

При настройках:

```python
poke_interval=3600
timeout=86400
mode="reschedule"
```

поведение будет примерно следующим:

| Время | Действие |
|---|---|
| 00:00 | Первая проверка источников |
| 01:00 | Повторная проверка |
| 02:00 | Следующая проверка |
| ... | Проверки продолжаются |
| До истечения тайм-аута | Сенсор продолжает ждать |
| После истечения тайм-аута | Сенсор завершается с ошибкой, если условие не выполнено |

Фактическое время проверок может немного отличаться от заданного интервала из-за планировщика и доступности ресурсов.

## 5. Что будет, если источники не готовы через сутки?

Допустим, DAG содержит последовательность:

```python
wait_for_sources >> update_mart >> check_result
```

Если источники не будут готовы в течение 24 часов:

1. `wait_for_sources` завершится со статусом `Failed`.
2. `update_mart` не запустится при стандартных настройках зависимостей.
3. `check_result` также не запустится.

Это предотвращает сборку витрины на неполных данных.

## 6. Как настроить повторные попытки

Можно добавить `retries` и `retry_delay`:

```python
from datetime import timedelta

wait_for_sources = PythonSensor(
    task_id="wait_for_sources",
    python_callable=check_sources,
    poke_interval=3600,
    timeout=86400,
    mode="reschedule",
    retries=2,
    retry_delay=timedelta(minutes=30),
)
```

Здесь:
- `retries=2` — до двух повторных попыток после первой неудачи.
- `retry_delay=timedelta(minutes=30)` — пауза в 30 минут между попытками.

Важно: каждая повторная попытка может снова ожидать до 24 часов. Поэтому общее время выполнения задачи способно превысить сутки.

## 7. Применение в ETL-процессах

`PythonSensor` полезен, когда перед запуском обработки необходимо дождаться внешнего события или готовности данных.

| Сценарий | Условие готовности |
|---|---|
| Загрузка файлов | Файл появился в нужной директории |
| Источники в Impala | В таблицах появились необходимые данные |
| Интеграция с API | Внешний процесс завершил получение данных |
| Обновление витрины | Все необходимые источники готовы |

Например, для витрины встреч сотрудников можно проверять готовность исходных таблиц, а затем запускать задачу сборки витрины.

Важно: если проверка обращается к Impala, функция `check_sources()` должна самостоятельно подключиться к базе, выполнить запросы и вернуть `True` только при выполнении заданных условий.

## Кратко

- `PythonSensor` — ждёт выполнения условия.
- `python_callable` — функция проверки.
- `poke_interval` — частота проверок.
- `timeout` — максимальное время ожидания.
- `mode="reschedule"` — освобождает слот выполнения между проверками.
- `retries` — число повторных попыток после ошибки.
- `retry_delay` — задержка между повторными попытками.

**Главная идея:** сенсор позволяет организовать зависимость между подготовкой источников и запуском ETL, не начиная обработку раньше времени.       

</details>


**16. Использовал ли ветвление (Branching)?**

<details>
<summary><strong>Ответ на вопрос</strong></summary>

Да, использовал.

## Branching (ветвление) в Apache Airflow

**Branching** — механизм, который позволяет выбирать дальнейший путь выполнения DAG в зависимости от определённого условия.

В своём DAG я использовал `BranchPythonOperator`, чтобы разделить логику сборки витрины на два сценария:

- **Первичная сборка** — создаётся итоговая витрина с нуля с помощью задачи `create_mart`. Тоесть выполняется DROP, CREATE итоговой витрины, первичная сборка, когда витирны еще нет.
- **Инкрементальное обновление** — создание витрины пропускается, выполнение продолжается с задачи `incremental_start`. Тоесть DROP, CREATE итоговой витрины не делаю, так как в ней уже есть данные, и новые данные добавляю инкрементом, повторная сборка.

Для выбора сценария используется функция `choose_calculation_mode`, которая возвращает `task_id` следующей задачи в зависимости от того, нужна первичная сборка или инкрементальное обновление.

### Пример

```python
from datetime import datetime
from airflow import DAG
from airflow.operators.python import (BranchPythonOperator,PythonOperator,)
from airflow.operators.empty import EmptyOperator

CREATE_SQL = "/opt/airflow/sql/create_mart.sql"

# Функция выбора сценария
def choose_calculation_mode():
    if is_first_run():
        return "create_mart"
    return "incremental_start"

def is_first_run():
    # Пример условной проверки
    return True

def execute_sql_file(file_path, **context):
    print(f"Выполняем SQL-файл: {file_path}")


with DAG(
    dag_id="example_branching",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
) as dag:

    # Выбираем первичную сборку или инкрементальный режим
    choose_mode = BranchPythonOperator(
        task_id="choose_calculation_mode",
        python_callable=choose_calculation_mode,
    )

    # Первичная сборка витрины
    create_mart = PythonOperator(
        task_id="create_mart",
        python_callable=execute_sql_file,
        op_kwargs={"file_path": CREATE_SQL},
    )

    # Точка входа в инкрементальный сценарий
    incremental_start = EmptyOperator(
        task_id="incremental_start",
    )

    # Связи между задачами
    choose_mode >> [create_mart, incremental_start]
```



Здесь `is_first_run()` — условная проверка, иллюстрирующая принцип работы.

Таким образом, ветвление позволяет **использовать один DAG для первичной сборки и последующих инкрементальных обновлений**, не выполняя создание витрины заново при каждом запуске.

</details>


**17. Что такое Trigger Rule в Apache Airflow?**

<details>
<summary><strong>Ответ на вопрос</strong></summary>

## Trigger Rule в Apache Airflow

**`trigger_rule`** — это правило, которое определяет, при каких статусах upstream-задач (предшествующих задач) может запуститься текущая задача.

### Зачем нужен `trigger_rule`?

Например, мы используем **Branching (ветвление)**. Airflow выбирает одну ветку, а другую пропускает — она получает статус `skipped`.

Но нам нужно продолжить выполнение DAG и запустить следующую задачу, которая объединяет ветки.

По умолчанию Airflow использует правило `all_success`:

| Правило | Условие запуска |
|---|---|
| `all_success` *(по умолчанию)* | Все upstream-задачи завершились со статусом `success`. |
| `none_failed_min_one_success` | Нет задач со статусами `failed` или `upstream_failed`, и хотя бы одна задача завершилась со статусом `success`. |
| `all_done` | Все upstream-задачи завершились, независимо от их статусов. |
| `one_success` | Хотя бы одна upstream-задача завершилась со статусом `success`. |
| `one_failed` | Хотя бы одна upstream-задача завершилась со статусом `failed` или `upstream_failed`. |
| `none_failed` | Все upstream-задачи завершились, и ни одна не имеет статуса `failed` или `upstream_failed`. |
| `all_skipped` | Все upstream-задачи имеют статус `skipped`. |

При ветвлении одна задача может завершиться со статусом `success`, а другая — `skipped`. В таком случае `all_success` не позволит запустить следующую задачу, а `none_failed_min_one_success` позволит, если выполнены его условия.

### Пример DAG с Branching и Trigger Rule

В примере DAG выбирает режим сборки витрины, затем объединяет ветки и запускает `update_mart`.

```python
from datetime import datetime

from airflow import DAG
from airflow.operators.python import (
    BranchPythonOperator,
    PythonOperator,
)
from airflow.operators.empty import EmptyOperator


CREATE_SQL = "/opt/airflow/sql/create_mart.sql"
INCREMENT_SQL = "/opt/airflow/sql/increment_mart.sql"


# Выбираем первичную сборку или инкрементальное обновление.
def choose_calculation_mode():
    if is_first_run():
        return "create_mart"
    return "incremental_start"


def is_first_run():
    # Пример условной проверки.
    return True


def execute_sql_file(file_path, **context):
    print(f"Выполняем SQL-файл: {file_path}")


with DAG(
    dag_id="example_branching_trigger_rule",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
) as dag:

    # Выбираем ветку выполнения.
    choose_mode = BranchPythonOperator(
        task_id="choose_calculation_mode",
        python_callable=choose_calculation_mode,
    )

    # Первичная сборка витрины.
    create_mart = PythonOperator(
        task_id="create_mart",
        python_callable=execute_sql_file,
        op_kwargs={"file_path": CREATE_SQL},
    )

    # Точка входа в инкрементальный сценарий.
    incremental_start = EmptyOperator(
        task_id="incremental_start",
    )

    # Объединяем ветки после выбора режима.
    merge_branches = EmptyOperator(
        task_id="merge_branches",
        trigger_rule="none_failed_min_one_success",
    )

    # Продолжаем обработку после объединения веток.
    update_mart = PythonOperator(
        task_id="update_mart",
        python_callable=execute_sql_file,
        op_kwargs={"file_path": INCREMENT_SQL},
    )

    # Связываем задачи.
    choose_mode >> [create_mart, incremental_start]
    [create_mart, incremental_start] >> merge_branches
    merge_branches >> update_mart
```

<img width="1077" height="240" alt="image" src="https://github.com/user-attachments/assets/c12f8ef4-e5bf-45f8-a55d-77dfaf6ad31f" />

### Как работает DAG

1. `choose_calculation_mode` выбирает одну из двух веток.
2. Если это первичная сборка, выполняется `create_mart`.
3. Если это инкрементальный запуск, выполняется `incremental_start`.
4. Не выбранная ветка получает статус `skipped`.
5. `merge_branches` запускается благодаря `none_failed_min_one_success`.
6. После объединения выполняется `update_mart`.

**Главное, что нужно запомнить:** `trigger_rule` управляет условиями запуска задачи на основе статусов её upstream-задач. При ветвлении он позволяет корректно продолжить выполнение DAG после выбора одной ветки.

В примере `is_first_run()` и `execute_sql_file()` — демонстрационные функции. В реальном DAG их нужно заменить проверкой режима сборки и реализацией выполнения SQL в Impala.

</details>
