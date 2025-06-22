#!/bin/bash

# Интерактивный скрипт для настройки переменных окружения

echo "🔧 Настройка переменных окружения для проекта Dogs"
echo ""

# Проверяем, существует ли уже файл .env
if [ -f .env ]; then
    echo "⚠️  Файл .env уже существует. Создать резервную копию? (y/n)"
    read -r backup_choice
    if [[ $backup_choice =~ ^[Yy]$ ]]; then
        cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
        echo "✅ Резервная копия создана"
    fi
fi

echo ""
echo "📝 Заполните следующие поля:"
echo ""

# Генерируем новый SECRET_KEY
NEW_SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

# Запрашиваем данные у пользователя
read -p "🌐 Доменное имя (например: example.com): " DOMAIN
read -p "🔑 SECRET_KEY (нажмите Enter для автогенерации): " SECRET_KEY
read -p "🗄️  Имя базы данных [dogs_db]: " DB_NAME
read -p "👤 Пользователь базы данных [dogs_user]: " DB_USER
read -s -p "🔒 Пароль базы данных: " DB_PASSWORD
echo ""
read -p "📧 Email для отправки писем: " EMAIL_HOST_USER
read -s -p "🔑 Пароль приложения для email: " EMAIL_HOST_PASSWORD
echo ""
read -p "🔑 Yandex OAuth2 Key: " YANDEX_OAUTH2_KEY
read -s -p "🔒 Yandex OAuth2 Secret: " YANDEX_OAUTH2_SECRET
echo ""

# Устанавливаем значения по умолчанию
SECRET_KEY=${SECRET_KEY:-$NEW_SECRET_KEY}
DB_NAME=${DB_NAME:-dogs_db}
DB_USER=${DB_USER:-dogs_user}

# Создаем файл .env
cat > .env << EOF
# Django settings
DEBUG=False
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN

# Database settings
DB_ENGINE=django.db.backends.postgresql
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432

# Redis settings
REDIS_URL=redis://localhost:6379/0

# Email settings
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=$EMAIL_HOST_USER
EMAIL_HOST_PASSWORD=$EMAIL_HOST_PASSWORD

# OAuth2 settings
SOCIAL_AUTH_YANDEX_OAUTH2_KEY=$YANDEX_OAUTH2_KEY
SOCIAL_AUTH_YANDEX_OAUTH2_SECRET=$YANDEX_OAUTH2_SECRET
SOCIAL_AUTH_LOGIN_REDIRECT_URL=https://$DOMAIN
SOCIAL_AUTH_LOGIN_ERROR_URL=https://$DOMAIN/login
SOCIAL_AUTH_YANDEX_OAUTH2_REDIRECT_URI=https://$DOMAIN/api/auth/yandex/callback/

# CORS settings
CORS_ALLOWED_ORIGINS=https://$DOMAIN,https://www.$DOMAIN

# Static and Media files
STATIC_ROOT=/var/www/dogs/static/
MEDIA_ROOT=/var/www/dogs/media/

# Celery settings
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
EOF

echo ""
echo "✅ Файл .env создан успешно!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Проверьте файл .env и при необходимости отредактируйте его"
echo "2. Настройте SSL сертификаты: ./update-ssl.sh"
echo "3. Запустите деплой: ./deploy.sh"
echo "" 