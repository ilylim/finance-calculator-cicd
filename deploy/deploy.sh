#!/usr/bin/env bash
set -e

echo "=== Запуск скрипта деплоя на Linux сервере ==="

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# 1. Проверяем наличие Python 3 и venv
if ! command -v python3 &> /dev/null; then
    echo "Python 3 не найден. Установите python3 и python3-venv!"
    exit 1
fi

# 2. Создаем или активируем виртуальное окружение
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения venv..."
    python3 -m venv venv
fi

source venv/bin/activate

# 3. Обновляем зависимости
echo "Установка/обновление зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Проверяем, запущен ли сервис через systemd
if systemctl is-active --quiet finance-tracker.service 2>/dev/null; then
    echo "Перезапуск системного сервиса finance-tracker..."
    sudo systemctl restart finance-tracker.service
else
    echo "Перезапуск Gunicorn в фоновом режиме..."
    # Останавливаем предыдущий процесс, если он работал
    pkill -f "gunicorn.*src.app:app" || true
    sleep 1

    # Запускаем Gunicorn
    nohup gunicorn --bind 0.0.0.0:5000 --workers 1 --threads 4 src.app:app > gunicorn.log 2>&1 &
fi

echo "Деплой скрипта завершен успешно!"
