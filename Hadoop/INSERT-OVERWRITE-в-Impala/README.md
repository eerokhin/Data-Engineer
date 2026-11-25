## INSERT OVERWRITE в Impala

### 1. Создаём партиционированную таблицу

Удаляем таблицу, если она уже существует:

```sql
DROP TABLE IF EXISTS dm_orders_test;
```

Создаём таблицу с партиционированием по отчётной дате:

```sql
CREATE TABLE dm_orders_test (
    order_id BIGINT,
    customer_id BIGINT,
    amount DECIMAL(12,2)
)
PARTITIONED BY (
    report_dt DATE
)
STORED AS PARQUET;
```

### 2. Загружаем тестовые данные

Имитируем ежемесячную загрузку данных за август, сентябрь и октябрь.

**Август:**

```sql
INSERT INTO dm_orders_test
PARTITION (report_dt = '2026-08-31')
VALUES
    (1, 101, 1500),
    (2, 102, 2500),
    (3, 103, 3500);
```

**Сентябрь:**

```sql
INSERT INTO dm_orders_test
PARTITION (report_dt = '2026-09-30')
VALUES
    (4, 104, 4500),
    (5, 105, 5500);
```

**Октябрь:**

```sql
INSERT INTO dm_orders_test
PARTITION (report_dt = '2026-10-31')
VALUES
    (6, 106, 6500),
    (7, 107, 7500);
```

Проверяем содержимое таблицы:

```sql
SELECT *
FROM dm_orders_test
ORDER BY report_dt, order_id;
```

Ожидаемый результат — 7 записей:

<img width="454" height="160" alt="image" src="https://github.com/user-attachments/assets/bf53e459-b08e-487f-a3c3-305051b9bdbe" />

### 3. Имитируем частичную загрузку

Представим, что Airflow запустил загрузку октября, но задача завершилась ошибкой. В результате в октябрьскую партицию попала только одна запись.

Выполняем:

```sql
INSERT OVERWRITE TABLE dm_orders_test
PARTITION (report_dt = '2026-10-31')
VALUES
    (6, 106, 6500);
```

Проверяем данные:

```sql
SELECT *
FROM dm_orders_test
ORDER BY report_dt, order_id;
```

<img width="454" height="143" alt="image" src="https://github.com/user-attachments/assets/a6a41f43-694a-44af-b117-e073c0c1a703" />

Что произошло:

- Август остался без изменений — 3 записи.
- Сентябрь остался без изменений — 2 записи.
- Октябрь перезаписан — теперь только 1 запись.

`INSERT OVERWRITE` заменил содержимое октябрьской партиции, а не добавил новую запись к существующим.

### 4. Восстанавливаем октябрьскую партицию

Повторно загружаем полный набор данных за октябрь:

```sql
INSERT OVERWRITE TABLE dm_orders_test
PARTITION (report_dt = '2026-10-31')
VALUES
    (6, 106, 6500),
    (7, 107, 7500),
    (8, 108, 8500);
```

Теперь в октябрьской партиции находятся 3 записи.

<img width="455" height="178" alt="image" src="https://github.com/user-attachments/assets/64589713-353b-464c-a440-b0a0edd25ea7" />

### 5. Проверяем 

Повторно выполняем тот же запрос:

```sql
INSERT OVERWRITE TABLE dm_orders_test
PARTITION (report_dt = '2026-10-31')
VALUES
    (6, 106, 6500),
    (7, 107, 7500),
    (8, 108, 8500);
```

Количество записей не увеличится. Октябрьская партиция будет содержать те же 3 строки.

Это и есть пример идемпотентной загрузки: повторный запуск с теми же исходными данными не приводит к дублированию.

### 6. Проверяем итоговые данные

```sql
SELECT
    report_dt,
    COUNT(*) AS cnt,
    SUM(amount) AS total_amount
FROM dm_orders_test
GROUP BY report_dt
ORDER BY report_dt;
```

Ожидаемый результат:

<img width="329" height="83" alt="image" src="https://github.com/user-attachments/assets/bc2e1556-2a32-4e8d-8bdf-7e64ba59c019" />

Август и сентябрь не изменились, октябрь успешно перезагружен.

### 7. Обновляем статистику таблицы

После загрузки данных можно обновить статистику:

```sql
COMPUTE STATS dm_orders_test;
```

Проверяем статистику:

```sql
SHOW TABLE STATS dm_orders_test;
```
<img width="1436" height="106" alt="image" src="https://github.com/user-attachments/assets/7af2d5ff-bccc-4e3e-bee5-bbfee8167bef" />

Impala использует статистику о количестве строк, размере данных и распределении по партициям для оптимизации выполнения запросов.

### Итог

В этом примере мы рассмотрели сценарий ежемесячной загрузки:

1. Загружаем данные за каждый месяц.
2. Имитируем ошибку при загрузке октября.
3. Перезаписываем только октябрьскую партицию.
4. Повторно выполняем загрузку и проверяем отсутствие дубликатов.
5. Обновляем статистику таблицы.

**Главная идея:** одна таблица, один DAG и партиционирование по отчётной дате. При повторной загрузке месяца заменяем только соответствующую партицию через `INSERT OVERWRITE`.
