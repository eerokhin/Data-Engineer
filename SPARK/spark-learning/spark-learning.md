# Spark Learning — запуск Apache Spark в Docker

## 1. Цель проекта

Цель — развернуть локальную среду Apache Spark с помощью Docker и научиться:

- запускать PySpark-приложения на Python;
- понимать архитектуру Spark-кластера;
- работать с DataFrame;
- изучать Jobs, Stages, Tasks и Executors через Spark UI;
- смотреть логи и диагностировать ошибки;
- управлять контейнерами через Docker Compose.

## 2. Используемые технологии

| Технология | Назначение |
|---|---|
| Docker Desktop | Запуск контейнеров |
| Docker Compose | Управление несколькими контейнерами |
| Apache Spark 4.0.1 | Распределённая обработка данных |
| PySpark | Python API для Spark |
| Spark Master | Координация кластера |
| Spark Worker | Предоставление вычислительных ресурсов |
| Spark UI | Мониторинг приложений и кластера |
| Python 3 | Написание кода обработки данных |

Рабочая директория проекта:

```text
spark-learning/
```

## 3. Архитектура

В проекте используются три контейнера:

- `spark-master` — координатор кластера;
- `spark-worker` — исполнитель, предоставляющий вычислительные ресурсы;
- `spark-app` — контейнер, в котором запускается Python-приложение и работает Spark Driver.

### Схема взаимодействия

```text
                    Docker Network
                          |
              +-----------------------+
              |      Spark Master     |
              |   spark-master:7077   |
              |      Web UI: 8080     |
              +-----------------------+
                          |
                  Регистрирует Worker
                          |
              +-----------------------+
              |      Spark Worker     |
              |      Web UI: 8081     |
              |                       |
              |  Запускает Executor    |
              +-----------------------+
                          |
                   Выполнение задач
                          |
              +-----------------------+
              |       Spark App       |
              |                       |
              |   Python / PySpark    |
              |      Spark Driver     |
              |      Spark UI: 4040   |
              +-----------------------+
```

Это схема логического взаимодействия компонентов, а не строгая последовательность сетевых соединений: Driver также взаимодействует с Executor напрямую.

### Spark Master

Master управляет ресурсами кластера на уровне планирования приложений.

Он:

- принимает регистрацию Worker;
- отслеживает доступные ресурсы;
- принимает заявки приложений;
- назначает ресурсы для запуска Executors.

Master не выполняет непосредственно вычисления над DataFrame.

<img width="1903" height="567" alt="image" src="https://github.com/user-attachments/assets/aa45a539-032b-4d90-ac3f-adbf970c2bd4" />


### Spark Worker

Worker предоставляет вычислительные ресурсы: CPU и память.

Он:

- регистрируется у Master;
- сообщает о доступных ресурсах;
- запускает Executors для приложений;
- предоставляет информацию о выполняющихся процессах.

<img width="1904" height="566" alt="image" src="https://github.com/user-attachments/assets/59ec7992-bd11-4499-bbcb-042b7fbd501f" />

### Spark Driver

Driver — управляющий компонент конкретного Spark-приложения.

Он:

- создаёт `SparkSession` и `SparkContext`;
- формирует план выполнения;
- разбивает вычисления на Jobs, Stages и Tasks;
- координирует выполнение задач на Executors.

В нашем проекте Driver работает внутри контейнера `spark-app`.

### Spark Executor

Executor — процесс, который выполняет задачи приложения и может хранить промежуточные данные в памяти или на диске.

В нашей конфигурации Worker предоставляет два CPU-ядра, а приложение получает Executor с двумя ядрами и примерно 1 GiB памяти.

Важно: Worker и Executor — не одно и то же. Worker является частью инфраструктуры кластера, а Executor относится к конкретному приложению.

## 4. Структура проекта

```text
spark-learning/
├── app/
│   └── main.py
└── docker-compose.yml
```

- `docker-compose.yml` описывает контейнеры, сеть и порты.
- `app/main.py` содержит PySpark-код.
- Каталог `app` подключается к контейнеру через volume, поэтому изменения файла доступны контейнеру без пересборки Docker-образа.

## 5. Полный docker-compose.yml

