## ThreadPoolExecutor (параллельные задачи)

**Аналогия:** Есть 5 грузчиков (потоков) и 100 коробок (задач). Даем каждому грузчику по коробке, они работают параллельно. Как только один освободился - берет следующую коробку.

**Синтаксис**

```python
from concurrent.futures import ThreadPoolExecutor

# Шаг 1: Создаем пул с 3 рабочими
with ThreadPoolExecutor(max_workers=5) as executor:
    # Шаг 2: Отправляем задачи
    future = executor.submit(функция, аргумент1, аргумент2)
    result = future.result()
```

`ThreadPoolExecutor(max_workers=5)` → создает 5 свободных рабочих

`executor.submit()` → отправляет задачу свободному рабочему

`future` → "обещание" что результат будет

`future.result()` → ждет и возвращает результат



```python
from concurrent.futures import ThreadPoolExecutor

def my_function(name):
    return f"Привет, {name}"

# 1. СОЗДАЕМ ПУЛ
with ThreadPoolExecutor(max_workers=3) as executor:
    # 2. ОТПРАВЛЯЕМ ЗАДАЧИ
    future1 = executor.submit(my_function, "Анна")   # запустили
    future2 = executor.submit(my_function, "Иван")   # запустили
    future3 = executor.submit(my_function, "Петр")   # запустили
    
    # 3. ПОЛУЧАЕМ РЕЗУЛЬТАТЫ
    result1 = future1.result()  # ждем результат
    result2 = future2.result()
    result3 = future3.result()
    
    print(result1, result2, result3)
```

`future` - это "обещание" что результат будет. Как заказ в ресторане: вы сделали заказ (`submit`), получили номерок (`future`), а когда блюдо готово - забираете (`result`).


```python
from concurrent.futures import ThreadPoolExecutor

def work(x):
    return x * 2

with ThreadPoolExecutor(max_workers=3) as executor:
    results = [executor.submit(work, i).result() for i in range(5)]
```

## threading.Lock (защита счетчика)

**Блокировки - зачем они?**

Проблема: Когда несколько потоков одновременно меняют одну переменную - может быть хаос.

```python
import threading

counter = 0
lock = threading.Lock()

def increment():
    global counter
    with lock:
        counter += 1
```

```python
from concurrent.futures import ThreadPoolExecutor
import threading

counter = 0
lock = threading.Lock()

def process(x):
    global counter
    with lock:
        counter += 1
    return x * 2

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(process, i) for i in range(10)]
    results = [f.result() for f in futures]

print(counter)  # 10
```

`ThreadPoolExecutor` → запускает много задач одновременно

`Lock` → защищает общую переменную от одновременного изменения

## threading.Thread (ручной поток)

`threading.Thread` нужен, когда нужно разные задачи выполнять одновременно

**Пример 1:** Скачивание файлов + прогресс-бар

```python
import threading
import time

def download_file():
    print("Начинаю скачивание...")
    time.sleep(5)
    print("Скачивание завершено!")

def show_progress():
    for i in range(5):
        time.sleep(1)
        print(f"Загрузка... {i+1} секунд")

# Запускаем две РАЗНЫЕ задачи одновременно
threading.Thread(target=download_file).start()
threading.Thread(target=show_progress).start()

```

Без `threading.Thread` пришлось бы ждать скачивание 5 секунд, а потом показывать прогресс. А так - всё одновременно.

`start()` - Запустить

`join()` - Подождать, пока закончит
