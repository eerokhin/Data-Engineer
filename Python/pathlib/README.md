# `Path(__file__).resolve().parent` в Python

`Path(__file__).resolve().parent` — выражение, которое возвращает абсолютный путь к директории, в которой находится текущий Python-файл.

## 1. Разбор по частям

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
```

| Элемент | Что делает | Пример результата |
|---|---|---|
| `Path(__file__)` | Создаёт объект пути к текущему файлу | `dags/my_dag.py` |
| `.resolve()` | Получает абсолютный путь, разрешая символические ссылки | `/home/airflow/project/dags/my_dag.py` |
| `.parent` | Возвращает родительскую директорию файла | `/home/airflow/project/dags` |

## 2. Пример структуры проекта

```text
my_project/
├── dags/
│   ├── my_dag.py
│   └── query.sql
└── README.md
```

В файле `my_dag.py`:

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

print(BASE_DIR)
```

Результат:

```text
/home/airflow/my_project/dags
```

**Важно:** `BASE_DIR` указывает на папку `dags`, а не на корень проекта.

## 3. Как получить путь к другому файлу

Допустим, необходимо прочитать SQL-запрос из файла `query.sql`, расположенного рядом с DAG.

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

sql_path = BASE_DIR / "query.sql"

with open(sql_path, encoding="utf-8") as file:
    sql = file.read()
```

Оператор `/` используется объектами `Path` для соединения частей пути.

Например:

```python
BASE_DIR / "sql" / "query.sql"
```

Результат:

```text
/home/airflow/my_project/dags/sql/query.sql
```

## 4. Почему это полезно в Airflow

Airflow может запускать DAG из разных рабочих директорий. Если использовать относительный путь:

```python
open("query.sql")
```

Python будет искать файл относительно текущей рабочей директории процесса, которая может отличаться от директории DAG.

Если использовать:

```python
BASE_DIR = Path(__file__).resolve().parent

open(BASE_DIR / "query.sql")
```

путь будет строиться относительно расположения самого Python-файла.

Это делает загрузку SQL-файлов более предсказуемой.

## 5. Как подняться на уровень выше

Свойство `.parent` можно использовать несколько раз:

```python
BASE_DIR = Path(__file__).resolve().parent

DAGS_DIR = BASE_DIR
PROJECT_DIR = BASE_DIR.parent
ROOT_DIR = BASE_DIR.parent.parent
```

Для структуры:

```text
my_project/
├── dags/
│   └── my_dag.py
└── sql/
    └── query.sql
```

Если `my_dag.py` находится в `dags`, то:

- `BASE_DIR` → `my_project/dags`
- `PROJECT_DIR` → `my_project`
- `ROOT_DIR` → родительская папка `my_project`

Чтобы обратиться к SQL-файлу в корневой папке проекта:

```python
sql_path = BASE_DIR.parent / "sql" / "query.sql"
```

## Кратко

- `Path` — класс для работы с файловыми путями.
- `__file__` — путь к текущему Python-файлу.
- `.resolve()` — получение абсолютного пути.
- `.parent` — родительская директория.
- `/` — соединение частей пути.

**Главная идея:** `Path(__file__).resolve().parent` позволяет находить файлы относительно самого Python-скрипта, не завися от текущей рабочей директории.

# `exists()` в Python

`exists()` — метод объекта `Path`, который проверяет, существует ли файл или директория по указанному пути.

Возвращает булево значение:
- `True` — путь существует.
- `False` — путь не существует.

## 1. Проверка существования файла

```python
from pathlib import Path

file_path = Path("query.sql")

if file_path.exists():
    print("Файл существует")
else:
    print("Файл не найден")
```

## 2. Проверка с `__file__`

Можно проверить, существует ли SQL-файл относительно текущего Python-скрипта.

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sql_path = BASE_DIR / "query.sql"

if sql_path.exists():
    print("SQL-файл найден")
else:
    print("SQL-файл не найден")
```

Например, если скрипт находится в `/home/project/dags/`, Python проверит путь:

```text
/home/project/dags/query.sql
```

## 3. Проверка директории

Метод `exists()` работает не только с файлами, но и с папками.

```python
from pathlib import Path

directory = Path("/home/project/dags")

print(directory.exists())
```

Если папка существует, результат будет `True`.

## 4. Разница между `exists()`, `is_file()` и `is_dir()`

| Метод | Что проверяет |
|---|---|
| `exists()` | Существует ли путь |
| `is_file()` | Существует ли обычный файл |
| `is_dir()` | Существует ли директория |

Пример:

```python
from pathlib import Path

path = Path("query.sql")

if path.exists() and path.is_file():
    print("Файл существует и это файл")
```

**Важно:** `exists()` сам по себе не проверяет, является ли путь файлом. Он вернёт `True`, если по указанному пути существует и файл, и директория.

## 5. Практический пример для Airflow

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SQL_PATH = BASE_DIR / "query.sql"

if not SQL_PATH.exists():
    raise FileNotFoundError(f"SQL-файл не найден: {SQL_PATH}")

with open(SQL_PATH, encoding="utf-8") as file:
    sql = file.read()
```

Здесь, если SQL-файла нет, выполнение завершится с понятной ошибкой, вместо попытки прочитать отсутствующий файл.

## Кратко

```python
path.exists()
```

Проверяет существование пути и возвращает `True` или `False`.

```python
if not path.exists():
    raise FileNotFoundError(path)
```

Позволяет явно сообщить об отсутствии необходимого файла или директории.
