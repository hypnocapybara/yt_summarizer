from django.core.management import BaseCommand
from apps.main.models import YoutubeVideo
from apps.main.summary.chapters import fill_video_chapters


class Command(BaseCommand):
    def handle(self, *args, **options):
        video = YoutubeVideo.objects.get(pk=33)
        fill_video_chapters(video)
