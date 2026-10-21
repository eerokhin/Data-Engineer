# Apache Spark + Docker + Jupyter

Учебный проект для запуска локального Spark-кластера из одного Master и двух Worker с возможностью выполнять PySpark-код в Jupyter Notebook.

## 1. Архитектура

```text
Jupyter Notebook
      |
      | PySpark
      v
Spark Master :7077
      |
      +------------------+
      |                  |
      v                  v
Spark Worker 1      Spark Worker 2
  2 cores             2 cores
  2 GB                2 GB
```

**Компоненты:**
- **Spark Master** — управляет ресурсами кластера.
- **Spark Worker** — предоставляет ресурсы для выполнения задач.
- **JupyterLab** — среда для написания и выполнения Python-кода.
- **PySpark** — Python API для работы с Apache Spark.
- **Docker Compose** — запускает и связывает контейнеры.

## 2. Структура проекта

```text
spark-learning/
├── compose.yaml
├── jupyter/
│   └── Dockerfile
├── notebooks/
│   └── Spark_Training.ipynb
└── data/
```

- `compose.yaml` — описание сервисов и сети.
- `jupyter/Dockerfile` — сборка окружения Jupyter.
- `notebooks/` — ноутбуки с учебными задачами.
- `data/` — файлы для обработки.

## 3. Что установить

Перед началом установи:
- Docker Desktop;
- Git — если планируешь хранить проект в GitHub.

В Docker Desktop дождись запуска Docker Engine.

## 4. Сборка и запуск с нуля

Открой терминал Windows и перейди в папку проекта:

```powershell
cd C:\Users\erohi\Desktop\spark-learning
```

Собери образ Jupyter:

```bash
docker compose build
```

Запусти все контейнеры:

```bash
docker compose up -d
```

Проверь состояние:

```bash
docker compose ps
```

Ожидается четыре контейнера:
- `spark-master`;
- `spark-worker`;
- `spark-worker-2`;
- `spark-jupyter`.

### Веб-интерфейсы

| Сервис | Адрес |
|---|---|
| JupyterLab | http://localhost:8888 |
| Spark Master UI | http://localhost:8080 |
| Spark Worker 1 UI | http://localhost:8081 |
| Spark Worker 2 UI | http://localhost:8082 |
| Spark Application UI | http://localhost:4040 |

Application UI доступен, пока Spark-приложение активно и использует этот порт.

## 5. Подключение к Spark из Jupyter

Открой http://localhost:8888 и создай Python Notebook.

Если библиотека PySpark ещё не установлена, выполни в терминале:

```bash
docker compose exec spark-jupyter python3 -m pip install pyspark==4.0.1
```

Затем перезапусти ядро Jupyter через **Kernel → Restart Kernel**.

Создай Spark-сессию:

```python
import os
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("SparkLearning")
    .master(
        os.getenv(
            "SPARK_MASTER_URL",
            "spark://spark-master:7077"
        )
    )
    .config("spark.driver.host", "spark-jupyter")
    .config("spark.driver.bindAddress", "0.0.0.0")
    .config("spark.driver.port", "7078")
    .config("spark.blockManager.port", "7079")
    .getOrCreate()
)

print("Spark version:", spark.version)
print("Master:", spark.sparkContext.master)
print("Application ID:", spark.sparkContext.applicationId)
```

Ожидаемый результат:

```text
Spark version: 4.0.1
Master: spark://spark-master:7077
Application ID: app-...
```

## 6. Первая распределённая задача

Создадим RDD из миллиона чисел и разделим его на 16 партиций:

```python
sc = spark.sparkContext

rdd = sc.parallelize(
    range(1, 1_000_001),
    16
)

print("Partitions:", rdd.getNumPartitions())

result = rdd.map(lambda x: x * 2).sum()

print("Result:", result)
```

Результат:

```text
Partitions: 16
Result: 1000001000000
```

### Что здесь происходит

1. `parallelize()` создаёт RDD из коллекции Python.
2. `16` задаёт количество партиций.
3. `map()` умножает каждое число на два.
4. `sum()` запускает вычисление и возвращает сумму.
5. Spark распределяет задачи между доступными ресурсами Worker.

## 7. Как изучать выполнение задачи

Пока приложение активно, открой http://localhost:4040.

Основные вкладки:
- **Jobs** — задания Spark.
- **Stages** — стадии выполнения заданий.
- **Executors** — исполнители, которые обрабатывают задачи.

На странице http://localhost:8080 можно посмотреть зарегистрированные Worker, их ресурсы и запущенные приложения.

Если вкладки Jobs и Stages не отображаются, проверь, что открыл Application UI на порту `4040`, а не Master UI на порту `8080`.

## 8. Как завершить работу

### Остановить Spark-сессию

Выполни в Jupyter:

```python
spark.stop()
```

Это завершает Spark-сессию, но не останавливает все Docker-контейнеры.

### Остановить контейнеры

В терминале проекта:

```bash
docker compose down
```

Контейнеры будут остановлены и удалены. Образы и файлы в локальных каталогах проекта останутся.

### Запустить проект снова

```bash
docker compose up -d
```

Проверить состояние:

```bash
docker compose ps
```

Затем снова открой http://localhost:8888.

Если ядро Jupyter сохранилось, после запуска инфраструктуры создай Spark-сессию заново, выполнив соответствующую ячейку.

## 9. Полная пересборка

Если изменился `jupyter/Dockerfile` или нужно пересобрать образ:

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

Если PySpark устанавливался вручную внутри контейнера, после пересборки его может потребоваться установить снова. Чтобы библиотека устанавливалась автоматически при сборке, добавь её установку в `jupyter/Dockerfile`.

## 10. Полезные команды Docker

| Команда | Назначение |
|---|---|
| `docker compose up -d` | Запустить контейнеры |
| `docker compose down` | Остановить и удалить контейнеры |
| `docker compose ps` | Посмотреть состояние контейнеров |
| `docker compose logs -f` | Смотреть логи всех сервисов |
| `docker compose logs -f spark-master` | Смотреть логи Master |
| `docker compose logs -f spark-worker` | Смотреть логи первого Worker |
| `docker compose logs -f spark-jupyter` | Смотреть логи Jupyter |
| `docker compose restart` | Перезапустить сервисы |
| `docker compose build --no-cache` | Пересобрать образы без кеша |

## 11. Важные замечания

- Два Worker по 2 ядра предоставляют Spark суммарно 4 заявленных ядра. Это не означает, что все задачи всегда выполняются одновременно.
- Количество партиций не равно количеству Worker или исполнителей.
- Spark Application UI обычно доступен только во время работы приложения.
- Установка PySpark должна соответствовать версии Spark. В проекте используется Spark `4.0.1`.
- В текущем локальном учебном окружении авторизация Jupyter отключена. Не публикуй порт `8888` в интернет без настройки аутентификации и сетевой защиты.

## 12. Остановка и очистка

Обычная остановка:

```bash
docker compose down
```

Остановка с удалением неиспользуемых ресурсов не требуется для обычной работы. Не используй `docker system prune -a` без необходимости: команда может удалить другие образы и кеш Docker.

---

**Цель проекта:** освоить запуск Spark-кластера, подключение PySpark из Jupyter, распределённую обработку RDD и изучение выполнения задач через Spark Web UI.
