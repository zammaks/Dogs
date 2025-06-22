#!/bin/bash

# Скрипт для мониторинга состояния сервисов

echo "🔍 Проверка состояния сервисов..."

# Проверяем статус контейнеров
echo "📊 Статус контейнеров:"
docker-compose -f docker-compose.prod.yml ps

echo ""

# Проверяем использование ресурсов
echo "💾 Использование ресурсов:"
docker stats --no-stream

echo ""

# Проверяем логи на ошибки
echo "⚠️  Последние ошибки в логах:"
docker-compose -f docker-compose.prod.yml logs --tail=20 | grep -i error

echo ""

# Проверяем доступность сервисов
echo "🌐 Проверка доступности сервисов:"

# Проверяем Django
if curl -f -s http://localhost:8000/api/ > /dev/null; then
    echo "✅ Django API доступен"
else
    echo "❌ Django API недоступен"
fi

# Проверяем базу данных
if docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U $DB_USER > /dev/null 2>&1; then
    echo "✅ База данных доступна"
else
    echo "❌ База данных недоступна"
fi

# Проверяем Redis
if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis доступен"
else
    echo "❌ Redis недоступен"
fi

echo ""

# Проверяем свободное место на диске
echo "💿 Использование диска:"
df -h | grep -E '^/dev/'

echo ""

# Проверяем использование памяти
echo "🧠 Использование памяти:"
free -h

echo ""

echo "✅ Мониторинг завершен" 