# import os 
import os

# import celery 
from celery import Celery

# set the default settings module so celery knows which django settings to use
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


app = Celery("config")

# load celery settings from django settings
app.config_from_object("django.conf:settings", namespace="CELERY")
# automatically find and load tasks.py files from installed apps
app.autodiscover_tasks()