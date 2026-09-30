## Apache Iceberg. Метатаблицы

Метатаблицы Iceberg — это как рентген для ваших данных: можно заглянуть внутрь, не вскрывая пациента. Только не удивляйтесь, если обнаружите, что некоторые файлы ведут себя странно — это нормально для данных, которые живут своей жизнью.

## Что такое метатаблицы и зачем они нужны

Метатаблицы Iceberg — это системные таблицы, которые дают вам доступ к внутреннему состоянию таблицы Iceberg через обычный `SQL`. Вместо того чтобы копаться в `JSON`-файлах метаданных или писать сложные скрипты, вы можете просто выполнить `SELECT` и увидеть, что происходит внутри таблицы.

```sql
-- Обычная таблица
SELECT * FROM sales;

-- Метаданные таблицы
SELECT * FROM sales.history;                              -- история изменений
SELECT * FROM sales.snapshots;                        -- информация о снэпшотах
SELECT * FROM sales.files;                                   -- файлы с данными
SELECT * FROM sales.manifests;                         -- файлы манифестов
SELECT * FROM sales.partitions;                         -- статистика партиций
SELECT * FROM sales.refs;                                   -- ветки и теги
SELECT * FROM sales.entries;                              -- изменения свойств
SELECT * FROM sales.metadata_log_entries;   -- изменения свойств
```

**Зачем это нужно?**

- Отладка производительности — понять, почему запросы стали медленнее
- Анализ файлов — увидеть распределение файлов по партициям, их размеры, количество
- Мониторинг здоровья — отслеживать рост таблицы, количество снапшотов, состояние манифестов
- Планирование обслуживания — определить, какие партиции нуждаются в компактификации

Метатаблицы доступны через синтаксис `table_name.metadata_table_name`. Например, если ваша таблица называется `orders`, то метатаблица снапшотов будет `orders.snapshots`. Рассмотрим на примере из прошлого упражнения.

## `snapshots` — снапшоты таблицы

Показывает все снапшоты таблицы: их `ID`, родительские снапшоты, временные метки и путь к файлу манифест-листа.

```sql
SELECT *
FROM finance.transactions.snapshots
ORDER BY committed_at DESC
LIMIT 1;
```

<img width="904" height="772" alt="image" src="https://github.com/user-attachments/assets/6f1b6b27-e4af-456a-a041-b6ac1f21a519" />

**Типичные случаи использования:**

- Просмотр истории изменений таблицы
- Понимание, какие операции (`append`, `replace`, `delete`) происходили
- Поиск конкретного снапшота для `time travel`

## `manifests` — манифесты

Даёт информацию о каждом файле манифеста: его путь, тип, количество добавленных и удалённых файлов, размер, время создания.

```sql
SELECT *
FROM finance.transactions.manifests
LIMIT 1;
```

<img width="848" height="575" alt="image" src="https://github.com/user-attachments/assets/c9662296-64a6-4318-a36e-5a75cb841a4c" />

**Типичные случаи использования:**

- Понимание распределения данных по манифестам
- Выявление манифестов с большим количеством мелких файлов
- Отслеживание эффективности компактификации

## `files` — файлы данных

Пожалуй, самая полезная метатаблица. Показывает детальную информацию о каждом файле данных: содержимое, партицию, размер, количество записей, форматы, статистику по колонкам.

```sql
SELECT *
FROM finance.transactions.files
LIMIT 1;
```

<img width="785" height="755" alt="image" src="https://github.com/user-attachments/assets/7004535f-d9d8-43fd-9e18-1e4494b037c6" />

<img width="586" height="779" alt="image" src="https://github.com/user-attachments/assets/d4002907-f968-46b2-a910-727c0c6f05ae" />

**Типичные случаи использования:**

- Анализ распределения размеров файлов
- Поиск слишком маленьких или слишком больших файлов
- Понимание, какие партиции содержат больше всего данных
- Отладка проблем с партицированием

## `partitions` — партиции

Показывает информацию о партициях таблицы: их спецификацию, количество файлов, записей, размер.

```sql
SELECT *
FROM finance.transactions.partitions
LIMIT 1;
```

