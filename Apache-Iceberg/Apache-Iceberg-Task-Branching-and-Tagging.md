## Apache Iceberg. Упражнение: Ветвление и тегирование

До сих пор вы работали со снапшотами по их `ID` или временным меткам. Это работает, но попробуйте объяснить вашему финансовому директору, что «квартальный отчёт использует снапшот `7851662191363948742`». Не очень удобно для пользователя.

Теги и ветки привносят `Git`‑подобную семантику в таблицы Iceberg:

- Теги — это именованные ссылки на конкретные снапшоты. Думайте о них как о закладках: «это данные, которые мы использовали для отчёта за `Q4`» или «это состояние перед большой миграцией».
- Ветки — это независимые линии разработки. Вы можете писать в ветку, не влияя на основную таблицу, валидировать изменения, а затем либо опубликовать их, либо выбросить. Это основа `workflow Write‑Audit‑Publish` (`WAP`).

В этом упражнении вы создадите теги для важных снапшотов (для соответствия требованиям), создадите `staging`‑ветку, загрузите в неё данные, проверите их и опубликуете в продакшен.

## Цели обучения

К концу упражнения вы сможете:

- Создавать теги для снапшотов и управлять ими
- Запрашивать данные по конкретному тегу
- Создавать ветки для изолированных записей
- Реализовывать workflow `Write‑Audit‑Publish`
- Выполнять fast‑forward основной ветки для включения проверенных изменений

## Предварительные требования

- Завершённое упражнение 4 (или запущенное окружение)
- Около 25 минут

## Шаг 1: Подготовка окружения

Запустите окружение, если оно ещё не запущено:

```
docker compose up -d
```

Запустите Spark SQL:

```
docker compose exec -it spark-iceberg spark-sql --conf "spark.hadoop.hive.cli.print.header=true"
```

Создадим таблицу, представляющую финансовый журнал — то, где качество данных имеет значение:

```sql
CREATE NAMESPACE IF NOT EXISTS demo.finance;
USE demo.finance;

DROP TABLE IF EXISTS transactions;

CREATE TABLE transactions (
    transaction_id BIGINT,
    account_id BIGINT,
    transaction_date DATE,
    amount DECIMAL(15, 2),
    description STRING,
    verified BOOLEAN
)
USING iceberg
TBLPROPERTIES ('format-version'='2', 'write.format.default'='parquet');
```

Загрузите некоторые начальные проверенные транзакции:

```sql
INSERT INTO transactions VALUES
    (1001, 100, CAST('2025-01-02' AS DATE), 5000.00, 'Начальный депозит', true),
    (1002, 100, CAST('2025-01-05' AS DATE), -150.00, 'Канцелярские товары', true),
    (1003, 101, CAST('2025-01-03' AS DATE), 12000.00, 'Начальный депозит', true),
    (1004, 101, CAST('2025-01-10' AS DATE), -3200.00, 'Покупка оборудования', true),
    (1005, 102, CAST('2025-01-04' AS DATE), 8500.00, 'Начальный депозит', true);
```

Проверьте данные:

```sql
SELECT * FROM transactions ORDER BY transaction_id;
```

<img width="871" height="244" alt="image" src="https://github.com/user-attachments/assets/904086a2-0556-4da9-bea5-631fef2e82c2" />

## Шаг 2: Создайте тег для закрытия месяца

`31` января. Финансовой команде нужно закрыть книги. Давайте пометим текущее состояние тегом, чтобы мы всегда могли воспроизвести числа за январь:

```sql
ALTER TABLE transactions CREATE TAG `jan-2025-close`;
```

Проверьте, что тег создан:

```sql
SELECT * FROM demo.finance.transactions.refs;
```

Вы должны увидеть:

<img width="876" height="123" alt="image" src="https://github.com/user-attachments/assets/811b4ac9-ea95-4dd9-b738-7fef70a22491" />

Обратите внимание, что `main` также указан — это ветка по умолчанию, которая есть у каждой таблицы Iceberg.

## Шаг 3: Продолжаем обычные операции

Наступает февраль. Поступают новые транзакции:

```sql
INSERT INTO transactions VALUES
    (1006, 100, CAST('2025-02-01' AS DATE), -89.99, 'Подписка на ПО', true),
    (1007, 102, CAST('2025-02-03' AS DATE), -1200.00, 'Оплата подрядчику', true),
    (1008, 101, CAST('2025-02-05' AS DATE), 4500.00, 'Получен платёж от клиента', true);
```

Текущая таблица теперь содержит `8` транзакций:

```sql
SELECT COUNT(*) FROM transactions;
```

## Шаг 4: Запрос помеченного снапшота

Приходят аудиторы. Они хотят увидеть точно, как выглядели книги на момент закрытия января. Без проблем:

```sql
SELECT *
FROM transactions VERSION AS OF 'jan-2025-close'
ORDER BY transaction_id;
```

<img width="882" height="249" alt="image" src="https://github.com/user-attachments/assets/c0ff2b66-d57c-4a4e-8fe5-0ea07aff7a85" />

