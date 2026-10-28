# Локальная Data Engineering-инфраструктура

## 1. Описание проекта

Локальная инфраструктура для разработки и тестирования ETL/ELT-процессов на Windows с использованием Docker.

### Компоненты

| Компонент | Назначение | Версия / образ |
|---|---|---|
| Docker Desktop | Запуск контейнеров | Docker Engine 28.4.0, Compose v2.39.2 |
| Apache Airflow | Оркестрация ETL-процессов | 2.10.5 |
| Apache Impala | SQL-обработка аналитических данных | 4.5.3 |
| PostgreSQL | Реляционная БД для учебных задач | PostgreSQL 13 |
| PostgreSQL (Airflow) | Метаданные Airflow | PostgreSQL 13 |
| MinIO | S3-совместимое объектное хранилище | Образ из Compose |
| Redis | Брокер сообщений для CeleryExecutor | Образ из Compose |
| DBeaver | SQL-клиент для работы с Impala | Локальное приложение |

### Архитектура

```text
Windows
│
└── Docker Desktop (WSL 2)
    │
    ├── Airflow
    │   ├── Webserver
    │   ├── Scheduler
    │   ├── Worker
    │   ├── Triggerer
    │   ├── PostgreSQL (metadata)
    │   └── Redis
    │
    ├── PostgreSQL DWH
    │
    ├── MinIO (S3 API)
    │
    └── Apache Impala 4.5.3
        ├── Hive Metastore
        ├── Statestore
        ├── Catalogd
        └── Impalad
```

Airflow запускает задачи, Python/PySpark обрабатывает данные, Impala выполняет SQL-запросы, PostgreSQL хранит реляционные данные, а MinIO позволяет работать с объектным хранилищем по S3 API.

> Важно: перечисленные компоненты запущены локально, но полноценный ETL-конвейер между ними необходимо реализовывать отдельно.

---

## 2. Требования к компьютеру

Проверенная конфигурация:

- Windows 10/11.
- Docker Desktop.
- WSL 2.
- Архитектура x86_64.
- 16 ГБ оперативной памяти.
- Около 50 ГБ свободного места на диске.

Ресурсы Docker Desktop должны позволять одновременно запускать Airflow, PostgreSQL, MinIO и Impala.

## 3. Установка Docker Desktop

1. Установить Docker Desktop для Windows.
2. Включить использование WSL 2.
3. Запустить Docker Desktop и дождаться готовности Docker Engine.
4. Открыть CMD и проверить:

```bat
docker --version
docker compose version
docker run --rm hello-world
```

Последняя команда должна завершиться сообщением об успешном запуске тестового контейнера.

---

## 4. Развёртывание Apache Impala

### 4.1. Получение исходных файлов

Открыть CMD:

```bat
cd /d C:\
mkdir projects
cd projects
```

Клонировать официальный репозиторий Apache Impala с частичной загрузкой:

```bat
git clone --depth 1 --filter=blob:none --sparse https://github.com/apache/impala.git impala-docker
cd impala-docker
git sparse-checkout set --skip-checks docker/quickstart.yml docker/quickstart_conf
```

Используется официальный репозиторий: https://github.com/apache/impala

Файл Compose:

```text
C:\projects\impala-docker\docker\quickstart.yml
```

**Примечание:** это sparse checkout, а не полный клон репозитория. Если структура quickstart изменится в будущей версии репозитория, команды потребуется сверить с актуальной документацией.

### 4.2. Переменные окружения

В том же окне CMD выполнить:

```bat
set IMPALA_QUICKSTART_IMAGE_PREFIX=apache/impala:4.5.3-
set QUICKSTART_LISTEN_ADDR=0.0.0.0
```

Первая переменная задаёт префикс образов Impala 4.5.3. Вторая позволяет публиковать сервисы на сетевых интерфейсах контейнера.

Переменные `set` действуют только в текущем окне CMD. После его закрытия их необходимо задать снова.

### 4.3. Запуск Impala

```bat
cd /d C:\projects\impala-docker
docker compose -f docker\quickstart.yml up -d
```

