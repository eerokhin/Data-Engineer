## Apache Iceberg

Apache Iceberg — табличный формат для `Data Lake`.

Он добавляет поверх файлового хранилища (`S3/HDFS`):

- `Schema` — структуру таблицы
- `Partitioning` — разбиение данных
- `Transactions` — безопасные изменения
- `Snapshots` — версии состояния таблицы
- `Time Travel` — просмотр данных в прошлом
- `Rollback` — откат к предыдущему состоянию
- `Schema Evolution` — изменение схемы без полной пересборки

Важно: `Iceberg ≠ база данных`.

Данные физически хранятся в `Object Storage` (`S3`, `MinIO` и т.д.), например в `Parquet`.

Iceberg управляет тем, как эти файлы объединяются в логическую таблицу.

## Iceberg Architecture

Iceberg превращает набор файлов в `S3/HDFS` в полноценную таблицу с метаданными, транзакциями и историей изменений.

### Основные уровни

```
Catalog
↓
Metadata File
↓
Snapshot
↓
Manifest List
↓
Manifest
↓
Data Files
```

<img width="1163" height="632" alt="image" src="https://github.com/user-attachments/assets/d905cf10-e1a2-48f7-a8e4-15d7e4ae79a7" />


### Data Files

Внизу находятся реальные данные. Физические данные таблицы.

Обычно используются:
- Parquet
- ORC
- Avro

Например:

```text
warehouse/orders/
├── data-001.parquet
├── data-002.parquet
└── data-003.parquet
```

Файлы не изменяются после записи. Если нужно обновить данные, Iceberg создаёт новые файлы.

### Manifest

Manifest хранит информацию о файлах данных. Описывает Data Files:

- какие файлы входят в таблицу;
- количество строк;
- информацию о partition;
- статистику min/max и т.д.

```text
manifest
 ├── data-001.parquet
 ├── data-002.parquet
 └── data-003.parquet
```

Благодаря этому Iceberg может не читать ненужные Parquet-файлы.

Например: `WHERE order_date = '2025-01-15'`. Iceberg по metadata может понять:

```text
file-001 → январь ❌
file-002 → январь ✅
file-003 → март ❌
```

и прочитать только `file-002`.

### Manifest List

Следующий уровень. Содержит список Manifest Files, относящихся к конкретному Snapshot.

```text
Manifest List
     │
     ├── manifest-001
     ├── manifest-002
     └── manifest-003
```

Он уже организует манифесты и содержит агрегированную информацию о них. Это позволяет ещё раньше отбрасывать ненужные данные.

### Metadata File

Это главный файл таблицы. Описывает состояние Iceberg-таблицы. Он содержит:

```text
Metadata
├── schema
├── partitioning
├── table properties
└── snapshots
```

Самое важное здесь — snapshots. Snapshot = состояние таблицы в конкретный момент времени.

### Snapshot

Snapshot — это состояние таблицы в определённый момент времени.

Например:

```text
Snapshot 1 → первая загрузка
Snapshot 2 → после INSERT
Snapshot 3 → после UPDATE
Snapshot 4 → после DELETE
```
Каждый snapshot указывает на соответствующий Manifest List.

Благодаря snapshots работают:

- Time Travel
- Rollback

### Catalog

Catalog хранит информацию о том, где находится актуальный Metadata File таблицы.

Catalog нужен для того, чтобы по имени `orders` понять где находится актуальный Metadata File этой таблицы?

Например:

```text
orders
↓
s3://warehouse/orders/metadata/....metadata.json
```

Catalog ≠ Metadata.

Catalog указывает, где находится Metadata, а Metadata описывает саму Iceberg-таблицу и её snapshots. То есть Catalog — это указатель на актуальное состояние таблицы.

### Как происходит INSERT

Допустим делаем: `INSERT INTO orders VALUES (...);`

Iceberg примерно делает:

```text
1. Создаёт новые Parquet
             ↓
2. Создаёт новый Manifest
             ↓
3. Создаёт новый Manifest List
             ↓
4. Создаёт новый Metadata File
             ↓
5. Появляется новый Snapshot
```

При этом старые Data Files не удаляются и не изменяются. И именно это позволяет делать: Time Travel, Rollback

### Главное

Iceberg не является базой данных.

Данные физически хранятся в Object Storage (S3, MinIO и т.д.), обычно в Parquet.

Iceberg добавляет над файлами слой метаданных, snapshots и управление таблицей.

Вся архитектура в одной картинке

```text
        CATALOG
           │
     "где таблица?"
           │
           ▼
  Metadata File
           │
     "какой snapshot?"
           │
           ▼
  Manifest List
           │
     "какие manifests?"
           │
           ▼
   Manifest Files
           │
     "какие data files?"
           │
           ▼
    Data Files
  Parquet / ORC
           │
           ▼
      MinIO / S3
```
