# Импорт Celery для автоматической загрузки
from .celery import app as celery_app

__all__ = ('celery_app',)