<img width="840" height="439" alt="image" src="https://github.com/user-attachments/assets/525ea1f6-b151-4772-ac32-ddae3ade9ce5" />

**Типичные случаи использования:**

- Мониторинг роста партиций
- Выявление несбалансированных партиций
- Планирование обслуживания

## refs` — ссылки (ветки и теги)

Показывает все ветки и теги таблицы, их тип, связанный снапшот и максимальный возраст ссылки.

```sql
SELECT *
FROM finance.transactions.refs
LIMIT 1;
```

<img width="744" height="303" alt="image" src="https://github.com/user-attachments/assets/2a4b74c9-911c-4d94-a531-bd08a19d8b37" />

**Типичные случаи использования:**

- Просмотр всех веток и тегов таблицы
- Понимание, какие снапшоты защищены от удаления
- Отладка политик удержания

## `entries` — записи манифеста

Предоставляет детальную информацию на уровне отдельных записей в манифестах: статус (добавлен/удалён), данные файла, последовательный номер, номер снапшота.

```sql
SELECT *
FROM finance.transactions.entries
LIMIT 1;
```

```text
Поле	                          Значение
status	                        1
snapshot_id	                    3007366648374978862
sequence_number	                4
file_sequence_number            4
data_file	                      {
                                "content":0,
                                "file_path":"s3://warehouse/finance/transactions/data/00000-17-c6bbfe6a-aba4-4aac-8968-54cedc04f16c-0-00001.parquet",
                                "file_format":"PARQUET",
                                "spec_id":0,
                                "record_count":4,
                                "file_size_in_bytes":2196,
                                "column_sizes": {
                                    1:64,
                                    2:95,
                                    3:57,
                                    4:68,
                                    5:163,
                                    6:42
                                },
                                "value_counts": {
                                    1:4,
                                    2:4,
                                    3:4,
                                    4:4,
                                    5:4,
                                    6:4
                                },
                                "null_value_counts": {
                                    1:0,
                                    2:0,
                                    3:0,
                                    4:0,
                                    5:0,
                                    6:0
                                },
                                "nan_value_counts": { },
                                "lower_bounds": {
                                    1:�,
                                    2:d,
                                    3:�N,
                                    4:�,
                                    5:Депозит нового к,
                                    6:
                                },
                                "upper_bounds": {
                                    1:�,
                                    2:g,
                                    3:�N,
                                    4:�`,
                                    5:Получен возврат,
                                    6:
                                },
                                "key_metadata":null,
                                "split_offsets":[4],
                                "equality_ids":null,
                                "sort_order_id":0,
                                "referenced_data_file":null,
                                "content_offset":null,
                                "content_size_in_bytes":null
                            }
readable_metrics	          {
                              "account_id": {
                                  "column_size":95,
                                  "value_count":4,
                                  "null_value_count":0,
                                  "nan_value_count":null,
                                  "lower_bound":100,
                                  "upper_bound":103
                              },
                              "amount": {
                                  "column_size":68,
                                  "value_count":4,
                                  "null_value_count":0,
                                  "nan_value_count":null,
                                  "lower_bound":-750.00,
                                  "upper_bound":15000.00
                              },
                              "description": {
                                  "column_size":163,
                                  "value_count":4,
                                  "null_value_count":0,
                                  "nan_value_count":null,
                                  "lower_bound":"Депозит нового к",
                                  "upper_bound":"Получен возврат"
                              },
                              "transaction_date": {
                                  "column_size":57,
                                  "value_count":4,
                                  "null_value_count":0,
                                  "nan_value_count":null,
                                  "lower_bound":2025-02-10,
                                  "upper_bound":2025-02-12
                              },
                              "transaction_id": {
                                  "column_size":64,
                                  "value_count":4,
                                  "null_value_count":0,
                                  "nan_value_count":null,
                                  "lower_bound":1009,
                                  "upper_bound":1012
                              },
                              "verified": {
                                  "column_size":42,
                                  "value_count":4,
                                  "null_value_count":0,
                                  "nan_value_count":null,
                                  "lower_bound":true,
                                  "upper_bound":true
                              }
                          }
```
