Рабочий docker файл который используется для тестирования.

Инструменты которые устанавливаются:
- Airflow
- Postgres
- Minio

В переменную `_PIP_ADDITIONAL_REQUIREMENTS: ${_PIP_ADDITIONAL_REQUIREMENTS:-duckdb}` был добавлен `duckdb`.

Выполняю команду: `docker-compose up -d`

Проверяю: `docker ps`

Как видно сервисы стартанули

<img width="1787" height="168" alt="image" src="https://github.com/user-attachments/assets/129c3e1b-47d4-490a-9b56-1a493ea0491c" />
