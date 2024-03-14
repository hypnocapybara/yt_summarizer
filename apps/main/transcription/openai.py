from time import time

from django.conf import settings
from openai import OpenAI

from apps.main.models import YoutubeVideo


LANGUAGES_MAP = {
    'russian': 'ru',
    'english': 'en',
}


def transcribe_video_openai(video: YoutubeVideo):
    client = OpenAI(api_key=settings.OPEN_AI_KEY)

    with open(video.audio_file.path, 'rb') as audio_file:
        time_start = time()
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
        )
        print("transcribed in", time() - time_start)
        video.transcription_language = LANGUAGES_MAP.get(result.language, 'unknown')
        video.transcription = result.text
        video.transcription_segments = [
            {
                key: s[key].strip() if type(s[key]) is str else s[key]
                for key in ['start', 'end', 'text']
            }
            for s in result.segments
        ]

        video.save()
