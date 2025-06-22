#!/bin/bash

# Скрипт для деплоя проекта Dogs

set -e  # Остановка при ошибке

echo "🚀 Начинаем деплой проекта Dogs..."

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден! Создайте его на основе env.example"
    exit 1
fi

# Останавливаем существующие контейнеры
echo "🛑 Останавливаем существующие контейнеры..."
docker-compose -f docker-compose.prod.yml down

# Удаляем старые образы (опционально)
echo "🧹 Удаляем старые образы..."
docker system prune -f

# Собираем и запускаем контейнеры
echo "🔨 Собираем и запускаем контейнеры..."
docker-compose -f docker-compose.prod.yml up --build -d

# Ждем запуска базы данных
echo "⏳ Ждем запуска базы данных..."
sleep 10

# Выполняем миграции
echo "📦 Выполняем миграции базы данных..."
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Создаем суперпользователя (если нужно)
echo "👤 Создание суперпользователя..."
read -p "Создать суперпользователя? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
fi

# Собираем статические файлы
echo "📁 Собираем статические файлы..."
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

# Проверяем статус сервисов
echo "🔍 Проверяем статус сервисов..."
docker-compose -f docker-compose.prod.yml ps

echo "✅ Деплой завершен успешно!"
echo "🌐 Приложение доступно по адресу: https://your-domain.com"
echo "📊 Мониторинг контейнеров: docker-compose -f docker-compose.prod.yml logs -f" 