Только исходные `5` транзакций. Февральские данные в этом теге не существуют.

Давайте проверим, что балансы счетов соответствуют отчётности:

```sql
SELECT
    account_id,
    SUM(amount) AS balance_at_jan_close
FROM transactions VERSION AS OF 'jan-2025-close'
GROUP BY account_id
ORDER BY account_id;
```

Вы должны увидеть:

<img width="584" height="170" alt="image" src="https://github.com/user-attachments/assets/8e4d8682-76b2-4959-a47b-448b9bfe6065" />

Эти числа неизменяемы. Независимо от того, что произойдёт с таблицей в будущем, этот тег всегда будет показывать одни и те же данные.

## Шаг 5: Создайте staging‑ветку

Теперь давайте рассмотрим более сложный сценарий. Ваш `ETL`‑пайплайн имеет новую партию транзакций для загрузки, но вы хотите проверить их, прежде чем они попадут в продакшен.

Создайте staging‑ветку:

```sql
ALTER TABLE transactions CREATE BRANCH staging;
```

Проверьте ссылки:

```sql
SELECT name, type, snapshot_id
FROM demo.finance.transactions.refs;
```

<img width="714" height="174" alt="image" src="https://github.com/user-attachments/assets/f4903252-b5e5-4b2d-a7fe-51c14b7e0cda" />

Теперь у вас три ссылки: `main`, `staging` и `jan-2025-close`. Обратите внимание, что `staging` начинается с того же снапшота, что и `main`.

## Шаг 6: Запись в staging‑ветку

Чтобы писать в ветку с использованием `Write‑Audit‑Publish`, сначала нужно включить эту возможность:

```sql
ALTER TABLE demo.finance.transactions
    SET TBLPROPERTIES ('write.wap.enabled' = 'true');
```

Затем нужно установить, какую ветку вы хотите использовать как цель записи:

```sql
SET spark.wap.branch = staging;
```

Теперь любые записи идут в staging‑ветку, а не в `main`. Загрузите новую партию:

```sql
INSERT INTO transactions VALUES
    (1009, 100, CAST('2025-02-10' AS DATE), -500.00, 'Консалтинговый сбор', false),
    (1010, 103, CAST('2025-02-10' AS DATE), 15000.00, 'Депозит нового клиента', false),
    (1011, 101, CAST('2025-02-11' AS DATE), -750.00, 'Командировочные расходы', false),
    (1012, 100, CAST('2025-02-12' AS DATE), 2000.00, 'Получен возврат', false);
```

Теперь проверьте обе ветки:

```sql
-- Продакшен (ветка main) — нужно явно запросить
SELECT COUNT(*) AS main_count
FROM transactions VERSION AS OF 'main';

-- Staging‑ветка (текущая цель записи, также доступна по имени)
SELECT COUNT(*) AS staging_count
FROM transactions VERSION AS OF 'staging';
```

В продакшене `8` транзакций. В `staging` — `12`. Ветки разошлись.

## Шаг 7: Валидация данных в staging

Перед публикацией давайте запустим некоторые проверки качества данных в `staging`:

```sql
-- Проверка на отрицательные балансы (нарушение бизнес‑правила)
SELECT
    account_id,
    SUM(amount) AS balance
FROM transactions VERSION AS OF 'staging'
GROUP BY account_id
HAVING SUM(amount) < 0;
```

Отрицательных балансов нет — хорошо.

```sql
-- Проверка на непроверенные транзакции (требуют ревью)
SELECT *
FROM transactions VERSION AS OF 'staging'
WHERE verified = false;
```

<img width="870" height="208" alt="image" src="https://github.com/user-attachments/assets/2e0a55fb-06be-4334-a9a2-9001cc6c15e9" />

Новые транзакции непроверенные. В реальном workflow вы могли бы:

- Запустить автоматические правила валидации
- Отправить алерты, если обнаружены аномалии
- Провести человеческий ревью и утверждение

Вы можете проверить, что продакшен всё ещё нетронут:

```sql
SELECT COUNT(*)
FROM transactions VERSION AS OF 'main'
WHERE verified = false;
```

Ноль непроверенных в продакшене.

Давайте пометим транзакции в `staging` как проверенные (помните, мы всё ещё пишем в `staging`):

```sql
UPDATE transactions
SET verified = true
WHERE verified = false;
```

Проверьте обновление (всё ещё в `staging`):

```sql
SELECT transaction_id, verified
FROM transactions VERSION AS OF 'staging'
WHERE transaction_id >= 1009;
```

<img width="697" height="216" alt="image" src="https://github.com/user-attachments/assets/84205742-cb05-4947-b2fb-1e001038037f" />

Все проверены.

## Шаг 8: Публикация проверенных изменений

Данные валидированы. Пора публиковать в продакшен.

Сначала посмотрим, куда указывает каждая ветка:

```sql
SELECT name, type, snapshot_id
FROM demo.finance.transactions.refs;
```

