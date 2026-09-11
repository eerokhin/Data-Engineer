## Apache Iceberg. Упражнение 1: Первая таблица

### Обзор

В этом упражнении развернём локальное окружение Iceberg, создадим свою первую таблицу и вставим данные.

### Цели обучения

К концу этого упражнения сможем:

- Запустить локальное окружение Iceberg со Spark, REST-каталогом и объектным хранилищем
- Создать пространство имён и таблицу с помощью Spark SQL
- Вставить данные и убедиться, что они корректно записались
- Изучить снапшоты и метаданные таблицы

### Предварительные требования

- Docker и Docker Compose установлены
- Терминал
- Около 15 минут свободного времени

### Шаг 1: Запуск окружения

Сначала создать директорию, например `iceberg-course-exercises`.

Открыть терминал в этой директории и создайте файл `docker-compose.yaml` со следующим содержимым. Эта конфигурация идентична официальному примеру с сайта `Apache Iceberg`:

```python
services:
  spark-iceberg:
    image: tabulario/spark-iceberg
    container_name: spark-iceberg
    build: spark/
    networks:
      iceberg_net:
    depends_on:
      - rest
      - minio
    volumes:
      - ./warehouse:/home/iceberg/warehouse
      - ./notebooks:/home/iceberg/notebooks/notebooks
    environment:
      - AWS_ACCESS_KEY_ID=admin
      - AWS_SECRET_ACCESS_KEY=password
      - AWS_REGION=us-east-1
    ports:
      - 8888:8888
      - 8080:8080
      - 10000:10000
      - 10001:10001
  rest:
    image: apache/iceberg-rest-fixture:1.10.1
    container_name: iceberg-rest
    networks:
      iceberg_net:
    ports:
      - 8181:8181
    environment:
      - AWS_ACCESS_KEY_ID=admin
      - AWS_SECRET_ACCESS_KEY=password
      - AWS_REGION=us-east-1
      - CATALOG_WAREHOUSE=s3://warehouse/
      - CATALOG_IO__IMPL=org.apache.iceberg.aws.s3.S3FileIO
      - CATALOG_S3_ENDPOINT=http://minio:9000
  minio:
    image: minio/minio
    container_name: minio
    environment:
      - MINIO_ROOT_USER=admin
      - MINIO_ROOT_PASSWORD=password
      - MINIO_DOMAIN=minio
    networks:
      iceberg_net:
        aliases:
          - warehouse.minio
    ports:
      - 9001:9001
      - 9000:9000
    command: ["server", "/data", "--console-address", ":9001"]
  mc:
    depends_on:
      - minio
    image: minio/mc
    container_name: mc
    networks:
      iceberg_net:
    environment:
      - AWS_ACCESS_KEY_ID=admin
      - AWS_SECRET_ACCESS_KEY=password
      - AWS_REGION=us-east-1
    entrypoint: |
      /bin/sh -c "
      until (/usr/bin/mc alias set minio http://minio:9000 admin password) do echo '...waiting...' && sleep 1; done;
      /usr/bin/mc rm -r --force minio/warehouse;
      /usr/bin/mc mb minio/warehouse;
      /usr/bin/mc policy set public minio/warehouse;
      tail -f /dev/null
      "
networks:
  iceberg_net:
```

*Микросервисный зоопарк: Обратите внимание, что у нас здесь целый зоопарк контейнеров — Spark для вычислений, REST-сервис для каталога, MinIO для хранения и даже утилита mc для настройки. Как дирижёр оркестра, Docker Compose управляет этим ансамблем.*

Далее создать файл `spark-defaults.conf` в той же директории со следующим содержимым:

```python
# S3 Support via Maven packages
spark.jars.packages                    org.apache.hadoop:hadoop-aws:3.3.4

# Hadoop S3A Configuration for MinIO
spark.hadoop.fs.s3a.endpoint           http://minio:9000
spark.hadoop.fs.s3a.access.key         admin
spark.hadoop.fs.s3a.secret.key         password
spark.hadoop.fs.s3a.path.style.access  true
spark.hadoop.fs.s3a.impl               org.apache.hadoop.fs.s3a.S3AFileSystem
spark.hadoop.fs.s3.impl                org.apache.hadoop.fs.s3a.S3AFileSystem
spark.hadoop.fs.s3a.connection.ssl.enabled false
```

Теперь запустите всё:

```
docker compose up -d
```

<img width="1088" height="424" alt="image" src="https://github.com/user-attachments/assets/0c1ce381-3568-4231-8646-7a0a18ff4c30" />


Подождать около 30 секунд, пока все сервисы инициализируются. Можно проверить, что всё работает:

```
docker compose ps
```

Должны увидеть четыре запущенных контейнера: `iceberg-rest`, `minio`, `mc` и `spark-iceberg`.

<img width="1905" height="138" alt="image" src="https://github.com/user-attachments/assets/f6bc40b3-e277-4c82-b9aa-cc81a5b5ae21" />

### Шаг 2: Подключение к Spark SQL

Открыть сессию `Spark SQL`:

```
docker compose exec -it spark-iceberg spark-sql --conf "spark.hadoop.hive.cli.print.header=true"
```

Должны увидеть приглашение `spark-sql>`. Проверим, что наш каталог `Iceberg` доступен:

```
SHOW CATALOGS;
```

<img width="1412" height="154" alt="image" src="https://github.com/user-attachments/assets/48601329-f9c7-42d4-b673-49c640447249" />

Должны увидеть `demo` в списке. Для этого упражнения мы будем использовать настроенный `REST-каталог Iceberg`, к которому Spark обращается напрямую.

<img width="395" height="92" alt="image" src="https://github.com/user-attachments/assets/16760182-7c6b-47da-9a26-e8cf1cc1c5e0" />

### Шаг 3: Создание базы данных

В Iceberg таблицы живут внутри пространств имён (`namespaces`). Создадим одно для наших `e-commerce` данных:

```
CREATE NAMESPACE demo.ecommerce;
```

Проверить, что оно существует:

```
SHOW NAMESPACES;
```

Должны увидеть `ecommerce` в выводе.

<img width="435" height="137" alt="image" src="https://github.com/user-attachments/assets/b419ae35-da0d-4bdc-8e90-dde111055a73" />

Теперь установим его как текущую базу данных:

```
USE demo.ecommerce;
```

<img width="358" height="57" alt="image" src="https://github.com/user-attachments/assets/cdb8c15e-de90-4d01-83a1-c81035a6991e" />

### Шаг 4: Создание таблицы Orders

Теперь главное событие. Мы создадим простую таблицу заказов:

```sql
CREATE TABLE orders (
    order_id BIGINT,
    customer_id BIGINT,
    order_date DATE,
    total_amount DECIMAL(10, 2),
    status STRING
)
USING iceberg
TBLPROPERTIES ('format-version'='2', 'write.format.default'='parquet');
```