Проверить состояние контейнеров:

```bat
docker compose -f docker\quickstart.yml ps
```

Ожидаемые сервисы:

- Hive Metastore (`quickstart-hive-metastore`).
- Statestore (`docker-statestored-1`).
- Catalogd (`docker-catalogd-1`).
- Impalad (`docker-impalad-1-1`).

Первый запуск может занять больше времени из-за загрузки Docker-образов и инициализации сервисов.

### 4.4. Проверка Impala

Веб-интерфейс:

http://localhost:25000

Проверить SQL-запрос можно из клиентского контейнера:

```bat
docker run --rm --network quickstart-network apache/impala:4.5.3-impala_quickstart_client impala-shell -i impalad-1:21050 -q "SELECT 1;"
```

Ожидаемый результат — запрос выполнен, возвращено значение `1`.

### 4.5. Основные порты

| Порт | Назначение |
|---|---|
| 21000 | Beeswax |
| 21050 | HiveServer2 / JDBC |
| 25000 | Impalad Web UI |
| 25010 | Catalogd Web UI |
| 25020 | Statestore Web UI |
| 28000 | Дополнительный служебный порт quickstart |

Для подключения через DBeaver используется порт **21050**, а не 21000.

---

## 5. Подключение DBeaver к Impala

Создать новое соединение через драйвер Apache Impala / Cloudera Impala JDBC.

Параметры подключения:

| Поле | Значение |
|---|---|
| Host | `localhost` |
| Port | `21050` |
| Database | `default` |
| Authentication | No Authentication |
| Driver class | `com.cloudera.impala.jdbc.Driver` |

<img width="885" height="698" alt="image" src="https://github.com/user-attachments/assets/e6ff0767-d560-4b38-9918-903b769553e1" />

Добавить джарник

<img width="825" height="419" alt="image" src="https://github.com/user-attachments/assets/933f6cfa-325e-41e7-9db3-6cf99e710eeb" />

В текущей рабочей конфигурации использовался JDBC-драйвер Cloudera Impala 2.6.42.1076.

После настройки выполнить:

```sql
SHOW DATABASES;
```

Создать учебную базу:

```sql
CREATE DATABASE IF NOT EXISTS sandbox;
```

Проверить:

```sql
SHOW DATABASES;
SHOW TABLES IN sandbox;
```

В списке баз должна присутствовать `sandbox`.

---

## 6. Развёртывание Airflow, PostgreSQL и MinIO

### 6.1. Папка проекта

Существующий проект находится здесь:

```text
C:\Users\erohi\Desktop\de_infra
```

В проекте уже есть:

```text
de_infra/
├── docker-compose.yaml
├── dags/
│   └── ees_input_contact_interact/
├── logs/
├── config/
└── plugins/
```

Перед повторным развёртыванием сохранить существующие `docker-compose.yaml`, DAG-файлы и другие необходимые конфигурации в GitHub или другом надёжном месте.

### 6.2. Docker Compose

В существующем `docker-compose.yaml` используются:

- Airflow 2.10.5.
- `CeleryExecutor`.
- PostgreSQL 13 для метаданных Airflow.
- Redis.
- PostgreSQL DWH (`postgres_dwh`).
- MinIO.
- Webserver, Scheduler, Worker, Triggerer.

В Compose опубликован веб-интерфейс Airflow на порту 8080.

### 6.3. Сборка собственного образа Airflow

В корне `de_infra` необходим файл `Dockerfile`:

```dockerfile
FROM apache/airflow:2.10.5

USER airflow

RUN pip install --no-cache-dir "impyla==0.22.0"
```

Он устанавливает библиотеку `impyla`, чтобы Python-код в Airflow мог подключаться к Impala через HiveServer2.

В секции `x-airflow-common` файла `docker-compose.yaml`:

```yaml
image: airflow-impala:2.10.5
build: .
```

Эта настройка заменяет стандартный образ Airflow собственным образом с библиотекой `impyla`.

### 6.4. Подключение Airflow к сети Impala

