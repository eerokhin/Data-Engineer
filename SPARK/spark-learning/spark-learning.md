# Spark Learning — запуск Apache Spark в Docker

## 1. Цель проекта

Учебный проект для знакомства с Apache Spark и PySpark на локальном компьютере с Windows.

В рамках проекта мы:
- запускаем Spark-кластер с помощью Docker Compose;
- изучаем архитектуру Spark;
- подключаем Python-приложение к кластеру;
- создаём DataFrame и выполняем операции над данными;
- изучаем Spark Web UI;
- разбираемся в ленивых вычислениях;
- учимся повторно запускать приложение после изменения кода.

## 2. Используемые технологии

- Docker Desktop
- Docker Compose
- Apache Spark 4.0.1
- PySpark
- Python 3
- Java 17
- Windows и PowerShell

## 3. Структура проекта

```text
spark-learning/
├── app/
│   └── main.py
├── docker-compose.yml
└── README.md
```

- `docker-compose.yml` — конфигурация контейнеров.
- `app/main.py` — Python-приложение на PySpark.
- `README.md` — документация проекта.

## 4. Архитектура Spark

В проекте используются Master, Worker, Driver и Executor.

### Master

Master управляет ресурсами кластера, принимает регистрацию Worker и помогает распределять ресурсы между приложениями.

Master не выполняет непосредственно преобразования DataFrame.

Адрес Master внутри Docker-сети:

```text
spark://spark-master:7077
```

Это внутренний адрес для подключения Spark-приложений, а не URL веб-страницы.

### Worker

Worker — рабочий узел, предоставляющий ресурсы для выполнения задач.

В нашем проекте Worker настроен на:
- 2 CPU cores;
- 2 GiB памяти.

### Driver

Driver управляет выполнением конкретного Spark-приложения. Он формирует план вычислений, организует выполнение заданий и взаимодействует с Executor.

В нашем проекте Driver запускается внутри контейнера `spark-app` вместе с Python-приложением.

### Executor

Executor выполняет задачи Spark и обрабатывает данные. Он запускается на Worker и взаимодействует с Driver.

### Схема взаимодействия

```text
Python-код: app/main.py
          |
          v
        Driver
          |
          v
     Spark Master
          |
          v
        Worker
          |
          v
       Executor
          |
          v
  Выполнение задач Spark
```

Важно различать роли:
- Master управляет ресурсами кластера.
- Driver управляет конкретным приложением.
- Worker предоставляет вычислительные ресурсы.
- Executor выполняет задачи.

В нашем проекте один Worker. Это позволяет изучать устройство Spark, но пока не демонстрирует преимущества распределения вычислений между несколькими рабочими узлами.

## 5. Полная конфигурация docker-compose.yml

Файл `docker-compose.yml`:

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
    profiles:
      - app
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

### Как работает конфигурация

**`image`**

```yaml
image: spark:4.0.1-python3
```

Docker использует образ Spark с Python. Если образ ещё не скачан, Docker загрузит его при необходимости.

**`command`**

Задаёт команду запуска компонента Spark внутри контейнера.

Для Master запускается класс:

```text
org.apache.spark.deploy.master.Master
```

Для Worker запускается класс:

```text
org.apache.spark.deploy.worker.Worker
```

Worker получает адрес Master:

```text
spark://spark-master:7077
```

**`environment`**

Настраивает параметры компонентов. Например, `SPARK_WORKER_CORES` и `SPARK_WORKER_MEMORY` задают ресурсы, которые Worker предоставляет Spark.

**`ports`**

Связывает порты контейнера с портами Windows.

| Порт | Назначение |
|---|---|
| 8080 | Master Web UI |
| 8081 | Worker Web UI |
| 7077 | Подключение к Master |
| 4040 | Application Web UI |
| 7078 | Порт Driver |
| 7079 | Порт Block Manager Driver |

Порты 7078 и 7079 опубликованы для связи компонентов Spark в текущей Docker-конфигурации.

**`volumes`**

```yaml
volumes:
  - ./app:/app
```

Связывает локальную папку `app` с папкой `/app` внутри контейнера.

Поэтому после изменения `main.py` не нужно пересобирать Docker-образ.

**`depends_on`**

Задаёт порядок запуска зависимостей. Однако сам по себе `depends_on` не гарантирует, что Master уже полностью готов принимать подключения.

**`networks`**

Все три сервиса подключаются к общей Docker-сети `spark-network` и могут обращаться друг к другу по именам сервисов.

**`profiles`**

```yaml
profiles:
  - app
```

