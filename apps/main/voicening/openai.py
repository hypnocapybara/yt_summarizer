import os
import tempfile

from openai import OpenAI
from nltk import tokenize
from pydub import AudioSegment
from django.conf import settings

from apps.main.models import YoutubeVideo
from apps.main.summary.generic import TOKENIZER_LANGUAGES

MAX_CHUNK_LEN = 4096


def voicen_video_openai(video: YoutubeVideo):
    client = OpenAI(api_key=settings.OPEN_AI_KEY)

    sentences = tokenize.sent_tokenize(video.summary, language=TOKENIZER_LANGUAGES[video.transcription_language])
    chunks = []
    next_chunk = ''

    for sentence in sentences:
        if len(next_chunk) + len(sentence) > MAX_CHUNK_LEN:
            chunks.append(next_chunk)
            next_chunk = ''

        next_chunk += sentence

    chunks.append(next_chunk)
    voicen_filenames = []

    for chunk in chunks:
        print('[OpenAI] Voicening the next chunk')

        _fd, temp_filename = tempfile.mkstemp()
        try:
            response = client.audio.speech.create(
                model="tts-1",
                voice="echo",
                input=chunk
            )

            response.stream_to_file(temp_filename)
            voicen_filenames.append(temp_filename)
        except Exception as e:
            os.remove(temp_filename)
            raise e

    if not voicen_filenames:
        return

    full_audio = AudioSegment.from_mp3(voicen_filenames[0])
    for next_audio_file in voicen_filenames[1:]:
        full_audio += AudioSegment.from_mp3(next_audio_file)

    for filename in voicen_filenames:
        os.remove(filename)

    _fd, temp_filename = tempfile.mkstemp()
    try:
        full_audio.export(temp_filename, format="mp3")

        with open(temp_filename, 'rb') as file:
            video.voiced_summary.save(f'{video.youtube_id}.mp3', file)
            video.save()
    finally:
        os.remove(temp_filename)