<img width="732" height="176" alt="image" src="https://github.com/user-attachments/assets/e6695a91-7977-46e7-b7d5-970f37f5c5ad" />

`Staging` опережает `main`. Чтобы опубликовать, мы делаем `fast‑forward main` к снапшоту `staging`:

```sql
CALL system.fast_forward('demo.finance.transactions', 'main', 'staging');
```

<img width="759" height="89" alt="image" src="https://github.com/user-attachments/assets/6406f880-39c7-4aae-a269-f6f2027f58ef" />

Это перемещает указатель ветки `main` так, чтобы он совпадал с `staging`. Никакие данные не копируются — это просто обновление метаданных.

Теперь сбросьте цель записи обратно на `main`:

```sql
ALTER TABLE demo.finance.transactions
    UNSET TBLPROPERTIES ('write.wap.enabled');
```

Проверьте, что продакшен теперь содержит все данные:

```sql
SELECT * FROM transactions ORDER BY transaction_id;
```

<img width="907" height="551" alt="image" src="https://github.com/user-attachments/assets/2cc9a07f-1e62-436c-82a0-d6e58d3b8442" />

Все `12` транзакций, все проверены.

## Шаг 9: Очистка ветки

`Staging`‑ветка выполнила свою задачу. Вы можете удалить её:

```sql
ALTER TABLE transactions DROP BRANCH staging;
```

Проверьте ссылки:

```sql
SELECT name, type FROM demo.finance.transactions.refs;
```

<img width="691" height="138" alt="image" src="https://github.com/user-attachments/assets/d2244c45-82ff-4ddd-919d-a779c397aad9" />

Остались только `main` и `jan-2025-close`.

## Шаг 10: Создайте ещё один тег

Давайте пометим закрытие февраля:

```sql
ALTER TABLE transactions CREATE TAG `feb-2025-close`;
```

Теперь вы можете сравнить любые две точки во времени:

```sql
SELECT period, account_id, balance FROM (
    -- Балансы января
    SELECT 'Январь' AS period, account_id, SUM(amount) AS balance
    FROM transactions VERSION AS OF 'jan-2025-close'
    GROUP BY account_id
    UNION ALL
    -- Балансы февраля
    SELECT 'Февраль' AS period, account_id, SUM(amount) AS balance
    FROM transactions VERSION AS OF 'feb-2025-close'
    GROUP BY account_id
) results
ORDER BY period, account_id;
```

Вы должны увидеть:

<img width="799" height="353" alt="image" src="https://github.com/user-attachments/assets/d863fb30-ec14-4c85-a5d5-ee0a99e8c170" />

Это невероятно мощно для финансовой отчётности, аудиторских следов и анализа трендов.

## Шаг 11: Управление тегами

Теги могут иметь политики удержания. Создайте тег с автоматическим истечением:

```sql
ALTER TABLE transactions CREATE TAG `temp-debug-tag` RETAIN 7 DAYS;
```

Через 7 дней этот тег станет кандидатом на очистку во время экспирации снапшотов.

Перечислите все теги с их свойствами:

```sql
SELECT
    name,
    type,
    snapshot_id,
    max_reference_age_in_ms / 86400000 AS retention_days
FROM demo.finance.transactions.refs
WHERE type = 'TAG';
```

<img width="830" height="184" alt="image" src="https://github.com/user-attachments/assets/8b2a3d87-c5d8-445a-9b5b-89067dd28fff" />

Не забывайте регулярно удалять теги, которые больше не нужны, чтобы держать ссылки таблицы в порядке:

```sql
ALTER TABLE transactions DROP TAG `temp-debug-tag`;
```

## Шаг 12: Очистка

Выйдите из Spark SQL:

```
exit;
```

Если вы закончили:

```
docker compose down -v
```

## Что вы узнали

- Теги — это именованные неизменяемые ссылки на снапшоты — идеально для соответствия требованиям и воспроизводимости.
- Ветки позволяют изолированные записи без влияния на продакшен.
- `Workflow Write‑Audit‑Publish` (`WAP`): `stage` → `validate` → `fast‑forward`.
- `fast_forward` публикует ветку, перемещая указатель `main`.
- Теги и ветки — это операции только с метаданными — мгновенные и дешёвые.

## Практические use‑cases

Теги:

- Регуляторное соответствие («это `Q4 2024`, как отчитано в `SEC`»)
- Воспроизводимость машинного обучения («модель `v2.3` обучалась на этом снапшоте»)
- Маркеры релизов («`before‑migration`», «`after‑migration`»)

Ветки:

- Валидация `ETL` перед публикацией
- `A/B`‑тестирование различных трансформаций данных
- Экспериментирование без риска для продакшена
- `Blue/green`‑деплойменты данных

*«Ветвление и тегирование в Iceberg — это как Git для данных: можно ставить закладки на важные моменты и экспериментировать в изоляции, не боясь сломать продакшен. Только не забывайте удалять старые ветки, иначе ваш data lake превратится в архив забытых экспериментов.»*
