import io

from django.utils import timezone
from django_rq import job, get_queue

from pytubefix import Channel, YouTube

from .transcription.openai import transcribe_video_openai
from .summary.openai import summarize_video_openai
from .voicening.openai import voicen_video_openai

from apps.main.models import YoutubeChannel, YoutubeVideo

BITRATE_THRESHOLD = 50_000
ENABLE_VOICENING = False


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

    if ENABLE_VOICENING:
        voice_summary.delay(video)
        _notify_telegram_users(video, 'Summarization done!')
    else:
        queue = get_queue('default')
        queue.enqueue('apps.telegram.tasks.send_video_notifications', video)


@job('ai', timeout=20 * 60)
def voice_summary(video: YoutubeVideo):
    print(f'running voice summary {str(video)}')

    if not video.summary:
        return

    voicen_video_openai(video)

    queue = get_queue('default')
    queue.enqueue('apps.telegram.tasks.send_video_notifications', video)


def _notify_telegram_users(video: YoutubeVideo, message: str):
    queue = get_queue('default')
    queue.enqueue('apps.telegram.tasks.notify_video_progress', video, message)
