import os
from celery import Celery
from celery.schedules import crontab

# Установка переменной окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dogs.settings')

# Создание экземпляра приложения Celery
app = Celery('dogs')

# Загрузка конфигурации из настроек Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматическое обнаружение и регистрация задач из всех приложений Django
app.autodiscover_tasks()

# Настройка периодических задач
app.conf.beat_schedule = {
    'check-inactive-users': {
        'task': 'main.tasks.check_inactive_users',
        'schedule': crontab(hour='*/24'),  # Каждые 24 часа
    },
    'send-daily-statistics': {
        'task': 'main.tasks.send_daily_statistics',
        'schedule': crontab(hour='23', minute='59'),  # Каждый день в полночь
    },
    'cleanup-old-sessions': {
        'task': 'main.tasks.cleanup_old_sessions',
        'schedule': crontab(hour='*/12'),  # Каждый день в 3 часа ночи
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 