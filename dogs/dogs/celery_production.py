import os
from celery import Celery
from celery.schedules import crontab

# Установка переменной окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dogs.settings_production')

# Создание экземпляра приложения Celery
app = Celery('dogs')

# Загрузка конфигурации из настроек Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматическое обнаружение и регистрация задач из всех приложений Django
app.autodiscover_tasks()

# Настройка периодических задач для продакшена
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
        'schedule': crontab(hour='*/12'),  # Каждые 12 часов
    },
    'backup-database': {
        'task': 'main.tasks.backup_database',
        'schedule': crontab(hour='2', minute='0'),  # Каждый день в 2:00
    },
}

# Настройки для продакшена
app.conf.update(
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    task_time_limit=30 * 60,  # 30 минут
    task_soft_time_limit=25 * 60,  # 25 минут
    worker_disable_rate_limits=False,
    worker_send_task_events=True,
    task_send_sent_event=True,
)

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 