## Apache Iceberg. Упражнение: Обслуживание таблиц

**Обзор**

Вы создавали таблицы, меняли схемы, партицировали данные, путешествовали во времени по снапшотам и использовали теги и ветки. Всё прекрасно работает в разработке. Но что происходит после шести месяцев в продакшене?

Вот реальность: `streaming`‑задания, которые пишут каждую минуту, создают тысячи крошечных файлов. Каждая операция `UPDATE` и `DELETE` создаёт новые снапшоты. Старые файлы данных накапливаются, даже когда на них больше не ссылаются. Оставленные без контроля, ваши таблицы превращаются в беспорядок из мелких файлов, которые убивают производительность запросов и тратят хранилище.

Iceberg предоставляет несколько операций обслуживания, чтобы поддерживать таблицы здоровыми:

- Сжатие (`compaction`): объединение мелких файлов в более крупные
- Удаление старых снапшотов (`snapshot expiration`): удаление старых снапшотов, которые вам больше не нужны
- Очистка осиротевших файлов (`orphan file cleanup`): удаление файлов данных, на которые не ссылается ни один снапшот

В этом упражнении вы намеренно создадите фрагментированную таблицу, увидите влияние на производительность, а затем очистите её.

**Цели обучения**

К концу упражнения вы сможете:

- Определять фрагментацию файлов с помощью метатаблиц
- Понимать `delete`‑файлы и как Iceberg обрабатывает `DELETE`
- Сжать мелкие файлы и мержить `delete`‑файлы с помощью `optimize`
- Удалять старые снапшоты с помощью `expire_snapshots`
- Удалять осиротевшие файлы с помощью `remove_orphan_files`
- Понимать, когда и зачем запускать каждую операцию обслуживания

**Предварительные требования**

- Завершённое упражнение 5 (или запущенное окружение)
- Около 25 минут

## Шаг 1: Подготовка окружения

Запустите окружение, если оно ещё не запущено:

```
docker compose up -d
```

Запустите `Spark SQL` с дополнительными параметрами для доступа к данным напрямую из `S3`‑совместимой файловой системы (`MinIO`):

```
docker compose exec -it spark-iceberg spark-sql \
    --packages org.apache.hadoop:hadoop-aws:3.3.4 \
    --conf "spark.hadoop.hive.cli.print.header=true" \
    --conf "spark.hadoop.fs.s3a.endpoint=http://minio:9000" \
    --conf "spark.hadoop.fs.s3a.path.style.access=true" \
    --conf "spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem" \
    --conf "spark.hadoop.fs.s3.impl=org.apache.hadoop.fs.s3a.S3AFileSystem" \
    --conf "spark.hadoop.fs.s3a.connection.ssl.enabled=false"
```

Создайте свежую таблицу:

```sql
CREATE NAMESPACE IF NOT EXISTS demo.ecommerce;
USE demo.ecommerce;
 
DROP TABLE IF EXISTS events;
 
CREATE TABLE events (
    event_id BIGINT,
    user_id BIGINT,
    event_type STRING,
    event_time TIMESTAMP,
    properties STRING
)
USING iceberg
PARTITIONED BY (days(event_time))
TBLPROPERTIES (
    'format-version'='2',
    'write.format.default'='parquet',
    'write.update.mode'='copy-on-write',
    'write.delete.mode'='merge-on-read'
);
```

## Шаг 2: Создайте фрагментацию файлов

В продакшене фрагментация часто возникает из‑за `streaming‑ингestion` — маленькие батчи приходят часто. Давайте смоделируем это:

