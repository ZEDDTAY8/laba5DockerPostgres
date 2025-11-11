# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код приложения
COPY . .

# Собираем статические файлы (для prod)
RUN python manage.py collectstatic --noinput

# Устанавливаем порт
EXPOSE 8000

# Команда для запуска (используем gunicorn для prod, но для dev — runserver)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "sales_app.wsgi:application"]