```yaml
services:
  spark-master:
    image: spark:4.0.1-python3
    container_name: spark-master
    command:
      - /opt/spark/bin/spark-class
      - org.apache.spark.deploy.master.Master
    environment:
      SPARK_MASTER_HOST: spark-master
      SPARK_MASTER_PORT: "7077"
      SPARK_MASTER_WEBUI_PORT: "8080"
    ports:
      - "8080:8080"
      - "7077:7077"
    networks:
      - spark-network

  spark-worker:
    image: spark:4.0.1-python3
    container_name: spark-worker
    command:
      - /opt/spark/bin/spark-class
      - org.apache.spark.deploy.worker.Worker
      - spark://spark-master:7077
    environment:
      SPARK_WORKER_CORES: "2"
      SPARK_WORKER_MEMORY: "2g"
      SPARK_WORKER_WEBUI_PORT: "8081"
    depends_on:
      - spark-master
    ports:
      - "8081:8081"
    networks:
      - spark-network

  spark-app:
    image: spark:4.0.1-python3
    container_name: spark-app
    command:
      - /opt/spark/bin/spark-submit
      - --master
      - spark://spark-master:7077
      - /app/main.py
    volumes:
      - ./app:/app
    ports:
      - "4040:4040"
      - "7078:7078"
      - "7079:7079"
    depends_on:
      - spark-master
      - spark-worker
    networks:
      - spark-network

networks:
  spark-network:
    driver: bridge
```

### Разбор конфигурации

**`image`**

```yaml
image: spark:4.0.1-python3
```

Используем Docker-образ Spark версии 4.0.1 с поддержкой Python.

**`command`**

Определяет команду, которая запускается внутри контейнера.

Для Master и Worker используется `spark-class`, для приложения — `spark-submit`.

**`environment`**

Настраивает компоненты Spark:

- `SPARK_MASTER_PORT` — порт взаимодействия с Master;
- `SPARK_MASTER_WEBUI_PORT` — порт веб-интерфейса Master;
- `SPARK_WORKER_CORES` — число CPU-ядер, доступных Worker;
- `SPARK_WORKER_MEMORY` — объём памяти, выделенный Worker;
- `SPARK_WORKER_WEBUI_PORT` — порт веб-интерфейса Worker.

**`ports`**

Формат:

```yaml
ports:
  - "8080:8080"
```

Первое число — порт на компьютере, второе — порт внутри контейнера.

Публикация портов позволяет открывать веб-интерфейсы из браузера Windows.

Порты `7078` и `7079` нужны для сетевого взаимодействия Driver и Executor. В этой конфигурации они опубликованы на хосте, а между контейнерами соединение происходит по внутренней Docker-сети.

**`volumes`**

```yaml
volumes:
  - ./app:/app
```

Подключает локальную папку `app` к папке `/app` внутри контейнера.

Это позволяет редактировать `main.py` на компьютере, а затем запускать обновлённый код в контейнере.

**`depends_on`**

Задаёт порядок запуска контейнеров. Однако сам по себе `depends_on` не гарантирует, что Master уже полностью готов принимать подключения.

**`networks`**

```yaml
networks:
  - spark-network
```

Все три контейнера подключены к общей Docker-сети. Поэтому они могут обращаться друг к другу по именам сервисов, например `spark-master` и `spark-app`.

## 6. Код приложения app/main.py

```python
import time

from pyspark.sql import SparkSession


spark = (
    SparkSession.builder
    .appName("SparkLearning")
    .master("spark://spark-master:7077")
    .config("spark.driver.bindAddress", "0.0.0.0")
    .config("spark.driver.host", "spark-app")
    .config("spark.driver.port", "7078")
    .config("spark.blockManager.port", "7079")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print("Spark version:", spark.version)

df = spark.createDataFrame(
    [
        ("Alice", "Data Engineer", 100),
        ("Bob", "Data Analyst", 80),
        ("Charlie", "Data Engineer", 120),
        ("Diana", "Data Scientist", 110),
    ],
    ["name", "role", "salary"],
)

df.show()

df.groupBy("role").avg("salary").show()

print("Spark UI is available while the application is running.")

time.sleep(300)

spark.stop()
```

### Что делает код

**1. Создаёт SparkSession**

```python
spark = (
    SparkSession.builder
    .appName("SparkLearning")
    .master("spark://spark-master:7077")
    # ...
    .getOrCreate()
)
```

`SparkSession` — основная точка входа для работы с DataFrame и SQL в PySpark.

`appName()` задаёт название приложения, которое видно в интерфейсе Master.

`master()` указывает адрес кластера, куда отправляется приложение.

`getOrCreate()` возвращает существующую сессию или создаёт новую.

**2. Настраивает сетевое взаимодействие Driver**

