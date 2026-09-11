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

<img width="864" height="210" alt="image" src="https://github.com/user-attachments/assets/21760cc3-f69a-4543-a1e3-b57cb5384e49" />

Несколько важных моментов:

- `USING iceberg` указывает `Spark`, что это таблица `Iceberg`
- Мы храним данные в файлах `Parquet` (по умолчанию, но лучше быть явным)
- `format-version='2'` включает операции на уровне строк `(UPDATE, DELETE, MERGE)`
- Пока без партицирования — мы рассмотрим это в следующем упражнении

Проверить, что таблица создана:

```sql
DESCRIBE orders;
```
Должны увидеть что-то вроде:

<img width="411" height="149" alt="image" src="https://github.com/user-attachments/assets/56787061-dff3-46b7-80ec-a4bfedb26f69" />

### Шаг 5: Вставка данных

Добавим несколько заказов. Ничего сложного — просто обычные `INSERT`-запросы:

```sql
INSERT INTO orders VALUES
    (1001, 42, CAST('2024-01-15' AS DATE), 299.99, 'completed'),
    (1002, 17, CAST('2024-01-15' AS DATE), 149.50, 'completed'),
    (1003, 42, CAST('2024-01-16' AS DATE), 89.00, 'pending');
```

Добавим ещё парочку:

```sql
INSERT INTO orders VALUES
    (1004, 88, CAST('2024-01-16' AS DATE), 1250.00, 'completed'),
    (1005, 17, CAST('2024-01-17' AS DATE), 45.00, 'cancelled');
```

*Фотографии таблицы: Каждый `INSERT` создаёт новый снапшот. Представьте, что вы фотографируете таблицу после каждого изменения. Эти «фотографии» позволяют потом путешествовать во времени, но об этом позже.*

<img width="816" height="208" alt="image" src="https://github.com/user-attachments/assets/7f387087-56c6-4bd2-8b6f-ee6b24c9e868" />

### Шаг 6: Запрос данных

Убедимся, что всё корректно записалось:

```sql
SELECT * FROM orders ORDER BY order_id;
```

Должны увидеть все пять заказов:

<img width="650" height="150" alt="image" src="https://github.com/user-attachments/assets/b049e88e-812b-487c-9387-bd32d774cfab" />

Попробуйте более интересный запрос — общая выручка по клиентам:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS total_spent
FROM orders
WHERE status = 'completed'
GROUP BY customer_id
ORDER BY total_spent DESC;
```

Должны получить такой результат:

<img width="540" height="243" alt="image" src="https://github.com/user-attachments/assets/34b31580-3bac-4e65-a8df-ed295c1955d9" />

### Шаг 7: Заглянем под капот

Вот где Iceberg становится по-настоящему интересным. Давайте посмотрим на созданные снапшоты, запросив метатаблицу снапшотов:

```sql
SELECT
    snapshot_id,
    committed_at,
    operation
FROM demo.ecommerce.orders.snapshots
ORDER BY committed_at;
```

Вот что я получил:

<img width="567" height="189" alt="image" src="https://github.com/user-attachments/assets/470e9e88-b5e1-428c-9fcb-d77062f9d807" />
