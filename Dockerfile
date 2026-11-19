# Базовый образ Python
FROM python:3.11-slim

# Установка переменных окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    DATA_DIR=/app/data

# Рабочая директория
WORKDIR /app

# Установка системных зависимостей (включая curl для healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей и устанавливаем
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создаем пользователя без root-прав для безопасности
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appuser /app

# Копируем исходный код приложения
COPY src/ /app/src/

# Переключаемся на непривилегированного пользователя
USER appuser

# Открываем порт
EXPOSE 5000

# Health check для Docker
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# Запуск WSGI-сервера Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "src.app:app"]