Сервис `spark-app` относится к отдельному профилю. Обычный запуск `docker compose up -d` не запускает его автоматически.

## 6. Запуск проекта

Все команды выполняются из корневой папки проекта `spark-learning`.

### Запустить Master и Worker

```powershell
docker compose up -d
```

### Проверить контейнеры

```powershell
docker compose ps
```

Master и Worker должны находиться в состоянии `running`.

### Посмотреть логи

```powershell
docker compose logs spark-master
docker compose logs spark-worker
```

Для просмотра логов в реальном времени:

```powershell
docker compose logs -f spark-worker
```

Выход из просмотра логов — `Ctrl + C`. Это прекращает просмотр, а не останавливает контейнер.

### Запустить Python-приложение

```powershell
docker compose run --rm --service-ports --name spark-app spark-app
```

Эта команда запускает отдельный контейнер для приложения.

- `run` — запускает сервис в отдельном контейнере.
- `--rm` — удаляет контейнер после завершения.
- `--service-ports` — публикует порты сервиса.
- `--name spark-app` — задаёт имя контейнера.

Внутри контейнера выполняется команда `spark-submit`, которая запускает `app/main.py` и подключает приложение к Master.

### Остановить приложение

Если приложение запущено в текущем терминале, нажать:

```text
Ctrl + C
```

### Остановить кластер

```powershell
docker compose down
```

Эта команда останавливает и удаляет контейнеры проекта и созданную Compose сеть. Скачанные образы при этом не удаляются.

## 7. Spark Web UI

Spark предоставляет веб-интерфейсы для мониторинга кластера и приложений.

| Интерфейс | Адрес | Назначение |
|---|---|---|
| Master UI | http://localhost:8080 | Состояние кластера |
| Worker UI | http://localhost:8081 | Состояние рабочего узла |
| Application UI | http://localhost:4040 | Выполнение приложения |

### Master UI — порт 8080

Показывает:
- количество зарегистрированных Worker;
- доступные CPU cores;
- доступную память;
- запущенные и завершённые приложения.

Например:

```text
Workers: 1 Alive
Cores: 2 Total
Memory: 2.0 GiB Total
```

Это означает, что один Worker зарегистрирован, доступно два ядра CPU и 2 GiB памяти.

### Worker UI — порт 8081

Показывает информацию о конкретном Worker, его ресурсах и запущенных на нём приложениях или исполнителях.

### Application UI — порт 4040

Показывает выполнение конкретного приложения.

Основные разделы:

- **Jobs** — задания, запущенные приложением.
- **Stages** — этапы выполнения заданий.
- **Executors** — исполнители, их ресурсы и статистика.
- **SQL / DataFrame** — планы и статистика SQL/DataFrame-операций, если раздел доступен.

Application UI обычно доступен только во время работы приложения. Если приложение завершилось, страница может перестать открываться.

В нашем приложении используется `time.sleep(600)`, чтобы после вычислений оставить приложение работающим примерно на 10 минут и дать время изучить UI.

## 8. PySpark и DataFrame

PySpark — Python API для Apache Spark. Он позволяет описывать обработку данных с помощью Python.

DataFrame — распределённая коллекция данных с именованными столбцами и схемой. По смыслу он похож на таблицу в реляционной базе данных.

### Создание SparkSession

```python
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
```

`SparkSession` — основная точка входа для работы с DataFrame и SQL в PySpark.

- `appName()` задаёт имя приложения.
- `master()` указывает адрес Spark-кластера.
- `getOrCreate()` получает существующую сессию или создаёт новую.

Сетевые настройки Driver нужны, чтобы компоненты Spark могли связываться друг с другом в Docker-сети.

### Создание DataFrame

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

Данные создаются прямо в коде. Это учебный набор из четырёх строк, а не таблица из внешней базы данных.

Исходный DataFrame:

| name | role | salary |
|---|---|---:|
| Alice | Data Engineer | 100 |
| Bob | Data Analyst | 80 |
| Charlie | Data Engineer | 120 |
| Diana | Data Scientist | 110 |

### Показать данные

```python
df.show()
```

Выводит строки DataFrame в терминал.

### Выбрать столбцы

```python
df.select("name", "salary").show()
```

Аналог SQL:

```sql
SELECT name, salary
FROM employees;
```

### Отфильтровать строки

```python
from pyspark.sql.functions import col

df.filter(col("salary") > 90).show()
```

Аналог SQL:

```sql
SELECT *
FROM employees
WHERE salary > 90;
```

Останутся Alice, Charlie и Diana.

### Добавить вычисляемый столбец

