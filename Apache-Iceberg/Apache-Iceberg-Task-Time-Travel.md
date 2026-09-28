## Apache Iceberg. Упражнение: Time Travel

Мы создавали таблицы, меняли их схемы и партицировали для производительности. Теперь поговорим об одной из самых крутых функций Iceberg — `time travel` (путешествие во времени).

Каждая операция записи в Iceberg создаёт снапшот — неизменяемую запись состояния таблицы в этот момент. Эти снапшоты — не просто для галочки. Вы можете их запрашивать. 
Можете откатываться к ним. Можете использовать, чтобы ответить на вопросы вроде «Как выглядела эта таблица вчера?» или «Каков был баланс клиента до того случайного `UPDATE`?».

В этом упражнении мы внесём изменения в таблицу, изучиме историю её снапшотов и запросим предыдущие версии данных.

## Цели обучения

К концу упражнения вы сможете:

- Просматривать историю снапшотов таблицы
- Запрашивать данные, какими они были в определённый момент времени
- Использовать как ID снапшотов, так и временные метки для `time travel`
- Откатывать таблицу к предыдущему состоянию

## Предварительные требования

- Завершённое упражнение 3 (или запущенное окружение)
- Около 20 минут 

## Шаг 1: Подготовка окружения

Запустите окружение, если оно ещё не запущено:

```
docker compose up -d
```

Запустите Spark SQL:

```
docker compose exec -it spark-iceberg spark-sql --conf "spark.hadoop.hive.cli.print.header=true"
```

Создадим свежую таблицу для этого упражнения. Мы используем небольшой набор данных, чтобы снапшоты было проще отслеживать:

```sql
CREATE NAMESPACE IF NOT EXISTS demo.ecommerce;
USE demo.ecommerce;

CREATE TABLE customers (
    customer_id BIGINT,
    name STRING,
    email STRING,
    balance DECIMAL(10, 2),
    status STRING
)
USING iceberg
TBLPROPERTIES ('format-version'='2', 'write.format.default'='parquet');
```

*`USING iceberg` - Говорит `Spark`: Создай эту таблицу как `Apache Iceberg table`, а не обычную `Spark/Parquet table`.*

Вставьте начальные данные:

```sql
INSERT INTO customers VALUES
    (1, 'Алиса Чен', 'alice@example.com', 1500.00, 'active'),
    (2, 'Боб Смит', 'bob@example.com', 2300.50, 'active'),
    (3, 'Кэрол Джонс', 'carol@example.com', 890.25, 'active'),
    (4, 'Дэвид Ли', 'david@example.com', 4200.00, 'active'),
    (5, 'Ева Мартинес', 'eva@example.com', 150.75, 'inactive');
```

Проверьте стартовую точку:

```sql
SELECT * FROM customers ORDER BY customer_id;
```

<img width="623" height="155" alt="image" src="https://github.com/user-attachments/assets/33f8a93f-7a0b-4b08-9386-04b83023b80b" />

## Шаг 2: Создаём историю

Теперь внесём изменения. В реальной системе они могли бы происходить в течение дней или недель. Мы сожмём эту временную шкалу.

**Обновление 1:** Боб погасил часть своего баланса:

```sql
UPDATE customers
SET balance = 1800.50
WHERE customer_id = 2;
```

**Обновление 2:** Кэрол совершила крупную покупку:

```sql
UPDATE customers
SET balance = 2890.25
WHERE customer_id = 3;
```

**Ой‑ой:** Кто‑то запустил плохое обновление — случайно обнулил все балансы:

```sql
UPDATE customers
SET balance = 0.00;
```

**Проверьте ущерб:**

```sql
SELECT * FROM customers ORDER BY customer_id;
```

<img width="642" height="156" alt="image" src="https://github.com/user-attachments/assets/e7012e10-25f4-47a3-8d21-786644104fe9" />

Все балансы теперь равны нулю. В традиционной базе данных вы бы лихорадочно искали бэкапы. С Iceberg у нас есть варианты.

## Шаг 3: Изучаем историю снапшотов

Давайте посмотрим каждую версию этой таблицы:

```sql
SELECT
    snapshot_id,
    parent_id,
    committed_at,
    operation
FROM demo.ecommerce.customers.snapshots
ORDER BY committed_at;
```

<img width="756" height="111" alt="image" src="https://github.com/user-attachments/assets/176c1fa3-b10d-4514-ab1f-11bca21d8777" />

Вы должны увидеть четыре снапшота:

- Начальный append (наш `INSERT`)
- `Overwrite` (обновление Боба)
- Ещё один `overwrite` (обновление Кэрол)
- Финальный `overwrite` (случайное массовое обновление)

Запомните значения `snapshot_id` — они понадобятся через мгновение. Также обратите внимание на временные метки в `committed_at`.

## Шаг 4: Запрос предыдущего снапшота

Давайте посмотрим на данные до катастрофы. Найдите `ID` снапшота, сделанного прямо перед массовым обновлением (второй `overwrite` в результатах таблицы `snapshots`), и запросите его:

