# 🚀 Руководство по деплою проекта Dogs

## 📋 Предварительные требования

### На сервере должны быть установлены:
- Docker (версия 20.10+)
- Docker Compose (версия 2.0+)
- Git

### Доменное имя и SSL сертификаты:
- Зарегистрированное доменное имя
- SSL сертификаты (можно получить бесплатно через Let's Encrypt)

## 🔧 Подготовка к деплою

### 1. Клонирование репозитория
```bash
git clone <your-repository-url>
cd Dogs
```

### 2. Настройка переменных окружения
```bash
# Копируем пример файла с переменными
cp env.example .env

# Редактируем файл .env с вашими настройками
nano .env
```

### 3. Настройка SSL сертификатов
```bash
# Создаем директорию для SSL сертификатов
mkdir -p nginx/ssl

# Получаем SSL сертификаты через Let's Encrypt
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Копируем сертификаты
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
```

## 🚀 Запуск деплоя

### Автоматический деплой
```bash
# Делаем скрипт исполняемым
chmod +x deploy.sh

# Запускаем деплой
./deploy.sh
```

### Ручной деплой
```bash
# 1. Останавливаем существующие контейнеры
docker-compose -f docker-compose.prod.yml down

# 2. Собираем и запускаем контейнеры
docker-compose -f docker-compose.prod.yml up --build -d

# 3. Ждем запуска базы данных
sleep 10

# 4. Выполняем миграции
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# 5. Создаем суперпользователя (опционально)
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# 6. Собираем статические файлы
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

## 📊 Мониторинг и управление

### Просмотр логов
```bash
# Все сервисы
docker-compose -f docker-compose.prod.yml logs -f

# Конкретный сервис
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### Статус сервисов
```bash
docker-compose -f docker-compose.prod.yml ps
```

### Остановка/запуск сервисов
```bash
# Остановка
docker-compose -f docker-compose.prod.yml stop

# Запуск
docker-compose -f docker-compose.prod.yml start

# Перезапуск
docker-compose -f docker-compose.prod.yml restart
```

### Обновление приложения
```bash
# Останавливаем контейнеры
docker-compose -f docker-compose.prod.yml down

# Обновляем код
git pull origin main

# Пересобираем и запускаем
docker-compose -f docker-compose.prod.yml up --build -d

# Выполняем миграции
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Собираем статические файлы
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

## 🔒 Безопасность

### Рекомендации по безопасности:
1. **Измените SECRET_KEY** в файле .env
2. **Используйте сильные пароли** для базы данных
3. **Настройте файрвол** на сервере
4. **Регулярно обновляйте** SSL сертификаты
5. **Мониторьте логи** на предмет подозрительной активности

### Настройка файрвола (Ubuntu/Debian):
```bash
# Устанавливаем UFW
sudo apt install ufw

# Разрешаем SSH
sudo ufw allow ssh

# Разрешаем HTTP и HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Включаем файрвол
sudo ufw enable
```

## 📈 Масштабирование

### Увеличение количества воркеров Django:
```bash
# В docker-compose.prod.yml измените количество воркеров
command: gunicorn --bind 0.0.0.0:8000 --workers 5 dogs.wsgi:application
```

### Увеличение количества Celery воркеров:
```bash
# Добавьте дополнительные сервисы celery
celery-worker-2:
  build: .
  environment:
    # ... те же переменные окружения
  command: celery -A dogs worker -l info
```

## 🐛 Устранение неполадок

### Проблемы с базой данных:
```bash
# Проверка подключения к БД
docker-compose -f docker-compose.prod.yml exec backend python manage.py dbshell

# Сброс миграций (осторожно!)
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate --fake-initial
```

### Проблемы с Redis:
```bash
# Проверка Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
```

### Проблемы с nginx:
```bash
# Проверка конфигурации nginx
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# Перезапуск nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### Очистка Docker:
```bash
# Удаление неиспользуемых образов
docker system prune -a

# Удаление неиспользуемых томов
docker volume prune
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `docker-compose -f docker-compose.prod.yml logs -f`
2. Убедитесь, что все переменные окружения настроены правильно
3. Проверьте, что порты 80 и 443 открыты на сервере
4. Убедитесь, что SSL сертификаты действительны

## 🔄 Автоматическое обновление SSL сертификатов

Создайте cron задачу для автоматического обновления SSL сертификатов:

```bash
# Открываем crontab
crontab -e

# Добавляем задачу (обновление каждые 60 дней)
0 0 1 */2 * certbot renew --quiet && cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /path/to/project/nginx/ssl/cert.pem && cp /etc/letsencrypt/live/your-domain.com/privkey.pem /path/to/project/nginx/ssl/key.pem && docker-compose -f /path/to/project/docker-compose.prod.yml restart nginx
``` 