```python
df.withColumn(
    "salary_with_bonus",
    col("salary") * 1.1
).show()
```

`withColumn()` возвращает новый DataFrame с дополнительным столбцом. Исходный DataFrame не изменяется.

### Группировка и средняя зарплата

```python
from pyspark.sql.functions import avg

df.groupBy("role").agg(
    avg("salary").alias("avg_salary")
).show()
```

Результат:

| role | avg_salary |
|---|---:|
| Data Analyst | 80 |
| Data Engineer | 110 |
| Data Scientist | 110 |

`groupBy()` группирует строки по должности, а `avg()` вычисляет среднее значение зарплаты в каждой группе.

## 9. Ленивые вычисления (Lazy Evaluation)

В Spark многие преобразования не выполняются сразу. Spark сначала описывает операции, которые нужно выполнить.

Например:

```python
filtered_df = df.filter(col("salary") > 90)
```

Эта строка обычно не запускает полное вычисление фильтра. Она создаёт описание преобразования.

Когда вызывается:

```python
filtered_df.show()
```

Spark запускает необходимые вычисления, чтобы получить и показать результат.

### Преобразования и действия

**Преобразования (transformations):**
- `select()`
- `filter()`
- `withColumn()`
- `groupBy()` — формирует объект группировки для последующей агрегации.

**Действия (actions):**
- `show()`
- `count()`
- `collect()`
- `write...`

Действие запускает вычисления, необходимые для получения результата.

Ленивое выполнение позволяет Spark строить и оптимизировать план обработки вместо немедленного выполнения каждого преобразования по отдельности.

## 10. Полный код приложения

Файл `app/main.py`:

```python
import time

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg

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

print("=== Original DataFrame ===")
df.show()

print("=== Select columns ===")
df.select("name", "salary").show()

print("=== Filter salary > 90 ===")
df.filter(col("salary") > 90).show()

print("=== Add salary bonus ===")
df.withColumn(
    "salary_with_bonus",
    col("salary") * 1.1
).show()

print("=== Average salary by role ===")
df.groupBy("role").agg(
    avg("salary").alias("avg_salary")
).show()

print("Application is running. Open http://localhost:4040")

time.sleep(600)

spark.stop()
```

## 11. Повторный запуск после изменения кода

После изменения `app/main.py`:

1. Сохранить файл через `Ctrl + S`.
2. Если предыдущий запуск ещё работает, остановить его через `Ctrl + C`.
3. Запустить приложение повторно:

```powershell
docker compose run --rm --service-ports --name spark-app spark-app
```

Master и Worker повторно запускать не нужно.

Docker-образ пересобирать не требуется: код приложения подключён через volume.

## 12. Диагностика проблем

### Проверить состояние контейнеров

```powershell
docker compose ps
```

### Проверить логи Master

```powershell
docker compose logs spark-master
```

### Проверить логи Worker

```powershell
docker compose logs spark-worker
```

### Посмотреть все контейнеры, включая завершённые

```powershell
docker compose ps -a
```

### Удалить остановленный контейнер приложения

```powershell
docker compose rm -f spark-app
```

Команда удаляет остановленный контейнер сервиса, но не удаляет исходный `app/main.py`.

### Предупреждение `Initial job has not accepted any resources`

Оно означает, что Spark пока не смог назначить ресурсы для выполнения задания.

Проверить:
1. Master UI — зарегистрирован ли Worker.
2. Достаточно ли свободных CPU и памяти.
3. Логи приложения и Worker.
4. Связь Executor с Driver.

Если Worker отображается как `ALIVE`, это подтверждает регистрацию Worker, но само по себе не гарантирует, что Executor сможет подключиться к Driver.

## 13. Что изучать дальше

1. Партиции DataFrame.
2. `repartition()` и `coalesce()`.
3. Логический и физический планы через `explain()`.
4. Shuffle и его влияние на производительность.
5. Чтение и запись CSV и Parquet.
6. Spark SQL и сравнение с PySpark DataFrame API.
7. Работа с несколькими Worker.
8. Оптимизация Spark-приложений.

## 14. Ключевые выводы

- Docker запускает инфраструктуру Spark в контейнерах.
- Master управляет ресурсами, Worker предоставляет их.
- Driver управляет приложением, Executor выполняет задачи.
- PySpark позволяет обрабатывать данные с помощью Python.
- DataFrame предоставляет операции, похожие на SQL.
- Ленивые вычисления позволяют Spark оптимизировать выполнение операций.
- Spark UI показывает состояние кластера и ход выполнения приложения.
- Изменённый Python-код можно запускать повторно без пересборки Docker-образа.
