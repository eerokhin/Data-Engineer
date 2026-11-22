# Типы даты/времени

```time``` - время суток (без даты)

```timestamp``` - дата и время

```interval``` - временной интервал

```date``` - дата (без времени суток)

Стандарт SQL требует, чтобы тип timestamp подразумевал timestamp without time zone (время без часового пояса), и PostgreSQL следует этому. Для краткости timestamp with time zone можно записать как timestamptz; это расширение PostgreSQL.

# Текущие дата и время

Для получения только текущей даты:

```
SELECT CURRENT_DATE;
```
Для получения только текущего времени (без даты):

```
SELECT CURRENT_TIME;
```

Для получения текущей даты и времени (включая час, минуту и секунду):

```
SELECT NOW();
```

# EXTRACT

Функция EXTRACT в PostgreSQL используется для извлечения различных компонентов даты и времени (например, года, месяца, дня, часа и т.д.) из значения типа timestamp, date, time и других типов данных.

| Поле              | Описание                               |
| ----------------- | -------------------------------------- |
| `CENTURY`         | Век (например, 2025 → 21)              |
| `DAY`             | День месяца                            |
| `DECADE`          | Десятилетие (2025 → 202)               |
| `DOW`             | День недели (0=воскресенье, 6=суббота) |
| `DOY`             | День года (от 1 до 366)                |
| `EPOCH`           | Кол-во секунд с начала Unix эпохи      |
| `HOUR`            | Час                                    |
| `ISODOW`          | ISO-день недели (1=понедельник)        |
| `ISOYEAR`         | ISO год                                |
| `MICROSECONDS`    | Микросекунды                           |
| `MILLENNIUM`      | Тысячелетие (2025 → 3)                 |
| `MILLISECONDS`    | Миллисекунды                           |
| `MINUTE`          | Минута                                 |
| `MONTH`           | Месяц (1-12)                           |
| `QUARTER`         | Квартал (1-4)                          |
| `SECOND`          | Секунда                                |
| `TIMEZONE`        | Часовой пояс (в секундах)              |
| `TIMEZONE_HOUR`   | Часовая часть временной зоны           |
| `TIMEZONE_MINUTE` | Минутная часть временной зоны          |
| `WEEK`            | Номер недели года                      |
| `YEAR`            | Год                                    |


```
-- Извлечение года из даты
SELECT EXTRACT(YEAR FROM '2025-01-24'::date) AS year;

 year
------
 2025
```

```
-- Извлечение месяца из timestamp
SELECT EXTRACT(MONTH FROM '2025-01-24 15:30:00'::timestamp) AS month;

 month
------
     1
```

```
-- Извлечение дня недели (цифровое представление)
SELECT EXTRACT(DOW FROM '2025-01-24'::date) AS day_of_week;

 day_of_week
-------------
           5
```

```
--Использование EXTRACT для извлечения продолжительности
SELECT EXTRACT(DAY FROM '2025-01-24'::date - '2025-01-01'::date) AS days_diff;

 days_diff
-----------
        23
```

```
SELECT EXTRACT(MONTH FROM INTERVAL '1 year 2 months') AS months;

months
-----------
2
```

# DATE_TRUNC

В PostgreSQL функция date_trunc используется для округления временных значений (типов данных timestamp, timestamptz, date) до указанного интервала. Она удаляет часть времени, оставляя только данные с точностью до выбранного уровня. Например, можно округлить дату до месяца, года, часа и так далее.

| Единица (`'unit'`) | Описание                       |
| ------------------ | ------------------------------ |
| `microseconds`     | До микросекунды                |
| `milliseconds`     | До миллисекунды                |
| `second`           | До секунды                     |
| `minute`           | До минуты                      |
| `hour`             | До часа                        |
| `day`              | До дня                         |
| `week`             | До начала недели (понедельник) |
| `month`            | До первого дня месяца          |
| `quarter`          | До начала квартала             |
| `year`             | До начала года                 |
| `decade`           | До начала десятилетия          |
| `century`          | До начала века                 |
| `millennium`       | До начала тысячелетия          |