```sql
-- Замените <SNAPSHOT_ID> на реальный ID из вашего вывода
SELECT *
FROM customers VERSION AS OF <SNAPSHOT_ID>
ORDER BY customer_id;
```

Вы увидите:

<img width="613" height="132" alt="image" src="https://github.com/user-attachments/assets/0729ea9d-ccab-47fe-a622-1a8db84bb524" />

Вот ваши данные, целые и невредимые. У Алисы всё ещё `$1,500`. У Боба `$1,800.50` (после его платежа). У Кэрол `$2,890.25` (после её покупки).

Вы также можете запросить по временной метке. Это часто практичнее — вы можете не знать `ID` снапшота, но знаете, что «данные были корректны в 14:00 вчера»:

```sql
-- Замените на метку времени между снапшотом 3 и 4
SELECT *
FROM customers TIMESTAMP AS OF '2026-09-28 18:15:32.418'
ORDER BY customer_id;
```

Настройте метку времени в соответствии с вашими значениями `committed_at`. Любая метка после снапшота `3`, но до снапшота `4` покажет вам состояние до катастрофы.

## Шаг 5: Откат таблицы

Смотреть на старые данные — это приятно, но иногда нужно реально отменить ущерб. Iceberg поддерживает откат к предыдущему снапшоту.

В Spark SQL используйте процедуру `rollback_to_snapshot`:

```sql
CALL system.rollback_to_snapshot(
  'demo.ecommerce.customers', 5554310500147269025
);
```

<img width="419" height="56" alt="image" src="https://github.com/user-attachments/assets/9fa847cd-036a-431e-9ccd-de6bde89e346" />

Замените `SNAPSHOT_ID` на снапшот перед массовым обновлением.

Теперь проверьте текущее состояние:

```sql
SELECT * FROM customers ORDER BY customer_id;
```

<img width="658" height="152" alt="image" src="https://github.com/user-attachments/assets/e9947881-f937-4626-80a1-e24d71f5771c" />

Балансы восстановлены. Плохое обновление отменено.

Важно: Откат обновляет указатель текущего снапшота таблицы, чтобы указывать на предыдущий снапшот — он не удаляет плохой снапшот и не создаёт новый. Вы по‑прежнему можете путешествовать во времени, чтобы увидеть катастрофу, если нужно. Проверьте:

```sql
SELECT
    snapshot_id,
    committed_at,
    operation
FROM demo.ecommerce.customers.snapshots
ORDER BY committed_at;
```

<img width="579" height="115" alt="image" src="https://github.com/user-attachments/assets/34d27405-1fc5-4b48-be21-8660afbd4eca" />

Вы всё ещё увидите те же четыре снапшота, что и раньше, но таблица теперь использует снапшот `3` как текущее состояние.

Вы можете убедиться в этом, выполнив:

```sql
SELECT * FROM demo.ecommerce.customers.refs;
```

<img width="965" height="73" alt="image" src="https://github.com/user-attachments/assets/ba834a86-6437-4aea-adae-a974b8f0a29f" />

Посмотрите, как ветка main указывает на снапшот, к которому вы откатились.

## Шаг 6: Сравнение версий

Time travel отлично подходит для отладки. Давайте сравним, что изменилось между двумя снапшотами.

```sql
SELECT
    curr.customer_id,
    curr.name,
    hist.balance AS balance_before,
    curr.balance AS balance_after,
    curr.balance - hist.balance AS difference
FROM customers curr
JOIN customers VERSION AS OF 5636692403768181432 AS hist
    ON curr.customer_id = hist.customer_id
ORDER BY curr.customer_id;
```

Вы должны увидеть:

<img width="633" height="131" alt="image" src="https://github.com/user-attachments/assets/d3d80cf6-5d4a-40b8-be42-a46a1c860672" />

Этот паттерн бесценен для аудита изменений или выяснения, что именно пошло не так.

## Шаг 7: Очистка

Выйдите из Spark SQL:

```
exit;
```

Если вы закончили на сегодня:

```
docker compose down -v
```

## Что вы узнали

- Каждая запись создаёт неизменяемый снапшот
- `FOR VERSION AS OF` позволяет запрашивать по `ID` снапшота
- `FOR TIMESTAMP AS OF` позволяет запрашивать по моменту времени
- `rollback_to_snapshot` восстанавливает таблицу к предыдущему состоянию (без потери истории)
- `Time travel` возможен, потому что файлы данных неизменяемы — Iceberg просто меняет, какие файлы ссылаются на каждый снапшот

## Практические use‑cases

- Отладка: «Как выглядела эта строка до запуска того ETL‑задания?»
- Аудит: «Покажите мне точно, какие данные были видны 31 декабря для соответствия требованиям»
- Восстановление: «Отменить тот случайный DELETE»
- Воспроизводимость: «Запустите этот анализ на тех же данных, что мы использовали в прошлом квартале»

*«Time travel — это как машина времени для данных: можно вернуться и посмотреть, что было вчера, позавчера или даже до того, как кто‑то случайно удалил всю таблицу. Только не пытайтесь убить дедушку парадокса.»*