```python
.config("spark.driver.bindAddress", "0.0.0.0")
.config("spark.driver.host", "spark-app")
.config("spark.driver.port", "7078")
.config("spark.blockManager.port", "7079")
```

- `spark.driver.bindAddress` определяет локальный сетевой адрес, на котором Driver принимает подключения.
- `spark.driver.host` задаёт адрес, по которому другие компоненты должны обращаться к Driver.
- `spark.driver.port` фиксирует порт RPC-сервиса Driver.
- `spark.blockManager.port` фиксирует порт передачи блоков данных.

Почему это важно: Driver находится в контейнере, и Executor должен иметь возможность подключиться к нему по сети. В Docker имя `spark-app` разрешается во внутренний IP-адрес контейнера.

**3. Создаёт DataFrame**

```python
df = spark.createDataFrame(
    [
        ("Alice", "Data Engineer", 100),
        ("Bob", "Data Analyst", 80),
        ("Charlie", "Data Engineer", 120),
        ("Diana", "Data Scientist", 110),
    ],
    ["name", "role", "salary"],
)
```

Создаётся таблица с тремя колонками: имя, роль и зарплата.

**4. Выводит данные**

```python
df.show()
```

Метод `show()` запускает вычисление, необходимое для получения строк, и выводит таблицу в логи приложения.

**5. Группирует данные и вычисляет среднюю зарплату**

```python
df.groupBy("role").avg("salary").show()
```

Данные группируются по должности, после чего вычисляется среднее значение зарплаты для каждой группы.

Это пример агрегирующей операции, для которой Spark строит и выполняет план вычислений.

**6. Удерживает приложение запущенным**

```python
time.sleep(300)
```

Ожидание в течение 300 секунд, то есть пяти минут, нужно для изучения Spark UI.

После ожидания выполняется:

```python
spark.stop()
```

Сессия останавливается, приложение завершается, а его веб-интерфейс на порту 4040 становится недоступен.

## 7. Веб-интерфейсы Spark

У каждого компонента свой интерфейс.

| Адрес | Интерфейс | Что показывает |
|---|---|---|
| `http://localhost:8080` | Master UI | Worker, ресурсы кластера, приложения |
| `http://localhost:8081` | Worker UI | Ресурсы Worker и Executors |
| `http://localhost:4040` | Application UI | Jobs, Stages, Tasks, SQL/DataFrame, Executors |

### Master UI — порт 8080

Здесь можно проверить:

- зарегистрирован ли Worker;
- сколько CPU и памяти доступно;
- какие приложения зарегистрированы;
- состояние приложения.

### Worker UI — порт 8081

Здесь можно изучать состояние Worker, его ресурсы и запущенные Executors.

### Application UI — порт 4040

Это основной интерфейс для изучения выполнения PySpark-кода.

Полезные вкладки:

- **Jobs** — задания, инициированные действиями приложения;
- **Stages** — этапы выполнения Jobs;
- **Tasks** — отдельные задачи внутри Stage;
- **Storage** — кэшированные данные;
- **Environment** — настройки Spark;
- **Executors** — состояние Executors, использование памяти и статистика задач;
- **SQL/DataFrame** — планы выполнения SQL и DataFrame-операций.

Вкладки могут отличаться в зависимости от версии Spark и того, какие операции выполнялись.

### Как связаны Jobs, Stages и Tasks

```text
Action
  |
  v
 Job
  |
  v
Stages
  |
  v
Tasks
```

- **Job** создаётся, когда действие требует выполнения вычислений.
- **Stage** — часть Job, объединяющая задачи с учётом границ обмена данными между этапами.
- **Task** — единица работы над частью данных, выполняемая Executor.

Например, `df.groupBy("role").avg("salary").show()` может приводить к нескольким этапам выполнения из-за агрегации и обмена данными.

Не каждая строка Python создаёт отдельный Job: Spark использует ленивые вычисления и запускает необходимые вычисления при выполнении действий.

## 8. Запуск проекта

Все команды выполняются из директории `spark-learning`.

### Проверить Docker

```powershell
docker --version
docker compose version
docker info
```

### Проверить конфигурацию

```powershell
docker compose config
```

Эта команда проверяет и отображает итоговую конфигурацию Compose.

Если YAML содержит ошибки или сервис вложен не в тот раздел, ошибка появится на этом этапе.

### Запустить все контейнеры

```powershell
docker compose up -d
```

