import io
import whisper

from pytube import Channel, YouTube
from pytube.streams import Stream

from apps.main.models import YoutubeChannel, YoutubeVideo


def parse_channel(channel: YoutubeChannel):
    yt_channel = Channel(channel.url)

    channel.title = yt_channel.title
    channel.save()

    videos = []


def parse_video(video: YoutubeVideo):
    yt_video = YouTube(video.url)

    video.youtube_id = yt_video.video_id
    video.title = yt_video.title
    video.save()

    audio_streams = [stream for stream in yt_video.streams if stream.type == 'audio']
    audio_streams = sorted(audio_streams, key=lambda s: s.bitrate, reverse=True)
    if not audio_streams:
        return

    stream: Stream = audio_streams[0]
    buffer = io.BytesIO()
    stream.stream_to_buffer(buffer)
    video.audio_file.save(video.youtube_id, buffer)
    video.save()


def transcribe_video(video: YoutubeVideo):
    model = whisper.load_model('medium')
    result = model.transcribe(video.audio_file.path)

    video.transcription_language = result['language']
    video.transcription = result['text']
    video.save()
