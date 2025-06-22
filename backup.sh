#!/bin/bash

# Скрипт для бэкапа базы данных

set -e

# Настройки
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME=${DB_NAME:-dogs_db}
DB_USER=${DB_USER:-dogs_user}
DB_HOST=${DB_HOST:-localhost}

# Создаем директорию для бэкапов если её нет
mkdir -p $BACKUP_DIR

# Имя файла бэкапа
BACKUP_FILE="$BACKUP_DIR/dogs_db_$DATE.sql"

echo "🔄 Создание бэкапа базы данных..."

# Создаем бэкап
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U $DB_USER $DB_NAME > $BACKUP_FILE

# Сжимаем бэкап
gzip $BACKUP_FILE

echo "✅ Бэкап создан: ${BACKUP_FILE}.gz"

# Удаляем старые бэкапы (оставляем последние 7)
echo "🧹 Удаление старых бэкапов..."
find $BACKUP_DIR -name "dogs_db_*.sql.gz" -mtime +7 -delete

echo "✅ Очистка завершена" 