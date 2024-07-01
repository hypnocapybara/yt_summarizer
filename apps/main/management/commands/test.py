from django.core.management import BaseCommand
from apps.main.models import YoutubeVideo
from apps.main.tasks import parse_video
from apps.main.transcription.runpod_whisper import transcribe_video_runpod_whisper, get_transcription
from apps.main.transcription.openai import transcribe_video_openai
from apps.main.summary.chapters import fill_video_chapters
from apps.main.summary.generic import summarize_video_generic


class Command(BaseCommand):
    def handle(self, *args, **options):
        video = YoutubeVideo.objects.get(pk=35)
        transcribe_video_runpod_whisper(video)
        # parse_video(video)
        # transcribe_video_openai(video)
        # fill_video_chapters(video)
        # summarize_video_generic(video)
