"""
WSGI config for dogs project in production.
"""

import os
from django.core.wsgi import get_wsgi_application

# Устанавливаем переменную окружения для настроек
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dogs.settings_production')

application = get_wsgi_application() 