Compose Impala использует внешнюю Docker-сеть:

```text
quickstart-network
```

Она должна существовать до запуска Airflow.

В секции `x-airflow-common` необходимо указать:

```yaml
networks:
  - default
  - quickstart-network
```

В конце `docker-compose.yaml` добавить конфигурацию внешней сети, если её ещё нет:

```yaml
networks:
  quickstart-network:
    external: true
    name: quickstart-network
```

Airflow подключается к Impala по имени контейнера и внутреннему порту:

```text
impalad-1:21050
```

При этом PostgreSQL и Redis продолжают работать во внутренней сети Airflow.

### 6.5. Проверка конфигурации и запуск

Открыть CMD:

```bat
cd /d C:\Users\erohi\Desktop\de_infra
docker compose config
```

Если конфигурация корректна, собрать образ:

```bat
docker compose build
```

Запустить сервисы:

```bat
docker compose up -d
```

Проверить состояние:

```bat
docker compose ps
```

Веб-интерфейс Airflow:

http://localhost:8080

Учётные данные зависят от текущей конфигурации Compose. Для стандартного учебного Compose обычно используются `airflow` / `airflow`, если они не изменены.

### 6.6. Предупреждение AIRFLOW_UID

Если Docker Compose выводит:

```text
The "AIRFLOW_UID" variable is not set.
Defaulting to a blank string.
```

это предупреждение об отсутствующей переменной окружения. Оно не обязательно препятствует запуску, но для корректных прав доступа к файлам проекта на Linux/WSL стоит проверить инструкцию по настройке `AIRFLOW_UID` в исходном Compose.

---

## 7. Проверка соединения Airflow → Impala

После запуска Airflow выполнить в CMD:

```bat
cd /d C:\Users\erohi\Desktop\de_infra
docker compose exec airflow-scheduler python -c "from impala.dbapi import connect; c=connect(host='impalad-1', port=21050, auth_mechanism='NOSASL'); cur=c.cursor(); cur.execute('SELECT 1'); print(cur.fetchall()); c.close()"
```

Ожидаемый результат:

```text
[(1,)]
```

Это подтверждает, что:

1. В контейнере Scheduler доступна библиотека `impyla`.
2. Airflow-контейнер видит сеть Impala.
3. Подключение к HiveServer2 работает.
4. SQL-запрос успешно выполняется.

Важно использовать один объект курсора для `execute()` и `fetchall()`.

---

## 8. Запуск и остановка инфраструктуры

### Запуск Impala

```bat
cd /d C:\projects\impala-docker
set IMPALA_QUICKSTART_IMAGE_PREFIX=apache/impala:4.5.3-
set QUICKSTART_LISTEN_ADDR=0.0.0.0
docker compose -f docker\quickstart.yml start
```

### Запуск Airflow и остальных сервисов

```bat
cd /d C:\Users\erohi\Desktop\de_infra
docker compose start
```

### Остановка Airflow

```bat
cd /d C:\Users\erohi\Desktop\de_infra
docker compose stop
```

### Остановка Impala

```bat
cd /d C:\projects\impala-docker
set IMPALA_QUICKSTART_IMAGE_PREFIX=apache/impala:4.5.3-
set QUICKSTART_LISTEN_ADDR=0.0.0.0
docker compose -f docker\quickstart.yml stop
```

`stop` останавливает контейнеры, но не удаляет их. При повторном запуске `start` использует существующие контейнеры.

**Не выполнять `docker compose down -v`, если необходимо сохранить данные в Docker volumes.**

---

## 9. Важные правила хранения данных

Docker volumes и bind mounts — разные механизмы хранения.

- PostgreSQL хранит данные в томах или каталогах, заданных в Compose.
- DAG-файлы Airflow находятся в папке `dags`, подключённой с хоста.
- Логи Airflow сохраняются в `logs`.
- Данные MinIO зависят от настроенного тома или каталога.
- Таблицы Impala используют настроенные источники и хранилище метаданных.

Для настоящего развёртывания с нуля необходимо сохранить не только этот документ, но и все собственные файлы проекта.

