from django.core.management import BaseCommand
from django_rq import job, get_queue
from apps.main.models import YoutubeVideo
from apps.main.summary.generic import summarize_video_generic

from pytubefix import YouTube


class Command(BaseCommand):
    def handle(self, *args, **options):
        video = YoutubeVideo.objects.get(pk=32)
        summarize_video_generic(video)
