#!/bin/bash

# Скрипт для обновления SSL сертификатов

set -e

echo "🔒 Обновление SSL сертификатов..."

# Проверяем, установлен ли certbot
if ! command -v certbot &> /dev/null; then
    echo "❌ Certbot не установлен. Установите его:"
    echo "sudo apt install certbot"
    exit 1
fi

# Получаем домен из переменной окружения или используем по умолчанию
DOMAIN=${DOMAIN:-your-domain.com}

echo "🌐 Обновление сертификатов для домена: $DOMAIN"

# Обновляем сертификаты
certbot renew --quiet

# Копируем обновленные сертификаты
echo "📋 Копирование сертификатов..."
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem nginx/ssl/key.pem

# Устанавливаем правильные права доступа
sudo chown $USER:$USER nginx/ssl/cert.pem nginx/ssl/key.pem
chmod 644 nginx/ssl/cert.pem
chmod 600 nginx/ssl/key.pem

# Перезапускаем nginx
echo "🔄 Перезапуск nginx..."
docker-compose -f docker-compose.prod.yml restart nginx

echo "✅ SSL сертификаты обновлены успешно!" 