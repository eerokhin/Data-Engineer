# Банк задач для собеседований по python

В этом разделе собраны практические задачи, которые часто встречаются на собеседованиях.

---

### Задача с собеседования в ВТБ

<details>
<summary>Задача</summary>

Что выведет код?

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

### Задача с собеседования в банк

<details>
<summary>Задача</summary>
  
Добавление элементов в список

**Условие**

Реализовать функцию `add_element`, которая добавляет один или несколько элементов в список.

**Функция принимает:**

• `new_element` - строку или список строк;

• `init_sequence` - исходный список, необязательный параметр.

**Правила работы:**

• Если `new_element` является строкой, добавить её с помощью `append()`.

• Если передан список строк, добавить все элементы с помощью `extend()`.

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

**Решение**

```python
def add_element(new_element, init_sequence=None):
    '''
    isinstance()  # проверяем тип
    all()         # проверяем все элементы
    append()      # добавляем один элемент
    extend()      # добавляем несколько элементов
    '''
    
    if init_sequence is None:
        init_sequence = []

    if isinstance(new_element, str):
        init_sequence.append(new_element)

    elif isinstance(new_element, list) and all(isinstance(x, str) for x in new_element):
        init_sequence.extend(new_element)

    return init_sequence

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
</details>

### Задача с собеседования на 350к

<details>
<summary>Задача</summary>

Поиск `n-го` параграфа в текстовом файле. Есть файл `/file_with_paragraphs.txt` с текстом, разбитым на параграфы. 
Каждый параграф состоит из одной или нескольких строк. Параграфы разделены строкой, состоящей только из специальных символов `@`.
Требуется написать функцию, которая печатает `n-й` по счёту параграф. Параметр `n` - положительное целое число.

Пример содержимого файла:

```text
Первый параграф.
Он может занимать несколько строк.
@@@
Второй параграф.
Он тоже может состоять из нескольких строк.
@@@
Третий параграф.
```

**Решение**

```python  
def par_search(file_path: str, n: int) -> None:
    if n <= 0:
        raise ValueError("n должно быть положительным числом")
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    paragraphs = content.split("@@@") # Разбивает текст на список параграфов по разделителю @@@
    if n > len(paragraphs):
        raise IndexError("Параграф не найден")
    print(paragraphs[n - 1].strip()) # Убирает пробельные символы в начале и конце параграфа

file_path = "C:/Users/erohi/Desktop/test/example.txt"
par_search(file_path, 1)
```
</details>

### Задача на словарь

<details>
<summary>Задача</summary>

**Условие**

Есть список заказов:

```python
orders = [
          {"order_id": 1, "customer_id": 101, "amount": 500},
          {"order_id": 2, "customer_id": 102, "amount": 1200},
          {"order_id": 3, "customer_id": 101, "amount": 800},
          {"order_id": 4, "customer_id": 103, "amount": 300},
          {"order_id": 5, "customer_id": 102, "amount": 700},
          {"order_id": 6, "customer_id": 101, "amount": 400},
          ]
```

Задание: напиши функцию, которая считает общую сумму заказов для каждого клиента.

Ожидаемый результат: `{101: 1700, 102: 1900, 103: 300}`

Ограничения:
- Используй стандартный Python.
- Не используй pandas.
- Используй словарь и цикл.
- Решение оформи в виде функции.

Дополнительный вопрос: что вернёт функция, если список заказов будет пустым?

**Решение**

```python
def my_func(orders):
    result = {}

    for order in orders:
        customer_id = order["customer_id"]
        amount = order["amount"]

        if customer_id in result:
            result[customer_id] += amount
        else:
            result[customer_id] = amount

    return result
```
  
</details>
