from django.core.management import BaseCommand
from apps.main.models import YoutubeVideo
from apps.main.tasks import parse_video
from apps.main.summary.openai import summarize_video_openai

from pytubefix import YouTube


class Command(BaseCommand):
    def handle(self, *args, **options):
        video = YoutubeVideo.objects.get(pk=1)
        yt_video = YouTube(video.url)
        video.chapters = [
            {
                "start": c.start_seconds,
                "duration": c.duration,
                "title": c.title
            }
            for c in yt_video.chapters
        ]
        video.save()
