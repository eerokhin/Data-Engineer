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