```
DATE_TRUNC('interval', date_or_timestamp)

где:

'interval' — это строка, указывающая на уровень округления. Например, 'minute', 'hour', 'day', 'month', 'year'.

date_or_timestamp — это значение даты или временной метки, которое нужно округлить.
```

```
-- Округление до дня
SELECT date_trunc('day', '2025-01-24 14:45:30'::timestamp);
--------------
2025-01-24 00:00:00
```

```
-- Округление до месяца
SELECT date_trunc('month', '2025-01-24 14:45:30'::timestamp);
--------------
2025-01-01 00:00:00
```

```
SELECT DATE_TRUNC('hour', TIMESTAMP '2025-05-27 14:32:45') AS result;
--------------
2025-05-27 14:00:00
```

# DATE_ADD

В PostgreSQL нет функции с именем DATE_ADD, как, например, в MySQL, но аналогичный функционал можно выполнить с помощью оператора + или функции interval.

```
SELECT '2025-01-24'::date + 5;
------------------
2025-01-29
```

```
SELECT '2025-01-24'::date + INTERVAL '1 month';
-----------------
2025-02-24
```

# TO_CHAR

`TO_CHAR()` преобразует дату, время или число в строку (TEXT) по заданному формату.

`TO_CHAR(value, format)`

`value` — исходное значение (дата, время, timestamp или число).

`format` — шаблон, определяющий, как будет выглядеть результат.

| Формат | Значение | Пример |
|:---|:---|:---|
| `YYYY` | Год | `2026` |
| `MM` | Месяц с ведущим нулём | `03` |
| `DD` | День с ведущим нулём | `03` |
| `FMDD` | День без ведущего нуля | `3` |
| `FMMM` | Месяц без ведущего нуля | `3` |
| `HH24` | Часы в 24-часовом формате | `17` |
| `HH12` | Часы в 12-часовом формате | `05` |
| `MI` | Минуты | `50` |
| `SS` | Секунды | `30` |

**FM (Fill Mode)** — модификатор, который убирает лишние пробелы и ведущие нули у числовых элементов формата.

**Пример**

```sql
Исходное значение: TIMESTAMP '2026-11-03 17:50:00'
Только время:
SELECT TO_CHAR(TIMESTAMP '2026-11-03 17:50:00', 'HH24:MI');
-- 17:50
```

**Пример 2**

Было

<img width="442" height="103" alt="image" src="https://github.com/user-attachments/assets/3431d626-dc83-4503-a28b-b29f33f854be" />

Запрос

```sql
SELECT
    TO_CHAR(time_out, 'HH24:MI, FMDD.FMMM')
    || ' - ' ||
    TO_CHAR(time_in, 'HH24:MI, FMDD.FMMM') AS flight_time
FROM Trip
```

Стало

<img width="194" height="118" alt="image" src="https://github.com/user-attachments/assets/415f283a-0810-4b2d-898d-3ac1c133acdc" />


# Получить текущий месяц

Сегодня 27.01.2025 пример работы функции

```
SELECT EXTRACT(MONTH FROM CURRENT_DATE) AS current_month;

 current_month 
----------------
              1

```

или 

```
SELECT DATE_PART('month', CURRENT_DATE) AS current_month;

 current_month 
----------------
              1
```

EXTRACT и DATE_PART выполняют одно и тоже, отличие в синтаксисе


# Получить интервал времени

```
SELECT
  EXTRACT(epoch FROM ('2025-01-27 18:00:00'::timestamp - '2025-01-27 14:30:00'::timestamp)) / 3600 AS hours,
  (EXTRACT(epoch FROM ('2025-01-27 18:00:00'::timestamp - '2025-01-27 14:30:00'::timestamp)) / 60) % 60 AS minutes;

 hours | minutes
-------+---------
     3 |      30
```

# Пример

```
SELECT CAST('2025-05-27' AS timestamp) AS cast_col_timestmp,
       CAST('2025-05-27 12:00:00' AS date) AS cast_col_date,
       TO_DATE('2025-05-27 12:00:00', 'YYYY-MM-DD') AS to_date_col,
       CURRENT_DATE AS current_date_col
```

![image](https://github.com/user-attachments/assets/2af96ebe-65f5-4239-8ba3-8b190b84a86c)