```sql
-- Батч 1
INSERT INTO events VALUES
    (1, 101, 'page_view', CAST('2025-01-15 10:00:00' AS TIMESTAMP), '{"page": "/home"}'),
    (2, 102, 'page_view', CAST('2025-01-15 10:01:00' AS TIMESTAMP), '{"page": "/products"}');
 
-- Батч 2
INSERT INTO events VALUES
    (3, 101, 'click', CAST('2025-01-15 10:02:00' AS TIMESTAMP), '{"button": "add_to_cart"}'),
    (4, 103, 'page_view', CAST('2025-01-15 10:03:00' AS TIMESTAMP), '{"page": "/checkout"}');
 
-- Батч 3
INSERT INTO events VALUES
    (5, 102, 'purchase', CAST('2025-01-15 10:05:00' AS TIMESTAMP), '{"amount": 99.99}'),
    (6, 101, 'page_view', CAST('2025-01-15 10:06:00' AS TIMESTAMP), '{"page": "/confirmation"}');
 
-- Батч 4
INSERT INTO events VALUES
    (7, 104, 'page_view', CAST('2025-01-15 10:10:00' AS TIMESTAMP), '{"page": "/home"}'),
    (8, 104, 'click', CAST('2025-01-15 10:11:00' AS TIMESTAMP), '{"button": "signup"}');
 
-- Батч 5
INSERT INTO events VALUES
    (9, 104, 'signup', CAST('2025-01-15 10:12:00' AS TIMESTAMP), '{"method": "email"}'),
    (10, 105, 'page_view', CAST('2025-01-15 10:15:00' AS TIMESTAMP), '{"page": "/products"}');
```

Это `10` строк, разбросанных по `5` `INSERT`‑запросам. Каждый `INSERT` создаёт новый файл данных.

## Шаг 3: Изучите фрагментацию

Давайте посмотрим на ущерб:

```sql
SELECT
    file_path,
    record_count,
    file_size_in_bytes
FROM demo.ecommerce.events.files;
```

<img width="895" height="373" alt="image" src="https://github.com/user-attachments/assets/0666b854-39c4-4944-910b-13e0a823a02b" />

Вы должны увидеть `5` файлов, каждый содержит только `2` записи. В реальной системе с миллионами строк у вас могут быть тысячи файлов с несколькими сотнями записей каждый. Это проблема, потому что:

- Накладные расходы на запросы: каждый файл требует поиска метаданных и операций ввода‑вывода
- Неэффективность хранилища: мелкие файлы плохо сжимаются и имеют высокие накладные расходы
- Время планирования: планировщик запросов должен обрабатывать метаданные каждого файла

Проверьте также снапшоты:

```sql
SELECT
    snapshot_id,
    committed_at,
    operation,
    summary['added-data-files'] AS files_added,
    summary['total-records'] AS total_records
FROM demo.ecommerce.events.snapshots
ORDER BY committed_at;
```

Вы должны увидеть что‑то вроде:

<img width="896" height="261" alt="image" src="https://github.com/user-attachments/assets/89fa4062-182e-4dd5-9d53-49b6acdb79d6" />

Пять снапшотов, по одному на `INSERT`.

## Шаг 4: Создайте историю снапшотов с обновлениями

Теперь выполним несколько `UPDATE`. В режиме `copy‑on‑write` каждый `UPDATE` читает файл, содержащий целевые строки, записывает новый файл с изменениями и создаёт новый снапшот, указывающий на новый файл:

```sql
-- Исправляем опечатку в типе события
UPDATE events
SET event_type = 'page_view'
WHERE event_id = 3;
 
-- Обновляем свойства
UPDATE events
SET properties = '{"page": "/home", "referrer": "google"}'
WHERE event_id = 1;
 
-- Помечаем событие как обработанное
UPDATE events
SET properties = '{"amount": 99.99, "processed": true}'
WHERE event_id = 5;
```

Проверьте историю снапшотов:

```sql
SELECT
    snapshot_id,
    committed_at,
    operation,
    summary['total-data-files'] AS data_files
FROM demo.ecommerce.events.snapshots
ORDER BY committed_at;
```

<img width="893" height="379" alt="image" src="https://github.com/user-attachments/assets/f7fbdab2-2a4b-4977-be1c-a201ad70b01a" />

Вы увидите 3 новых снапшота (по одному на UPDATE), всего 8 снапшотов. Каждая операция UPDATE заменила файл данных обновлённой версией. Текущий снапшот всё ещё показывает ~5 файлов данных, но старые версии этих файлов теперь осиротевшие (ссылаются только на предыдущие снапшоты).

