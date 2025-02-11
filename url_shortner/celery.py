import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'url_shortner.settings')

app = Celery('url_shortner')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()