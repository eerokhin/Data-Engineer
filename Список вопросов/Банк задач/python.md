# Банк задач для собеседований по python

В этом разделе собраны практические задачи, которые часто встречаются на собеседованиях.

---

## Задача с собеседования в ВТБ

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

---

## Задача с собеседования в банк

Добавление элементов в список

**Условие**

Реализовать функцию `add_element`, которая добавляет один или несколько элементов в список.

**Функция принимает:**

• new_element - строку или список строк;
• init_sequence - исходный список, необязательный параметр.

**Правила работы:**

• Если new_element является строкой, добавить её с помощью append().
• Если передан список строк, добавить все элементы с помощью extend().
• Если исходный список не передан, создать новый пустой список.
• Вернуть получившийся список.

**Примеры использования**

```python
sequence_1 = add_element("first")
print(sequence_1)
# ['first']

sequence_2 = add_element(["second", "third"], sequence_1)
print(sequence_2)
# ['first', 'second', 'third']

sequence_3 = add_element(["fourth"], sequence_2)
print(sequence_3)
# ['first', 'second', 'third', 'fourth']
```

<details>
<summary>Решение</summary>
  
```python

```

</details>
