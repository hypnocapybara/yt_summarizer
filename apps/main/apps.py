from django.utils import timezone
from django_rq import get_scheduler

from django.apps import AppConfig
from django_rq.queues import DjangoScheduler


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.main'

    def ready(self):
        scheduler: DjangoScheduler = get_scheduler('default')

        for job in scheduler.get_jobs():
            job.delete()

        scheduler.schedule(timezone.now(), 'apps.main.tasks.parse_all_channels', interval=5)