## Шаг 5: Удаление файлов и позиционные удаления

Теперь посмотрим, что происходит при удалении строк. Iceberg использует `positional delete files` для отслеживания удалённых строк без перезаписи файлов данных:

```sql
-- Удаляем некоторые события
DELETE FROM events
WHERE event_id IN (7, 8);
 
-- Удаляем ещё одно событие
DELETE FROM events
WHERE event_id = 10;
```

Теперь изучите файлы и увидите появление `delete`‑файлов:

```sql
SELECT
    content,
    file_path,
    record_count,
    file_size_in_bytes
FROM demo.ecommerce.events.files
ORDER BY content, file_path;
```

<img width="902" height="603" alt="image" src="https://github.com/user-attachments/assets/cd4f9fb1-b305-4a87-b7ce-93d0b2f36e44" />

Посмотрите на колонку `content`:

- `0 = Data file` (содержит фактические строки)
- `1 = Positional delete file` (помечает строки как удалённые)

Вы должны увидеть новые файлы с `content = 1`. Это `delete`‑файлы, которые записывают, какие позиции (номера строк) в файлах данных были удалены.

Ключевое понимание: В режиме `merge‑on‑read Iceberg` не перезаписывает файлы данных сразу при удалении строк. Вместо этого он создаёт маленькие `delete`‑файлы, которые движки запросов должны читать и применять. Это эффективно для мелких удалений, но со временем накапливает накладные расходы.

Проверьте, сколько у нас `delete`‑файлов:

```sql
SELECT
    content,
    CASE content
        WHEN 0 THEN 'DATA'
        WHEN 1 THEN 'POSITION_DELETES'
        WHEN 2 THEN 'EQUALITY_DELETES'
    END AS file_type,
    COUNT(*) AS file_count,
    SUM(record_count) AS total_records
FROM demo.ecommerce.events.files
GROUP BY content
ORDER BY content;
```

Вы должны получить:

<img width="882" height="176" alt="image" src="https://github.com/user-attachments/assets/00dc886e-0403-43c2-83fa-dcc3e4872d5b" />

## Шаг 6: Сжатие файлов (compaction)

Время убираться. Нам нужно сжать файлы данных И применить `delete`‑файлы. Ключ — использовать правильные опции:

```sql
CALL system.rewrite_data_files(
    table => 'demo.ecommerce.events',
    options => map(
        'rewrite-all', 'true'
    )
);
```

Опция `'rewrite-all'` => `'true'` принудительно перезаписывает все файлы данных независимо от размера.

Вот результат, который вы должны увидеть:

<img width="879" height="122" alt="image" src="https://github.com/user-attachments/assets/debfb3d9-a402-41ac-ba25-d0c3ed5b9e49" />

Процедура `rewrite_data_files` применяет позиционные удаления, физически удаляя 3 удалённые строки.

Давайте проверим, что у нас после сжатия:

```sql
SELECT
    content,
    file_path,
    record_count,
    file_size_in_bytes
FROM demo.ecommerce.events.files;
```

```text
content| file_path| record_count| file_size_in_bytes 
0| s3://warehouse/ecommerce/events/data/event_time_day=2025-01-15/00000-51-0dd6c489-8b1f-40cd-a7dc-5407ced7608b-0-00001.parquet| 7| 2032 
1| s3://warehouse/ecommerce/events/data/event_time_day=2025-01-15/00000-40-6226306e-25f7-4be9-991b-007f0b577cf2-00001-deletes.parquet| 1| 1582 
1| s3://warehouse/ecommerce/events/data/event_time_day=2025-01-15/00000-38-70c50e32-7034-468d-a4af-73343d58bb46-00001-deletes.parquet| 2| 1631
```

Вы должны увидеть:

- 1 файл данных с 7 записями (сжатый файл с применёнными удалениями)
- 2 delete‑файла всё ещё видны (но они теперь осиротевшие)