Флаг `-d` запускает контейнеры в фоновом режиме.

### Проверить состояние

```powershell
docker compose ps
```

Для просмотра также завершившихся контейнеров:

```powershell
docker compose ps -a
```

### Посмотреть логи приложения

```powershell
docker compose logs -f spark-app
```

`-f` означает непрерывный просмотр новых строк логов.

Чтобы выйти из просмотра логов, нажми `Ctrl+C`. Это прекращает просмотр, но само по себе не останавливает контейнер.

### Открыть интерфейсы

После запуска:

1. Открой `http://localhost:8080`.
2. Убедись, что Worker зарегистрирован.
3. Открой `http://localhost:8081`.
4. Открой `http://localhost:4040`, пока работает приложение.

## 9. Остановка и повторный запуск

### Остановить и удалить контейнеры проекта

```powershell
docker compose down
```

Команда останавливает и удаляет контейнеры проекта и созданную Compose сеть. Docker-образы при обычном выполнении этой команды остаются на компьютере.

### Запустить кластер и приложение заново

```powershell
docker compose up -d
```

При необходимости принудительно пересоздать контейнер приложения:

```powershell
docker compose up -d --force-recreate spark-app
```

Затем посмотреть логи:

```powershell
docker compose logs -f spark-app
```

## 10. Ошибки, с которыми столкнулись

### Ошибка 1. Неправильные отступы в docker-compose.yml

Сообщение:

```text
services.spark-worker additional properties 'spark-app' not allowed
```

Причина: сервис `spark-app` был помещён внутрь блока `spark-worker`, вместо того чтобы находиться на одном уровне с ним.

Неправильно:

```yaml
services:
  spark-worker:
    # настройки Worker
    spark-app:
      # настройки приложения
```

Правильно:

```yaml
services:
  spark-worker:
    # настройки Worker

  spark-app:
    # настройки приложения
```

В YAML отступы определяют структуру документа.

### Ошибка 2. Driver не мог привязаться к сетевому адресу

Сообщение:

```text
java.net.BindException: Cannot assign requested address
```

Причина: в настройке `spark.driver.host` был указан адрес `spark-master`, хотя Driver работает в контейнере `spark-app`.

Исправление:

```python
.config("spark.driver.bindAddress", "0.0.0.0")
.config("spark.driver.host", "spark-app")
.config("spark.driver.port", "7078")
.config("spark.blockManager.port", "7079")
```

После этого Driver смог запуститься, подключиться к Master и зарегистрировать BlockManager.

### Ошибка 3. Spark UI перестал открываться

Причина: приложение содержало ожидание:

```python
time.sleep(300)
```

Через пять минут выполнение продолжалось до `spark.stop()`, после чего приложение завершалось.

Это ожидаемое поведение: Spark Application UI доступен, пока работает приложение.

При этом Master и Worker могут продолжать работать, а их интерфейсы на портах 8080 и 8081 останутся доступными.

### Как диагностировать проблемы

Сначала:

```powershell
docker compose ps -a
```

Затем:

```powershell
docker compose logs --tail=50 spark-app
```

При проблемах с Master или Worker:

```powershell
docker compose logs --tail=50 spark-master
docker compose logs --tail=50 spark-worker
```

Эти команды помогают понять, завершился ли контейнер, возникла ли ошибка запуска или приложение работает, но не выполняет ожидаемые операции.

## 11. Что изучать дальше

1. Создать DataFrame из CSV-файла.
2. Научиться применять `select`, `filter`, `withColumn` и `groupBy`.
3. Изучить разницу между transformations и actions.
4. Посмотреть, когда появляются Jobs и Stages.
5. Выполнить `join` двух DataFrame и изучить план выполнения.
6. Сравнить `explain()` и визуальный план в Spark UI.
7. Изучить `repartition`, `coalesce` и shuffle.
8. Проверить, как меняются Tasks при разном количестве партиций.
9. Поэкспериментировать с `cache()` и `persist()`.
10. Научиться читать статистику Executors и находить узкие места.

## Итог

В результате мы развернули локальный Spark-кластер в Docker, подключили Python-приложение к Master, запустили вычисления на Worker и получили доступ к интерфейсам мониторинга.

Ключевое различие:

- Master управляет ресурсами кластера.
- Worker предоставляет ресурсы для выполнения вычислений.
- Driver координирует выполнение конкретного приложения.
- Executor выполняет задачи приложения.
- Spark UI позволяет наблюдать за работой кластера и приложения.
