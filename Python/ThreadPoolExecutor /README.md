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

Проблема: Потоки делят память. Когда несколько потоков одновременно меняют одну переменную без защиты - может быть хаос, результат непредсказуем (race condition).

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

Посмотрим: пять потоков увеличивают счётчик по миллиону раз каждый, значит должно получиться `5 000 000`.

```python
import threading

counter = 0

def increment():
    global counter
    for _ in range(1_000_000):
        counter += 1

threads = [threading.Thread(target=increment) for _ in range(5)] # Создай 5 потоков, каждый из которых при запуске будет выполнять increment
for t in threads:
    t.start()
for t in threads:
    t.join()

print(counter)        # например 3137095 — и при каждом запуске другое число
```

Ждали `5 000 000`, а получили меньше — и в следующий раз число будет другим. Дело в том, что `counter += 1` не одно действие, а три (прочитать значение, прибавить единицу, записать обратно), и потоки успевают влезть между шагами, затирая чужие инкременты. Защита — `Lock`: пока один поток внутри `with lock`, остальные ждут своей очереди.

```python
import threading

counter = 0
lock = threading.Lock()

def increment():
    global counter
    for _ in range(1_000_000):
        with lock:                # автоматический acquire/release
            counter += 1

threads = [threading.Thread(target=increment) for _ in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(counter)        # 5000000 — теперь всегда верно
```

`with lock`: — стандартный способ работы: он гарантирует освобождение блокировки даже при исключении. Кроме `Lock` в `threading` есть `Event`, `Semaphore`, `Condition`, `RLock`. На практике в `90%` случаев хватает `Lock` и `Queue` (см. ниже). Остальное нужно для нетривиальной координации.

## threading.Thread (ручной поток)

`threading.Thread` нужен, когда нужно разные задачи выполнять одновременно.

Создаём поток через `threading.Thread`, передавая ему функцию-цель и аргументы.

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

```python
import threading
import time

def work():
    time.sleep(2)
    print("Поток закончил работу")

t = threading.Thread(target=work)

# start() - ЗАПУСКАЕТ поток
t.start()
print("Поток запущен!")

# join() - ЖДЕТ завершения потока
t.join()
print("Поток завершен, продолжаем программу")

#Поток запущен!
#Поток закончил работу  (через 2 секунды)
#Поток завершен, продолжаем программу
```

```python
import threading
import time

def worker(name, sleep_time):
    print(f"Поток {name}: засыпаю на {sleep_time} с")
    time.sleep(sleep_time)
    print(f"Поток {name}: завершён")

t1 = threading.Thread(target=worker, args=("A", 2))
t2 = threading.Thread(target=worker, args=("B", 1))

t1.start()                # запускаем
t2.start()
t1.join()                 # ждём завершения
t2.join()
print("Все потоки завершены")
```

Если запустить, увидим примерно такой вывод:

```text
Поток A: засыпаю на 2 с
Поток B: засыпаю на 1 с
Поток B: завершён
Поток A: завершён
Все потоки завершены
```

Поток `B` стартовал вторым, но завершился первым — его `sleep` короче, и `t1.join()` ждёт именно завершения `A`. Это и есть конкурентное выполнение: потоки идут одновременно, порядок завершения определяется их работой, а не порядком запуска.

`target` — функция, которую выполняет поток.

`args` — кортеж аргументов.

`start()` - Запускает поток. Поток начинает выполняться.

`join()` - Подождать, пока закончит. Останавливает основную программу и ждет, пока поток не завершится.

## threading.local (свои данные для каждого потока)

`threading.local()` нужен, когда у нас много потоков, но каждому потоку нужно хранить **свои собственные данные**, которые не должны смешиваться с данными других потоков.

**Аналогия:** Есть 3 грузчика (потока). У каждого есть свой личный шкафчик. Они могут положить в него вещи с одинаковым названием, но вещи находятся в разных шкафчиках.

