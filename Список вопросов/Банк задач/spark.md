### PySpark — GroupBy и Aggregation

<details>
<summary>Задача</summary>

**Условие**

Есть DataFrame с заказами:

```python
data = [
    (1, 101, 500),
    (2, 102, 1200),
    (3, 101, 800),
    (4, 103, 300),
    (5, 102, 700),
    (6, 103, 400),
    (7, 103, 500)
]

columns = ["order_id", "customer_id", "amount"]

df = spark.createDataFrame(data, columns)
```

Напиши PySpark-код, который для каждого клиента рассчитает:

1. customer_id — идентификатор клиента.
2. total_amount — общую сумму заказов.
3. orders_count — количество заказов.

Ожидаемый результат:

```
+-----------+------------+------------+
|customer_id|total_amount|orders_count|
+-----------+------------+------------+
|        101|        1300|           2|
|        102|        1900|           2|
|        103|        1200|           3|
+-----------+------------+------------+
```

Условия:
- Используй DataFrame API.
- Используй groupBy() и agg().
- Не используй Spark SQL.

**Решение**

```python
import pyspark.sql.functions as F
res = (
    df
    .groupBy("customer_id")
    .agg(
        F.sum("amount").alias("total_amount"),
        F.count("order_id").alias("orders_count")
    )
)
res.show()
```

</details>


### PySpark — window spec

<details>
<summary>Задача</summary>

**Условие**

Есть DataFrame с историей изменений сотрудников:

```python
from pyspark.sql import functions as F
from pyspark.sql.window import Window

data = [
    (1, "Иван", "Moscow", "2026-11-18 10:00:00"),
    (1, "Иван", "SPB", "2026-11-19 12:00:00"),
    (2, "Петр", "Kazan", "2026-11-18 09:00:00"),
    (2, "Петр", "Moscow", "2026-11-19 15:00:00"),
    (3, "Анна", "Moscow", "2026-11-18 11:00:00"),
    (3, "Анна", "Moscow", "2026-11-19 08:00:00"),
]

columns = ["employee_id", "name", "city", "updated_at"]
df = spark.createDataFrame(data, columns)
```

Для каждого сотрудника необходимо оставить только последнюю запись по updated_at.

Ожидаемый результат:

```text
employee_id	name	city	updated_at
1	Иван	SPB	2026-11-19 12:00:00
2	Петр	Moscow	2026-11-19 15:00:00
3	Анна	Moscow	2026-11-19 08:00:00
```

**Решение**

```python
window_spec = (Window.partitionBy("employee_id").orderBy(F.col("updated_at").desc()))
df_res = df.withColumn("row_num", F.row_number().over(window_spec)).where(F.col("row_num") == 1).select('employee_id', 'name', 'city', 'updated_at')
df_res.show(10)
```
</details>
