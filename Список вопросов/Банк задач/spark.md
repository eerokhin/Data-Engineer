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
