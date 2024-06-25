from django.core.management import BaseCommand
from django_rq import job, get_queue
from apps.main.models import YoutubeVideo
from apps.main.tasks import voice_summary

from pytubefix import YouTube


class Command(BaseCommand):
    def handle(self, *args, **options):
        video = YoutubeVideo.objects.get(pk=32)
        queue = get_queue('default')
        queue.enqueue('apps.telegram.tasks.send_video_notifications', video)