```text
thread_local
│
├── Поток 1 → свои данные
├── Поток 2 → свои данные
└── Поток 3 → свои данные
```

**Синтаксис**

```python
import threading

# Создаем хранилище для данных потоков
thread_local = threading.local()

def worker(name):
    # Каждый поток получает свое значение
    thread_local.name = name

    print(thread_local.name)
```

`threading.local()` → создает специальное хранилище, где у каждого потока свои значения

`thread_local.name = ...` → записывает значение для текущего потока

`thread_local.name` → получает значение текущего потока

**Пример без `threading.local()`:**

```python
import threading
import time

name = None

def worker(my_name):

    global name

    # Все потоки записывают значение в ОДНУ переменную
    name = my_name

    time.sleep(1)

    print(f"{my_name} видит: {name}")


threads = []

for person in ["Вася", "Петя", "Коля"]:

    thread = threading.Thread(
        target=worker,
        args=(person,)
    )

    threads.append(thread)
    thread.start()


for thread in threads:
    thread.join()
```

Результат может быть:

```text
Вася видит: Коля
Петя видит: Коля
Коля видит: Коля
```

Почему?

Потому что `name` — **одна общая переменная для всех потоков**.

```text
                 name
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
    Поток 1     Поток 2    Поток 3
       │          │          │
       └──────────┼──────────┘
                  │
            одно общее значение
```

Например:

```text
Поток 1 → name = "Вася"
Поток 2 → name = "Петя"
Поток 3 → name = "Коля"
```

Последний поток перезаписал значение:

```text
name = "Коля"
```

Поэтому другие потоки могут увидеть `"Коля"`.

**Пример с `threading.local()`:**

```python
import threading
import time

thread_local = threading.local()

def worker(name):

    # Каждый поток получает свое значение
    thread_local.name = name

    time.sleep(1)

    # Каждый поток увидит свое значение
    print(f"{name} видит: {thread_local.name}")


threads = []

for name in ["Вася", "Петя", "Коля"]:

    thread = threading.Thread(
        target=worker,
        args=(name,)
    )

    threads.append(thread)
    thread.start()


for thread in threads:
    thread.join()
```

Результат:

```text
Вася видит: Вася
Петя видит: Петя
Коля видит: Коля
```

У каждого потока свое значение:

```text
Поток Вася → thread_local.name = "Вася"

Поток Петя → thread_local.name = "Петя"

Поток Коля → thread_local.name = "Коля"
```

```text
thread_local - Создаёт специальное хранилище. У каждого потока своё отдельное значение. 

          thread_local
               │
       ┌───────┼───────┐
       │       │       │
       ▼       ▼       ▼
     Вася    Петя     Коля
       │       │       │
       ▼       ▼       ▼
     "Вася"  "Петя"  "Коля"

     
thread_local
     │
     ├── Поток Вася → "Вася"
     │
     ├── Поток Петя → "Петя"
     │
     └── Поток Коля → "Коля"
```

В отличие от обычной переменной:

```python
name = None
```

которая была бы **одной общей для всех потоков**.

`threading.local()` → дает каждому потоку свое отдельное хранилище данных

`thread_local.name` → значение `name`, принадлежащее текущему потоку

**Частый пример:** хранить отдельный `requests.Session()` для каждого потока.

```python
import threading
import requests

thread_local = threading.local()

def get_session():

    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()

    return thread_local.session
```

Здесь каждый поток при первом вызове `get_session()` создает свою `Session`:

```text
Поток 1 → thread_local.session → Session №1

Поток 2 → thread_local.session → Session №2

Поток 3 → thread_local.session → Session №3
```

`hasattr(thread_local, "session")` → проверяет, есть ли у текущего потока уже своя `session`

`thread_local.session = requests.Session()` → создает `session` именно для текущего потока

`return thread_local.session` → возвращает `session` текущего потока


