## Apache Iceberg. Упражнение: Эволюция схемы

Пора применить теорию на практике. В этом упражнении вы создадите таблицу Iceberg, последовательно измените её схему и убедитесь, что все операции безопасны и обратимы.

## Цели

- Создать таблицу `user_events` с базовой схемой.
- Добавить новые колонки без перезаписи данных.
- Удалить колонку и проверить, что данные остаются доступны через `time travel`.
- Переименовать колонку и убедиться, что исторические запросы работают.
- Расширить тип колонки (`widening`).
- Изменить порядок колонок для улучшения читаемости.

## Предварительные требования

- Локальное окружение Iceberg (как в упражнении «Каталоги»).
- Доступ к `Spark SQL` или другому движку, поддерживающему `Iceberg`.
- Около 20 минут.

## Шаг 1: Запуск окружения

Если у вас ещё не запущено локальное окружение, выполните команды из упражнения «Каталоги»:

```
cd iceberg-course-exercises
docker compose up -d
```

Подключится к Spark SQL:

```
docker compose exec -it spark-iceberg spark-sql --conf "spark.hadoop.hive.cli.print.header=true"
```

Убедитесь, что каталог demo доступен:

```
SHOW CATALOGS;
```

Создайте базу данных для упражнения:

```
CREATE NAMESPACE demo.schema_evolution;
USE demo.schema_evolution;
```

## Шаг 2: Создание исходной таблицы

Создадим таблицу `user_events` с тремя колонками:

```sql
CREATE TABLE user_events (
    event_id BIGINT,
    user_id INT,
    event_type STRING
)
USING iceberg
TBLPROPERTIES ('format-version'='2');
```

Вставим несколько тестовых записей:

```sql
INSERT INTO user_events VALUES
    (1, 1001, 'login'),
    (2, 1002, 'purchase'),
    (3, 1001, 'logout');
```

Проверим, что данные записались:

```sql
SELECT * FROM user_events ORDER BY event_id;
```

<img width="670" height="118" alt="image" src="https://github.com/user-attachments/assets/8afb2d4b-6c8c-4b62-b8ac-30dd6809153a" />

## Шаг 3: Добавление колонок

Маркетинг просит добавить информацию об устройстве и версии браузера. Выполним:

```sql
ALTER TABLE user_events ADD COLUMNS (
    device_type STRING,
    browser_version STRING
);
```

Теперь вставим новую запись с заполненными новыми колонками:

```sql
INSERT INTO user_events VALUES
    (4, 1003, 'view', 'mobile', 'Chrome 120');
```

Запросим таблицу:

```sql
SELECT * FROM user_events ORDER BY event_id;
```

<img width="726" height="134" alt="image" src="https://github.com/user-attachments/assets/ef1cc8db-88be-4c17-a440-7441314277c1" />

<img width="786" height="190" alt="image" src="https://github.com/user-attachments/assets/0c470c9d-fe82-4bb2-8a0c-ed5aa73b4e12" />

Вы видите, что старые записи имеют `NULL` в новых колонках, а новая запись — заполненные значения. Это обычное поведение реляционных баз, но в Iceberg оно достигнуто без перезаписи файлов.

## Шаг 4: Удаление колонки

Через некоторое время выясняется, что `browser_version` больше не нужна. Удалим её:

```sql
ALTER TABLE user_events DROP COLUMN browser_version;
```

Запросим таблицу — колонка исчезла:

```sql
SELECT * FROM user_events ORDER BY event_id;
```

<img width="709" height="134" alt="image" src="https://github.com/user-attachments/assets/399ac14e-ae76-4390-91e4-6633c87d8929" />

*Куда делись данные? Они остались в хранилище, но скрыты от текущего снапшота. Давайте проверим с помощью `time travel`.*

## Шаг 5: Time travel к предыдущему снапшоту

Узнаем `ID` снапшота перед удалением колонки. Сначала посмотрим историю снапшотов:

```sql
SELECT
    snapshot_id,
    committed_at,
    operation
FROM demo.schema_evolution.user_events.snapshots
ORDER BY committed_at;
```

Запомните snapshot_id того снапшота, где колонка ещё существовала (скорее всего, второй сверху). Используем его в запросе:

<img width="789" height="188" alt="image" src="https://github.com/user-attachments/assets/1182b6b8-4f84-4f91-861d-672ece2af9cd" />

