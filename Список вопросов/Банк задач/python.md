# Банк задач для собеседований по python

В этом разделе собраны практические задачи, которые часто встречаются на собеседованиях.

### Задача с собеседования в ВТБ

Что выведет код?

<details>
<summary>Решение</summary>
  
```python
a = "2"
b = "6"
a,b = b,a
print(a, '-' ,  b)
# 6 - 2

a = "2"
b = "6"
a = b  
b = a
print(a, '-' ,  b)
# 6 - 6

values = (9, 11, 96, 130)
result = tuple(filter(lambda x: x % 2 == 0, values))
print(result)
# (96, 130)

value = "1234"
result = sum(map(int, value))
print(result)
# 10

values = [1, 2, 5, 2, 5, 5, 3]
result = max(set(values), key=values.count)
print(result)
#set(values) убирает дубликаты:{1, 2, 3, 5}
#values.count: Для каждого элемента max() будет считать, сколько раз он встречается в исходном списке
#max(..., key=values.count). max() ищет элемент с максимальным результатом функции values.count.
# 1 → 1
# 2 → 2
# 3 → 1
# 5 → 3  ← максимум
# Ответ 5

items = [[1, 2], [3]]
items[1].append(4)
print(items)
# [[1, 2], [3, 4]]
```

</details>

