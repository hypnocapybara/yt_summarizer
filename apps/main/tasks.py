import io
import os
import random

import torch
import tempfile

from django.utils import timezone
from django_rq import job, get_queue
from TTS.api import TTS

from pytubefix import Channel, YouTube

from .transcription.openai import transcribe_video_openai
from .summary.openai import summarize_video_openai

from apps.main.models import YoutubeChannel, YoutubeVideo

BITRATE_THRESHOLD = 50_000
SPEAKERS = [
    'Claribel Dervla', 'Daisy Studious', 'Gracie Wise', 'Tammie Ema', 'Alison Dietlinde', 'Ana Florence',
    'Annmarie Nele', 'Asya Anara', 'Brenda Stern', 'Gitta Nikolina', 'Henriette Usha', 'Sofia Hellen',
    'Tammy Grit', 'Tanja Adelina', 'Vjollca Johnnie', 'Andrew Chipper', 'Badr Odhiambo', 'Dionisio Schuyler',
    'Royston Min', 'Viktor Eka', 'Abrahan Mack', 'Adde Michal', 'Baldur Sanjin', 'Craig Gutsy', 'Damien Black',
    'Gilberto Mathias', 'Ilkin Urbano', 'Kazuhiko Atallah', 'Ludvig Milivoj', 'Suad Qasim', 'Torcull Diarmuid',
    'Viktor Menelaos', 'Zacharie Aimilios', 'Nova Hogarth', 'Maja Ruoho', 'Uta Obando', 'Lidiya Szekeres',
    'Chandra MacFarland', 'Szofi Granger', 'Camilla Holmström', 'Lilya Stainthorpe', 'Zofija Kendrick',
    'Narelle Moon', 'Barbora MacLean', 'Alexandra Hisakawa', 'Alma María', 'Rosemary Okafor', 'Ige Behringer',
    'Filip Traverse', 'Damjan Chapman', 'Wulf Carlevaro', 'Aaron Dreschner', 'Kumar Dahl', 'Eugenio Mataracı',
    'Ferran Simen', 'Xavier Hayasaka', 'Luis Moray', 'Marcos Rudaski'
]


@job('default')
def parse_all_channels():
    print('running parse all channels')

    for channel in YoutubeChannel.objects.filter(enabled=True):
        parse_channel.delay(channel)


@job('default')
def parse_channel(channel: YoutubeChannel):
    print(f'running parse channel {str(channel)}')

    yt_channel = Channel(channel.url)
    channel.title = yt_channel.channel_name
    channel.save()

    try:
        last_video = yt_channel.videos[0]
    except IndexError:
        return

    if YoutubeVideo.objects.filter(channel=channel, youtube_id=last_video.video_id).exists():
        return

    new_video = YoutubeVideo.objects.create(
        channel=channel,
        url=last_video.watch_url,
        youtube_id=last_video.video_id,
        title=last_video.title,
    )

    channel.last_parsed_at = timezone.now()
    channel.save()

    parse_video.delay(new_video)


@job('default')
def parse_video(video: YoutubeVideo):
    print(f'running parse video {str(video)}')

    yt_video = YouTube(video.url)

    video.youtube_id = yt_video.video_id
    video.title = yt_video.title
    video.chapters = [
        {
            "start": c.start_seconds,
            "duration": c.duration,
            "title": c.title
        }
        for c in yt_video.chapters
    ]
    video.save()

    audio_streams = [stream for stream in yt_video.streams if stream.mime_type == "audio/mp4"]

    if not audio_streams:
        return

    high_bitrate_streams = sorted(
        [stream for stream in audio_streams if stream.bitrate > BITRATE_THRESHOLD],
        key=lambda s: s.bitrate
    )

    if high_bitrate_streams:
        stream = high_bitrate_streams[0]
    else:
        stream = audio_streams[0]

    buffer = io.BytesIO()
    stream.stream_to_buffer(buffer)
    video.audio_file.save(f'{video.youtube_id}.{stream.subtype}', buffer)
    video.save()

    transcribe_video.delay(video)

    _notify_telegram_users(video, 'Video fetched! Running transcript...')


@job('ai', timeout=60 * 60)
def transcribe_video(video: YoutubeVideo):
    print(f'running transcribe video {str(video)}')

    if video.transcription:
        print("already have transcription, skipping...")
        return

    transcribe_video_openai(video)
    summarize_video.delay(video)

    _notify_telegram_users(video, 'Transcription done! Running summarization...')


@job('ai', timeout=10 * 60)
def summarize_video(video: YoutubeVideo):
    print(f'running summarize video {str(video)}')

    if video.summary:
        print("already have summary, skipping...")
        return

    summarize_video_openai(video)
    # voice_summary.delay(video)

    _notify_telegram_users(video, 'Summarization done! Generating audio...')


@job('ai', timeout=20 * 60)
def voice_summary(video: YoutubeVideo):
    print(f'running voice summary {str(video)}')

    if not video.summary:
        return

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2').to(device)
    _fd, temp_filename = tempfile.mkstemp()
    try:
        if video.channel and video.channel.voice_file:
            speaker_params = {'speaker_wav': video.channel.voice_file.path}
        else:
            speaker_params = {'speaker': random.choice(SPEAKERS)}

        tts.tts_to_file(
            text=video.summary,
            language=video.transcription_language,
            file_path=temp_filename,
            **speaker_params,
        )
        with open(temp_filename, 'rb') as file:
            video.voiced_summary.save(f'{video.youtube_id}.wav', file)
            video.save()
    finally:
        os.remove(temp_filename)

    queue = get_queue('default')
    queue.enqueue('apps.telegram.tasks.send_video_notifications', video)


def _notify_telegram_users(video: YoutubeVideo, message: str):
    queue = get_queue('default')
    queue.enqueue('apps.telegram.tasks.notify_video_progress', video, message)