```sql
SELECT *
FROM demo.schema_evolution.user_events
FOR VERSION AS OF 8201666587885597047
ORDER BY event_id;
```

Вы снова увидите колонку `browser_version`! Это доказывает, что Iceberg не стирает данные при удалении колонки — он лишь помечает её как удалённую в метаданных.

<img width="662" height="190" alt="image" src="https://github.com/user-attachments/assets/60b53480-7e3d-4068-94c6-aff28b7f3aa5" />

## Шаг 6: Переименование колонки

Колонка `event_type` кажется недостаточно описательной. Переименуем её в `action_category`:

```sql
ALTER TABLE user_events RENAME COLUMN event_type TO action_category;
```

Проверим, что переименование сработало:

```sql
SELECT action_category, user_id FROM user_events ORDER BY event_id;
```

<img width="890" height="137" alt="image" src="https://github.com/user-attachments/assets/472f29a0-3693-4f0c-9159-179681f0fed7" />

Исторические данные остались доступны — они просто теперь фигурируют под новым именем. Если вы выполните `time travel` к снапшоту до переименования, там колонка будет называться `event_type`.

## Шаг 7: Расширение типа колонки (widening)

Предположим, у вас внезапно появилось более `4,2` миллиарда пользователей (поздравляем!). Колонка `user_id` типа `INT` уже не вмещает такие значения. Расширим её до `BIGINT`:

```sql
ALTER TABLE user_events ALTER COLUMN user_id TYPE BIGINT;
```

Вставьте запись с большим значением `user_id`:

```sql
INSERT INTO user_events VALUES (5, 5000000000, 'click', 'desktop');
```

Запросите таблицу — всё работает. Старые данные по‑прежнему хранятся как `INT`, но при чтении автоматически приводятся к `BIGINT`.

```sql
SELECT user_id FROM user_events ORDER BY event_id;
```

<img width="776" height="156" alt="image" src="https://github.com/user-attachments/assets/297087f5-27e3-455a-acfc-17d9bc488b65" />

## Шаг 8: Изменение порядка колонок

Таблица стала выглядеть неупорядоченно. Давайте переместим `action_category` сразу после `event_id` для лучшей читаемости:

```sql
ALTER TABLE user_events ALTER COLUMN action_category AFTER event_id;
```

Проверим схему:

```sql
DESCRIBE user_events;
```

<img width="497" height="132" alt="image" src="https://github.com/user-attachments/assets/c367f59b-81f5-4ed4-855f-9f20143ea8f5" />

Колонки теперь идут в порядке: `event_id`, `action_category`, `user_id`, `device_type`. Ни один файл данных не был перезаписан — только метаданные.

## Шаг 9: Эволюция комплексного типа (опционально)

Если ваш движок поддерживает, можно попробовать работу со структурами. Создадим новую таблицу с полем‑структурой:

```sql
CREATE TABLE user_prefs (
    user_id BIGINT,
    preferences STRUCT<email_notifications:BOOLEAN, color_theme:STRING>
)
USING iceberg;
```

Добавим поле в структуру:

```sql
ALTER TABLE user_prefs ADD COLUMN preferences.mobile_notifications BOOLEAN;
```

```sql
DESCRIBE user_prefs;
```

<img width="979" height="95" alt="image" src="https://github.com/user-attachments/assets/f2ccd1a3-4ebc-44e1-9560-5eb0e1255fbe" />

Это демонстрирует, что эволюция схемы работает и для вложенных типов.

## Что вы узнали
- Добавление колонок — мгновенная операция, старые записи получают `NULL`.
- Удаление колонок — данные не стираются, остаются доступны через `time travel.
- Переименование колонок — меняется только имя в метаданных, исторические запросы работают.
- Расширение типов — безопасное приведение при чтении без перезаписи.
- Изменение порядка колонок — чисто косметическое изменение, не затрагивающее данные.
- `Time travel` — мощный инструмент для доступа к предыдущим состояниям схемы и данных.

*Эволюция — это не революция. Iceberg позволяет менять схему постепенно, без катастрофических последствий. Как садовник, который подрезает ветви, а не вырубает дерево.*

## Что дальше? 

В следующем уроке мы изучим Партицирование и эволюция партиций — как организовать данные для эффективных запросов и менять стратегию партицирования без перезаписи.
