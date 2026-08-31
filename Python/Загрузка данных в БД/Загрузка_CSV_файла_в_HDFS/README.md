## 1. Подготовка CSV-файла

Если исходные данные находятся в `Excel`: `Файл → Сохранить как → CSV`. Например: `data.csv`

Проверить кодировку. CSV должен быть сохранён в `UTF-8`. Это можно проверить/изменить через `Notepad++`: `Кодировки → Преобразовать в UTF-8`

## 2. Создание таблицы

Проверить разделитель. Открой CSV и посмотри, чем разделены поля.

Например:

```text
id;service_m;type_m
1;service1;type1
2;service2;type2
```

Здесь разделитель: `;`

Перед применением шаблона обязательно:
- Заменить <схема>.<название таблицы> на свое название таблицы
- Привести состав полей к виду вашего CSV
- Проверить/заменить разделители, `FIELDS TERMINATED BY ';'` - Разделитель полей в рамках одной строки, `LINES TERMINATED BY '\n'` - разделитель строк.

Шаблон:

```python
DROP TABLE IF EXISTS <схема>.<название таблицы;

CREATE TABLE <схема>.<название таблицы (
    id INT,
    service_m STRING,
    type_m STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ';'
LINES TERMINATED BY '\n'
STORED AS TEXTFILE;
```

## 3. Перенос файла в hdfs

Для переноса файла с локального `ПК` в `HDFS` можно использовать веб-интерфейс `HUE`.

В левой части окна `HUE` необходимо выбрать иконку `"файлы"`, затем в основной части прописать путь до нужной директории в `hdfs`. К примеру, если у вас таблица называется `test_table` и хранится в схеме `sbxm_hr`, 
то путь будет выглядеть так: `/data/sbxm/hr/test_table`

После этого можно перетащить файл из локальной папки прямо в окно `HUE` (`drag-and-drop`), либо воспользоваться кнопкой `Upload`.

<img width="1164" height="521" alt="image" src="https://github.com/user-attachments/assets/a4e12084-fc3c-4aa1-ac8d-fb19b5cf09f2" />


## 4. Обновление данных

Обновить информацию в Impala.

Чтобы данные подтянулись из файла выполняем запрос (требуется подставить свое название таблицы):

```python
REFRESH <схема>.<название таблицы>
```

Это сообщает Impala: В директории таблицы появились новые файлы, перечитай метаданные.

## 5. Проверить директорию через Python

В `Jupyter`, можно проверять дирректорию и путь `HDFS` прямо из `Python`.

Например:

```python
import subprocess

hdfs_dir = "/user/gpbu53998/test_table"

result = subprocess.run(
    ["hdfs", "dfs", "-ls", "-d", hdfs_dir],
    capture_output=True,
    text=True
)

print("return code:", result.returncode)
print("stdout:", result.stdout)
print("stderr:", result.stderr)
```

Если: `return code: 0` директория существует и доступна.

Если: `return code: 1` или другой ненулевой код — нужно смотреть: `print(result.stderr)`

**Если директории нет**

Если у тебя есть права на создание директории:

```python
import subprocess

hdfs_dir = "/user/gpbu53998/test_table"

subprocess.run(
    ["hdfs", "dfs", "-mkdir", "-p", hdfs_dir],
    check=True
)
```

Проверяем:

```python
subprocess.run(
    ["hdfs", "dfs", "-ls", "-d", hdfs_dir],
    check=True
)
```

Но не создавать `/data/sbxm/hr/...` самостоятельно, если нет уверенности, что это правильный корпоративный путь.


## 6. Загрузка CSV через Python

Если `hdfs` доступен из `Jupyter`, можно загрузить программно.

```
import subprocess

local_file = "data.csv"
hdfs_dir = "/user/gpbu53998/test_table"

result = subprocess.run(
    ["hdfs", "dfs", "-put", local_file, hdfs_dir],
    capture_output=True,
    text=True
)

print("return code:", result.returncode)
print("stdout:", result.stdout)
print("stderr:", result.stderr)
```

Если: `return code: 0`, файл должен быть загружен.

`-put` передаёт файл непосредственно в HDFS, не загружая весь файл в память Python.

**Проверить, что CSV действительно попал в HDFS**

После загрузки:

```python
import subprocess

result = subprocess.run(
    ["hdfs", "dfs", "-ls", hdfs_dir],
    capture_output=True,
    text=True
)

print(result.stdout)
print(result.stderr)
```

Должно появиться примерно: `-rw-r--r--   3 gpbu53998 supergroup   1234567 2026-08-31 18:00 /user/gpbu53998/test_table/data.csv`

Это означает:

```text
HDFS
└── /user/gpbu53998/test_table
    └── data.csv
```

## 7. Полный процесс

```text
В итоге твой workflow выглядит так:

             Excel
               │
               ▼
         Сохранить CSV
               │
               ▼
        Проверить UTF-8
               │
               ▼
      Проверить разделитель
               │
               ▼
      ┌───────────────────┐
      │ Создать таблицу    │
      │ в Impala           │
      └─────────┬─────────┘
                │
                ▼
             HDFS
                │
       ┌────────┴────────┐
       │                 │
      Hue              Python
       │                 │
       └────────┬────────┘
                ▼
             data.csv
                │
                ▼
          REFRESH table
                │
                ▼
          SELECT / COUNT
```
