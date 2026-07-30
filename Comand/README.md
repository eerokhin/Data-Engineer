# **Основные команды**

1) **Виртуальное окружение python**

   `python -m venv myenv` - Создает новое виртуальное окружение Python с именем myenv

   `myenv\Scripts\activate` - Активирует виртуальное окружение myenv

2) **Запуск скрипта в Jupyter**
   
   `%run data_for_model.py`

3) **Узнать путь до текущей дирректори в Jupyter**

   `import os`
   
   `os.getcwd()`

4) **Закомментировать сразу большой кусок кода**

   Windows / Linux: `Ctrl + /`

   Jupyter автоматически добавит `#` в начале каждой строки.

5) **Скачать полностью папку из JupyterHub**

```python
import shutil

shutil.make_archive("project_backup","zip","project")
```
Означает:

- `"project_backup"` → имя создаваемого архива (получится `project_backup.zip`)
- `"zip"` → формат архива
- `"project"` → папка, которую нужно запаковать
