# Используем официальный образ Python
FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы приложения в контейнер
COPY requirements.txt .
COPY . .

# Устанавливаем зависимости
RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install --upgrade pip \
    && pip install -r requirements.txt

# Запускаем приложение
CMD ["python", "app.py"]
