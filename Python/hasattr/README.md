`hasattr()` — это встроенная функция Python, которая проверяет, есть ли у объекта определённый атрибут.

```python
hasattr(объект, "имя_атрибута")

#Результат:True или False
```

```python
class User:
    pass


user = User()
print("1:", hasattr(user, "name"))

user.name = "Евгений"
print("2:", hasattr(user, "name"))

print("Имя:", user.name)

#Результат
#1: False
#2: True
#Имя: Евгений
```

```text
hasattr(user, "name")
        │
        ├── False → такого атрибута нет
        │
        └── True  → такой атрибут есть
```

Важный момент: `hasattr()` проверяет именно атрибут объекта, а не обычную переменную. Например, в `user.name` — `name` является атрибутом объекта `user`.
