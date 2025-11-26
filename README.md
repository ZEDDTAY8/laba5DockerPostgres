# Sales XML App (Dockerized with PostgreSQL)

Это Django-приложение для работы с данными о продажах. Данные можно сохранять в XML-файлах или в базе данных PostgreSQL. Приложение упаковано в Docker для простоты запуска.

## Требования
- Установленный Docker и Docker Compose (на Red OS Linux: откройте терминал и выполните `sudo dnf install docker docker-compose` — если Red OS на базе Fedora, это сработает. Если нужно, проверьте документацию Red OS для установки Docker).
- Свободный порт 8000 на вашем компьютере.

## Установка и запуск для разработки (просто для тестирования)
1. Скачайте проект с GitHub: В терминале выполните `git clone https://github.com/ZEDDTAY8/laba5DockerPostgres`. Перейдите в папку: `cd laba5DockerPostgres`.
2. Создайте файл `.env` в корне папки. Скопируйте в него это (замените пароли на свои, если хотите):

DB_NAME=sales_db
DB_USER=sales_user
DB_PASSWORD=Пароль
DB_HOST=db
DB_PORT=5432
SECRET_KEY=Ключ Сгенерируйте: python -c "import secrets; print(secrets.token_urlsafe(50))"
DEBUG=True

3. Запустите приложение: В терминале выполните `docker-compose up --build`. Это соберёт и запустит контейнеры (приложение и базу данных). Подождите, пока увидите сообщение о запуске сервера.
4. Откройте в браузере: http://localhost:8000 (или http://127.0.0.1:8000).
5. Первый раз настройте базу: В новом терминале выполните `docker-compose exec web python manage.py migrate` (это создаст таблицы в PostgreSQL).
6. Чтобы остановить: Нажмите Ctrl+C в терминале, или `docker-compose down`.

Если что-то не запускается, проверьте логи: `docker-compose logs`.

## Запуск для production (для реального использования, без отладки)
1. В файле `.env` измените `DEBUG=False` (для безопасности).
2. В файле `docker-compose.yml` измените строку `command: python manage.py runserver 0.0.0.0:8000` на `command: gunicorn --bind 0.0.0.0:8000 sales_app.wsgi:application` (замените `sales_app` на имя вашего проекта, если отличается).
3. Добавьте в `requirements.txt` строку `gunicorn` и пересоберите: `docker-compose up --build`.
4. Соберите статические файлы: `docker-compose exec web python manage.py collectstatic --noinput`.
5. Запустите как в разработке, но теперь приложение готово к реальной работе. Для статических файлов добавьте NGINX (см. docker-compose.yml, раскомментируйте сервис `nginx` и настройте конфиг, если нужно).

## Перенос данных из старой базы (SQLite) в новую (PostgreSQL)
Если у вас есть данные в старой SQLite-базе (файл db.sqlite3):
1. В старом проекте (без Docker) выполните `python manage.py dumpdata sales_app.Sale > data.json` (это сохранит данные в файл data.json).
2. Скопируйте data.json в папку нового проекта.
3. Запустите Docker: `docker-compose up -d` (в фоне).
4. Импортируйте: `docker-compose exec web python manage.py loaddata data.json`.
5. Проверьте в приложении, что данные появились.

Если данных мало, можно ввести заново через форму в приложении.

## Функционал
- Ввод продаж через форму (выберите в XML или БД).
- Проверка на дубликаты в БД (не добавит, если уже есть).
- Просмотр данных из XML или БД (выберите источник).
- Поиск по товарам в БД (AJAX, работает динамически).
- Редактирование и удаление записей в БД.
- Загрузка XML-файлов.

Если проблемы: Проверьте, что Docker запущен (`sudo systemctl start docker` на Red OS), и порты свободны.
