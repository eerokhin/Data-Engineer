- [Параллельное и асинхронное программирование](#параллельное-и-асинхронное-программирование)
    - [Конкурентность, параллелизм, асинхронность в Python](#конкурентность-параллелизм-асинхронность-в-python)
    - [Три понятия](#Три-понятия)
    - [I/O-bound vs CPU-bound: ключевая дихотомия](#io-bound-vs-cpu-bound-ключевая-дихотомия)
    - [GIL: почему threading не помогает с CPU](#GIL-почему-threading-не-помогает-с-CPU)
    - [Какой инструмент когда](#Какой-инструмент-когда)

# Параллельное и асинхронное программирование

## Конкурентность, параллелизм, асинхронность в Python

Допустим, наша программа должна скачать 100 страниц с разных сайтов. Если делать по очереди — каждый запрос ждёт ответа сервера 1-2 секунды, и общее время это сумма всех ожиданий. Большую часть этого времени процессор простаивает. Решение очевидно: пока один запрос ждёт ответа, можно отправлять другие. Это и есть конкурентное выполнение.

В Python три инструмента для этого: `threading`, `multiprocessing`, `asyncio`. Эта статья — карта: какой и когда брать.

Сначала посмотрим на проблему вживую. Три «скачивания» по очереди, каждое ждёт полсекунды:

```python
import time

def download(url):
    time.sleep(0.5)          # имитация ожидания ответа сервера
    return f"данные с {url}"

start = time.time()
for url in ["site-1", "site-2", "site-3"]:
    print(download(url))

print(f"Ушло {time.time() - start:.1f} с")
```

Три запроса — полторы секунды, и процессор всё это время не делал ничего, просто ждал ответа. Дальше три разных способа уложить те же запросы в полсекунды.

## Три понятия

В разговорах о конкурентности постоянно мешают три похожих слова. Различие важное:

- Конкурентность (`concurrency`): задачи могут переключаться между собой, создавая иллюзию одновременной работы. Один бариста за стойкой принимает заказ, ставит молоко греться, переходит к следующему клиенту, возвращается к молоку. Один исполнитель, несколько задач «в воздухе» одновременно.

- Параллелизм (`parallelism`): задачи выполняются физически одновременно на разных ядрах процессора. Несколько бариста, каждый делает свой кофе. Требует многоядерности.

- Асинхронность (`asynchronicity`): способ организации кода, при котором задача может «отложиться» в ожидании (например, ответа сервера), не блокируя весь поток. Это способ достижения конкурентности на одном потоке, без переключения ОС.

Конкурентность это цель, параллелизм и асинхронность — два способа её достичь.

<img width="775" height="347" alt="image" src="https://github.com/user-attachments/assets/b6f07482-75f4-46d6-9938-6f3cb79d3d12" />

## I/O-bound vs CPU-bound: ключевая дихотомия

Выбор инструмента зависит только от того, чего ждёт ваша задача:

- `I/O-bound`: процессор простаивает в ожидании внешнего ресурса. Сетевой запрос, чтение с диска, ответ БД. Здесь побеждает асинхронность — пока один запрос ждёт, отправляем следующие.

- `CPU-bound`: процессор честно работает над вычислениями. Сжатие изображения, шифрование, научные вычисления. Здесь нужен реальный параллелизм на нескольких ядрах.

Самая частая ошибка новичка: брать `multiprocessing` для скачивания страниц или `asyncio` для перемножения матриц. Это даст замедление, не ускорение.

## GIL: почему threading не помогает с CPU

В стандартной реализации Python (`CPython`) есть `Global Interpreter Lock (GIL)` — глобальный замок, который разрешает выполнять Python-код только одному потоку за раз внутри процесса. Даже если у вас 8 ядер, потоки выполняются по очереди.

Что из этого следует:

- Для `CPU-bound` задач `threading` бесполезен — потоки делят одно ядро через `GIL`. Нужны процессы (`multiprocessing`), у каждого свой `GIL` и своё ядро.

- Для `I/O-bound` задач `GIL` отпускается при ожидании сети/диска. Поэтому `threading` отлично подходит для `I/O`, как и `asyncio` (но без накладных расходов на потоки).

## Какой инструмент когда

```text
Задача	                                                Инструмент
Множество сетевых запросов, тысячи соединений	        asyncio
I/O в legacy-коде без async-библиотек	                threading
Тяжёлые вычисления на нескольких ядрах	                multiprocessing
Простое распараллеливание без погружения в детали	    concurrent.futures (ThreadPoolExecutor / ProcessPoolExecutor)
```

Поток это легковесный исполнитель внутри одного процесса (для I/O), процесс это отдельная программа с собственной памятью (для CPU-bound).

# Потоки и процессы

## Потоки и процессы в Python

Восемь тяжёлых вычислений через `ThreadPoolExecutor` считаются секунд двенадцать. Меняете в нём одно слово, `Thread` на `Process`, и те же восемь укладываются в три-четыре. В этом зазоре и живёт вся разница между потоками и процессами.

Расклад следующий: потоки (`threading`) для `I/O`, процессы (`multiprocessing`) для вычислений. Здесь разберём оба модуля. API у них почти одинаковый: выучили один — считайте, что выучили оба.

<img width="725" height="350" alt="image" src="https://github.com/user-attachments/assets/9786cdec-b25f-419d-a85a-bfd7a5ad4b14" />

## threading.Thread (ручной поток) потоки внутри одного процесса

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

## Обмен данными между потоками: `queue.Queue`

Менять общие переменные напрямую опасно: приходится расставлять `Lock` везде. Чище и безопаснее передавать данные через потокобезопасную очередь из модуля `queue`:

```python
import threading
import queue
import time

q = queue.Queue()

def producer():
    for i in range(5):
        q.put(f"item-{i}")
        time.sleep(0.1)
    q.put(None)               # сигнал «больше не будет»

def consumer():
    while True:
        item = q.get()
        if item is None:
            break
        print(f"Получил {item}")

t_prod = threading.Thread(target=producer)
t_cons = threading.Thread(target=consumer)
t_prod.start()
t_cons.start()
t_prod.join()
t_cons.join()
```

`q.put()` блокируется если очередь переполнена (для ограниченных), `q.get()` блокируется если пуста. Внутри уже есть все нужные блокировки.

`q.put(None)` в конце `producer-а` это соглашение между `producer` и `consumer`: «данных больше не будет». В `Queue` нет встроенного сигнала «конец потока», поэтому договариваются вручную, и `None` это просто наиболее частый выбор. Можно использовать любое значение, которое не может прийти как валидные данные.

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

## `multiprocessing`: настоящий параллелизм

API почти идентичен `threading`, но вместо потоков создаются отдельные процессы. Каждый со своим интерпретатором, своей памятью, своим GIL. Несколько процессов реально работают одновременно на разных ядрах.

```python
import multiprocessing
import time

def heavy_calc(n):
    print(f"Процесс считает для n={n}")
    total = sum(i * i for i in range(n))
    return total

if __name__ == "__main__":                     # обязательная защита
    p1 = multiprocessing.Process(target=heavy_calc, args=(10_000_000,))
    p2 = multiprocessing.Process(target=heavy_calc, args=(10_000_000,))

    p1.start()
    p2.start()
    p1.join()
    p2.join()
    print("Оба процесса завершились")
```

`if __name__ == "__main__"`: обязательна на Windows и macOS. Без неё дочерние процессы будут пытаться запустить весь модуль заново и упадут в бесконечную рекурсию создания процессов. Привыкайте сразу.

## Обмен данными между процессами: `Queue`

Процессы изолированы: у каждого своя память, общие переменные не работают. Передача данных идёт через специальный механизм. Самый удобный это `multiprocessing.Queue` с тем же API, что и `queue.Queue`:

```python
import multiprocessing

def producer(q):
    for i in range(3):
        q.put(f"item-{i}")
    q.put(None)

def consumer(q):
    while True:
        item = q.get()
        if item is None:
            break
        print(f"Получил {item}")

if __name__ == "__main__":
    q = multiprocessing.Queue()
    p1 = multiprocessing.Process(target=producer, args=(q,))
    p2 = multiprocessing.Process(target=consumer, args=(q,))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
```

Кроме `Queue` есть `Pipe` (для двух процессов), `Value/Array` (общие примитивные данные) и `Manager` (общие списки/словари через серверный процесс). Это всё нужно редко: `Queue + Pool` (ниже) покрывают большинство случаев.

## Пул процессов для CPU-bound задач

Создавать процессы вручную для каждой задачи накладно. `multiprocessing.Pool` создаёт пул из `N` процессов и распределяет между ними задачи:

```python
import multiprocessing

def heavy_square(x):
    # имитация тяжёлых вычислений, нагружающих CPU
    return sum(i * i for i in range(x * 100_000))

if __name__ == "__main__":
    with multiprocessing.Pool(processes=4) as pool:
        results = pool.map(heavy_square, range(1, 9))
    print(results)
```

`pool.map(func, items)` применяет функцию к каждому элементу из `items`, распределяя работу между процессами в пуле. Контекстный менеджер сам закроет пул и дождётся всех процессов.

## concurrent.futures: одинаковый API для потоков и процессов. ThreadPoolExecutor (параллельные задачи)

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

Модуль `concurrent.futures` даёт высокоуровневую обёртку над обоими подходами. Один и тот же код работает и с потоками, и с процессами, меняется только класс `executor`:

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

def task(x):
    return x * x

# if __name__ нужен из-за ProcessPoolExecutor: он запускает процессы
if __name__ == "__main__":
    # Для I/O-bound: потоки
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(task, range(10)))

    # Для CPU-bound: процессы — меняется только класс executor
    with ProcessPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(task, range(10)))
```

Это самый практичный способ распараллелить простые задачи. На современных проектах `concurrent.futures` встречается чаще, чем прямые `threading.Thread` или `multiprocessing.Process`.


## Когда что брать
```text
Задача	                                                      Инструмент
Простые I/O-bound в существующем синхронном коде	          ThreadPoolExecutor
Когда нужно вручную управлять состоянием (Lock, Queue)	      threading напрямую
CPU-bound вычисления	                                      ProcessPoolExecutor или multiprocessing.Pool
Тысячи сетевых соединений	                                  asyncio
```

`asyncio` лучше для `I/O-bound` на больших объёмах: один поток, минимальные накладные расходы на переключение. Но требует переписать код в `async-стиле`.

# Асинхронное програмирование

## Основы asyncio в Python

Три «скачивания» из вводной статьи заняли полторы секунды — и почти всё это время процессор просто ждал ответа сервера. Потоки и процессы решали это, поручая переключение операционной системе. asyncio идёт иначе: один поток и кооперативная многозадачность. Пока один запрос ждёт сервер, тот же поток сам берётся за следующий, а места, где задачу можно «отложить», программа помечает ключевым словом await.

Для I/O-bound нагрузок asyncio даёт лучшее соотношение производительности и ресурсов: тысячи одновременных соединений на одном потоке без накладных расходов на потоки ОС.

## Цикл событий и кооперативная модель

Сердце asyncio — event loop (цикл событий). Он держит список задач, выполняет одну из них, и когда задача доходит до await something_slow(), задача «уступает управление», event loop переключается на следующую готовую задачу. Когда something_slow() завершается, исходная задача снова становится готовой.

<img width="523" height="368" alt="image" src="https://github.com/user-attachments/assets/d78baf51-001c-413d-a9a6-ba6740a9ef45" />

Важно: переключение происходит только на await. Никаких прерываний посередине вычисления. Это «кооперативная» многозадачность: задачи договариваются, когда уступать. У такого подхода есть последствие: если задача не делает await (например, считает что-то долго на CPU), весь event loop стоит.

## async и await

В Python 3.5 появились ключевые слова для асинхронности:

- async def — определяет корутину (асинхронную функцию)

- await — внутри корутины: «дождись завершения этой операции, на время ожидания отпусти управление»

```python
import asyncio

async def say_hello():
    print("Привет...")
    await asyncio.sleep(1)        # не блокирует поток, отпускает event loop
    print("...мир")
```

Важный нюанс: вызов say_hello() не запускает корутину. Он создаёт объект-корутину:

```python
coro = say_hello()
print(type(coro))     # <class 'coroutine'>
# код корутины ещё не выполнен!
```

Чтобы запустить корутину, нужен event loop.

## asyncio.run: точка входа

asyncio.run() запускает event loop, выполняет переданную корутину и закрывает loop:

```python
import asyncio

async def main():
    print("Запуск")
    await asyncio.sleep(1)
    print("Завершено через 1 секунду")

asyncio.run(main())
```

asyncio.run() — стандартный способ запустить async-программу из обычного синхронного кода. Внутри одной программы вызывается один раз на верхнем уровне.

## Последовательно vs конкурентно

Если просто пишем await подряд, корутины выполняются последовательно, одна за другой:

```python
import asyncio
import time

async def slow_task(name, delay):
    await asyncio.sleep(delay)
    print(f"{name} готова за {delay}с")

async def main():
    start = time.time()
    await slow_task("A", 2)
    await slow_task("B", 1)
    await slow_task("C", 3)
    print(f"Всего: {time.time() - start:.1f}с")    # ~6с

asyncio.run(main())
```

Все три задачи могли бы идти параллельно (они только ждут), но мы заставили их идти по очереди: await ждёт завершения текущей. Чтобы запустить конкурентно, используем asyncio.gather():

```python
async def main():
    start = time.time()
    await asyncio.gather(
        slow_task("A", 2),
        slow_task("B", 1),
        slow_task("C", 3),
    )
    print(f"Всего: {time.time() - start:.1f}с")    # ~3с

asyncio.run(main())
```

gather() запускает все переданные корутины конкурентно и возвращает список результатов. Общее время равно самой долгой задаче, а не сумме всех. Это и есть суть asyncio для I/O.

## Tasks: запуск корутин «в фоне»

Иногда нужно запустить корутину «прямо сейчас», не дожидаясь её, чтобы она работала параллельно с основной логикой. Для этого есть asyncio.create_task():

```python
import asyncio

async def background_log():
    while True:
        print("heartbeat")
        await asyncio.sleep(1)

async def main():
    task = asyncio.create_task(background_log())
    await asyncio.sleep(3)      # делаем что-то другое
    task.cancel()               # остановили фоновую корутину

asyncio.run(main())
```

create_task() сразу планирует корутину к выполнению. Возвращает объект Task, у которого есть методы cancel(), done(), result(). По сути Task — это корутина, которую event loop уже запустил и отслеживает: можно проверить статус, забрать результат или отменить её.

##Главные правила

- Внутри async def любое долгое ожидание — через await. Обычный time.sleep(1) заблокирует весь event loop. Используйте await asyncio.sleep(1).

- Хочется конкурентно — asyncio.gather() или asyncio.create_task(). Просто await подряд = последовательно.

- CPU-bound в asyncio останавливает всё. Считаете долго? Выносите в run_in_executor (следующая статья) или в multiprocessing.

Далее — продвинутые техники asyncio: очереди, синхронизация между корутинами и (главное) как запускать блокирующий код, не убивая event loop.

# Продвинутое асинхронное програмирование

## Продвинутый asyncio в Python

Асинхронный сервис держал тысячи соединений и вдруг замер весь, для всех разом. Причина в одной строке: кто-то вызвал синхронную requests.get(), и она на секунду заблокировала единственный поток event loop, а с ним и все остальные корутины.

Базовых средств asyncio из прошлой статьи (async def, await, gather, Tasks) здесь недостаточно. Для реальных приложений нужны ещё три инструмента: очереди между корутинами, синхронизация и, главное, запуск блокирующего кода без остановки event loop.

## asyncio.Queue: обмен данными между корутинами

В asyncio все корутины работают в одном потоке и в принципе могут делиться состоянием напрямую. Но для производитель-потребитель паттерна удобнее очередь:

```python
import asyncio

async def producer(q):
    for i in range(5):
        await q.put(f"item-{i}")
        await asyncio.sleep(0.1)
    await q.put(None)            # сигнал остановки

async def consumer(q):
    while True:
        item = await q.get()
        if item is None:
            break
        print(f"Получил {item}")

async def main():
    q = asyncio.Queue()
    await asyncio.gather(producer(q), consumer(q))

asyncio.run(main())
```

API такой же, как у queue.Queue, но методы здесь корутины (await q.put, await q.get). Очередь блокирует на пустом get() или переполненном put() (если задан maxsize), но не сам поток — она уступает управление event loop.

## asyncio.Lock: защита общего состояния

В asyncio переключение корутин происходит только на await. Если между двумя await есть критическая секция (где меняется общее состояние), переключение туда не вклинится. Но если внутри критической секции есть await, другая корутина может вмешаться.

```python
import asyncio

counter = 0
lock = asyncio.Lock()

async def increment():
    global counter
    async with lock:
        current = counter
        await asyncio.sleep(0.01)     # await ВНУТРИ критической секции
        counter = current + 1

async def main():
    await asyncio.gather(*(increment() for _ in range(100)))
    print(counter)        # 100 — корректно благодаря lock

asyncio.run(main())
```

Без lock несколько корутин прочитали бы одно и то же значение current, и итог был бы меньше 100. С async with lock: только одна корутина может находиться в критической секции одновременно.

В реальном asyncio-коде блокировки нужны редко, потому что большинство переменных живут внутри одной корутины. Lock пригодится, когда несколько корутин читают/пишут одну общую структуру или ресурс — например, общий счётчик активных подключений или кэш.

Кроме Lock есть asyncio.Event, asyncio.Semaphore, asyncio.Condition (API копирует threading, но операции через await).

## Блокирующий код в asyncio: run_in_executor

Вернёмся к аварии из начала главы. Правило, которое там нарушили: в event loop нельзя вызывать блокирующие функции напрямую. time.sleep(2), requests.get(), тяжёлый расчёт останавливают его целиком.

Но иногда деваться некуда: нужна старая синхронная библиотека или CPU-bound расчёт. На этот случай есть loop.run_in_executor(): запустить блокирующую функцию в отдельном потоке (или процессе), пока event loop спокойно продолжает работу.

<img width="775" height="376" alt="image" src="https://github.com/user-attachments/assets/5a8f432a-a2b9-4a41-8cd7-786455031339" />

```python
import asyncio
import time

def blocking_io():
    print("Блокирующая функция: засыпаю на 2с")
    time.sleep(2)                    # синхронный sleep
    return "готово"

async def main():
    loop = asyncio.get_running_loop()
    print("Запускаем блокирующую задачу в executor")

    # None = executor по умолчанию (ThreadPoolExecutor)
    future = loop.run_in_executor(None, blocking_io)

    # пока блокирующая задача работает, event loop свободен
    await asyncio.sleep(1)
    print("Event loop работает параллельно")

    result = await future
    print(f"Результат: {result}")

asyncio.run(main())
```

run_in_executor(None, func, *args) отдаёт func(*args) в стандартный ThreadPoolExecutor (тот самый, что мы видели в статье про потоки и процессы) и возвращает future, который можно await-ить.

Для CPU-bound кода можно передать ProcessPoolExecutor первым аргументом — функция уйдёт в отдельный процесс с собственным GIL.

## async-итерация и контекстные менеджеры

Если объект собирает данные постепенно (через сеть, например), он может быть асинхронным итератором: итерируется через async for:

```python
async for line in aiohttp_response:
    process(line)
```

Если ресурс надо открыть и закрыть асинхронно (соединение с БД), это асинхронный контекстный менеджер через async with:

```python
async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
        data = await response.json()
```

Сами вы их пишете редко, это инструменты библиотек (aiohttp, asyncpg, aioredis). Достаточно знать, что они существуют и узнавать async for / async with в чужом коде.

## Сравнение трёх подходов

```text
                    threading	                multiprocessing	                    asyncio
Параллелизм CPU	    нет (GIL)	                да	                                нет (1 поток)
I/O-bound	        хорошо	                    хорошо, но дорого	                отлично
Накладные расходы	низкие	                    высокие	                            минимальные
Память	            общая	                    изолированная	                    общая (1 поток)
Обмен данными	    переменные + Lock / Queue	Queue, Pipe, Manager	            переменные / asyncio.Queue
Тысячи задач	    плохо	                    очень плохо	                        прекрасно
```

## Правило выбора:

- Тысячи сетевых соединений, новые проекты → asyncio

- I/O в существующем синхронном коде без async-библиотек → threading или ThreadPoolExecutor

- Тяжёлые вычисления → multiprocessing или ProcessPoolExecutor

- В одном приложении часто всё это сочетается: asyncio как основной слой + run_in_executor с пулом потоков/процессов для блокирующих кусков.

## Несколько подводных камней

- CPU-bound в asyncio убивает event loop. Используйте run_in_executor с ProcessPoolExecutor для тяжёлых вычислений в async-коде.

- Забытая await: asyncio.sleep(1) без await ничего не делает (создаёт корутину и выбрасывает её). В современных IDE это подсвечивается.

- Mix sync/async: вызов requests.get() (синхронный) в asyncio блокирует всё. Используйте aiohttp / httpx для async-HTTP.

- if __name__ == "__main__": на Windows и macOS обязательна для multiprocessing, иначе процессы будут рекурсивно создавать сами себя.

На этом модуль конкурентности завершён. Карта из вводной статьи и матрица выше уже отвечают на вопрос «что брать», а на практике основная программа чаще всего живёт на asyncio, отдавая CPU-тяжёлые куски в process pool через run_in_executor.