GitHub не должен содержать пароли, токены, секретные ключи и другие чувствительные данные. Перед публикацией проверить Compose, конфигурационные файлы и переменные окружения.

---

## 10. Контрольный список после восстановления

- [ ] Docker Desktop запущен.
- [ ] WSL 2 работает.
- [ ] Репозиторий Impala получен.
- [ ] Impala-контейнеры запущены.
- [ ] Impala Web UI открывается на `localhost:25000`.
- [ ] DBeaver подключается к `localhost:21050`.
- [ ] База `sandbox` существует.
- [ ] Airflow собран с `impyla`.
- [ ] Airflow подключён к `quickstart-network`.
- [ ] PostgreSQL, Redis и MinIO запущены.
- [ ] Airflow Web UI открывается на `localhost:8080`.
- [ ] Тест `SELECT 1` из Scheduler возвращает `[(1,)]`.
- [ ] DAG-файлы доступны в интерфейсе Airflow.

## 11. Полезные ссылки

- Apache Impala: https://github.com/apache/impala
- Apache Airflow: https://airflow.apache.org/docs/
- Docker Compose: https://docs.docker.com/compose/
- MinIO: https://min.io/docs/
- DBeaver: https://dbeaver.io/

## 12. Добавление почты, для рассылки уведомлений от Airflow

**1. Проверить настройки Яндекса**

1. Открой Яндекс ID.
2. Перейди в раздел безопасности и проверь, создан ли пароль приложения для почтового клиента.
3. Если не уверен, создай новый пароль приложения для почты. Используй именно его, а не обычный пароль от аккаунта.

**2. Проверь .env**

В `C:\Users\erohi\Desktop\de_infra\.env` должны быть такие переменные:

```
YANDEX_EMAIL=твой_полный_адрес@yandex.ru
YANDEX_APP_PASSWORD=пароль_приложения
ALERT_EMAIL=твой_полный_адрес@yandex.ru
```

Проверь следующее:

- YANDEX_EMAIL — полный адрес почтового ящика, от имени которого отправляешь письма.
- YANDEX_APP_PASSWORD — пароль приложения, скопированный из Яндекс ID.
- Вокруг значений не нужны кавычки.
- Не добавляй пробелы до или после =.
- Если используешь собственный домен или почту организации, уточни, поддерживает ли этот ящик SMTP и разрешена ли отправка через smtp.yandex.ru.

**3. Включи доступ к почтовым программам**

Это важный шаг, который легко пропустить. В настройках Яндекс Почты:

1. Открой Яндекс Почту.
2. Перейди в Настройки → Все настройки → Почтовые программы.
3. Включи доступ к почте через почтовые клиенты по протоколу IMAP и опцию «Пароли приложений и OAuth-токены».
4. Сохрани изменения.

Яндекс указывает эти разрешения и для сценария, когда почтовая программа используется только для отправки писем по SMTP.

**4. Не забыть добавить файл .env в .gitignore**

**5. Тесты**

DAG для проверки работоспособности

```python
from datetime import datetime
import os

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.email import send_email


def send_test_email():
    recipient = os.getenv("ALERT_EMAIL")

    if not recipient:
        raise RuntimeError("Переменная ALERT_EMAIL не задана")

    send_email(
        to=recipient,
        subject="[Airflow] Yandex SMTP test",
        html_content="""
        <h2>SMTP работает</h2>
        <p>Тестовое письмо успешно отправлено из Apache Airflow.</p>
        <p>Проект: hr_etl_monitoring</p>
        """,
    )

    print(f"Тестовое письмо отправлено на {recipient}")


with DAG(
    dag_id="test_yandex_email",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["test", "email"],
) as dag:
    send_test_email_task = PythonOperator(
        task_id="send_test_email",
        python_callable=send_test_email,
    )
```

Проверить почтовый ящик

<img width="912" height="274" alt="image" src="https://github.com/user-attachments/assets/63a4da80-eb51-4a4d-ac76-e058eb52fe03" />