Подождите, `delete`‑файлы всё ещё там? Да! Но обратите внимание: файл данных содержит только 7 строк. Удаления были физически применены во время сжатия. `Delete`‑файлы, которые вы видите, теперь осиротевшие — они ссылаются на старые файлы данных, которые были заменены. Не волнуйтесь, мы очистим их на следующих шагах.

Проверьте данные:

```sql
SELECT * FROM events ORDER BY event_id;
```

Вы должны увидеть 7 строк (10 исходных − 3 удалённых). Осиротевшие `delete`‑файлы не влияют на запросы — это просто остатки метаданных, которые скоро будут очищены.

## Шаг 7: Поймите накопление снапшотов

Сжатие помогло с файлами, но посмотрите на снапшоты:

```sql
SELECT
    snapshot_id,
    committed_at,
    operation
FROM demo.ecommerce.events.snapshots
ORDER BY committed_at;
```

Теперь у вас много снапшотов: `5 INSERT (append)`, `3 UPDATE (overwrite)`, `2 DELETE (overwrite)` и `1 сжатие (replace)`. В продакшене после месяцев операций у вас могут быть тысячи.

Помните: каждый снапшот не даёт удалять старые файлы данных (для `time travel`), но занимает место в метаданных и замедляет операции с метаданными.

## Шаг 8: Удаление старых снапшотов

Если вам не нужно путешествовать во времени к каждому состоянию, вы можете удалить старые снапшоты. Сначала проверьте метку времени последнего снапшота:

```sql
SELECT MAX(committed_at) FROM demo.ecommerce.events.snapshots;
```

Затем удалите все старые снапшоты, сохраняя только самый свежий:

```sql
CALL system.expire_snapshots(
    table => 'demo.ecommerce.events',
    older_than => TIMESTAMP '2026-01-09 12:00:00',  -- замените на максимальную метку времени из запроса выше
    retain_last => 1  -- Всегда сохранять как минимум столько снапшотов.
);
```

Параметр `older_than` говорит Iceberg удалить снапшоты, закоммиченные до этой метки времени, а `retain_last` гарантирует, что вы всегда сохраните как минимум 1 снапшот (даже если он старше метки). В продакшене вы бы вычисляли метку времени динамически (например, текущая дата минус 7 дней), чтобы сохранить неделю истории.

Эта процедура должна вернуть:

```
deleted_data_files_count	 deleted_position_delete_files_count	 deleted_equality_delete_files_count	 deleted_manifest_files_count	 deleted_manifest_lists_count	 deleted_statistics_files_count
8	                         0	                                   0	                                    11	                         10	                           0
```

Проверьте, что осталось:

```
SELECT
    snapshot_id,
    committed_at,
    operation
FROM demo.ecommerce.events.snapshots
ORDER BY committed_at;
```

Остался только самый свежий снапшот. Старые ушли.

Предупреждение: Как только снапшоты удалены, вы больше не можете путешествовать во времени к ним. Параметр `retain_last` защищает недавние снапшоты.

## Шаг 9: Удаление осиротевших файлов

Удаление снапшотов удаляет метаданные старых снапшотов, но фактические файлы данных, на которые они ссылались, всё ещё на диске. Теперь они осиротевшие — файлы, на которые не ссылается ни один снапшот.

Давайте проверим на осиротевшие файлы, сравнив файлы в хранилище с файлами в метаданных:

```sql
-- Файлы, на которые в данный момент ссылается таблица
SELECT COUNT(*) AS referenced_files
FROM demo.ecommerce.events.files;
```

```
referenced_files
3
```

Осиротевшие файлы всё ещё в `MinIO`, занимая место. Вы можете проверить это в другом терминале, выполнив:

```sql
docker compose exec minio mc ls /data/warehouse/ecommerce/events/data/event_time_day=2025-01-15
```

На моей машине я получил:

```
[2026-06-21 09:17:42 UTC] 4.0KiB 00000-38-70c50e32-7034-468d-a4af-73343d58bb46-00001-deletes.parquet/
[2026-06-21 09:17:43 UTC] 4.0KiB 00000-40-6226306e-25f7-4be9-991b-007f0b577cf2-00001-deletes.parquet/
[2026-06-21 09:20:28 UTC] 4.0KiB 00000-51-0dd6c489-8b1f-40cd-a7dc-5407ced7608b-0-00001.parquet/
```

Чтобы очистить их, мы бы обычно использовали:

```sql
CALL system.remove_orphan_files(
    table => 'demo.ecommerce.events',
    older_than => TIMESTAMP 'xxxx-xx-xx 00:00:00'  -- должно быть как минимум 24 часа назад
);
```

Теперь Iceberg по умолчанию осторожен. Процедура очистки требует минимальный 24‑часовой период ожидания перед фактическим удалением файлов. Это мера безопасности, чтобы убедиться, что мы случайно не выбросим данные, которые всё ещё могут читаться длительным запросом.

Если вы действительно хотите увидеть удаление файлов и не хотите ждать до завтра, есть обходной путь с использованием Action API напрямую, но это немного выходит за рамки этого упражнения (это включает запуск spark‑shell вместо spark‑sql с параметрами в начале упражнения).

А сейчас давайте сосредоточимся на тех двух висячих `delete`‑файлах, которые всё ещё болтаются в наших метаданных. Даже несмотря на то, что данные, на которые они указывали, исчезли после сжатия и удаления снапшотов, метаданные ещё этого не знают.

Чтобы привести всё в порядок, нам нужно перезаписать позиционные delete‑файлы:

```sql
CALL system.rewrite_position_delete_files(
    table => 'demo.ecommerce.events',
    options => map('rewrite-all', 'true')
);
```

Опция `'rewrite-all' => 'true'` заставляет процедуру обработать все `delete`‑файлы, включая висячие. Она должна вернуть:

<img width="887" height="83" alt="image" src="https://github.com/user-attachments/assets/684d694b-67af-4f25-85e3-656de53d6194" />

`2` висячих `delete`‑файла были консолидированы в ничто, поскольку они не ссылаются на существующие данные, эффективно удаляя их из метаданных.

## Шаг 10: Проверка очистки

Теперь давайте проверим, что всё чисто:

```sql
-- Должно быть 7 записей
SELECT COUNT(*) AS total_records
FROM demo.ecommerce.events;
 
-- Должен быть 1 файл данных (больше нет delete‑файлов!)
SELECT
    content,
    CASE content
        WHEN 0 THEN 'DATA'
        WHEN 1 THEN 'POSITION_DELETES'
        WHEN 2 THEN 'EQUALITY_DELETES'
    END AS file_type,
    COUNT(*) AS file_count
FROM demo.ecommerce.events.files
GROUP BY content
ORDER BY content;
 
-- Должно быть 2 снапшота типа "replace"
SELECT COUNT(*) AS snapshot_count
FROM demo.ecommerce.events.snapshots;
```

<img width="173" height="87" alt="image" src="https://github.com/user-attachments/assets/9dacb964-d312-410d-9925-fbd0f70f2c03" />

Отлично! Вы успешно завершили workflow обслуживания:

- Сжали 5 мелких файлов данных в 1 и применили удаления (осталось 7 строк)
- Удалили 11 старых снапшотов, сохранив только самый свежий
- Удалили 9 осиротевших файлов данных из хранилища
- Очистили 2 висячих `delete`‑файла из метаданных

Таблица теперь компактна и чиста!

## Шаг 11: Очистка

Выйдите из Spark SQL:

```
exit;
```

Если вы закончили:

```
docker compose down -v
```

## Что вы узнали

Вы увидели полную последовательность обслуживания:

- Сжатие файлов данных (применение удалений)
- Удаление старых снапшотов
- Удаление осиротевших файлов
- Перезапись позиционных `delete`‑файлов

*«Обслуживание таблиц Iceberg — это как уборка в data lake: если делать регулярно, вода остаётся чистой, а запросы — быстрыми. Если не делать — получается болото, где тонут даже самые оптимистичные запросы.»*
