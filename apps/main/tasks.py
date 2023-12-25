import io
import os

import whisper
import torch
import tempfile
from django.utils import timezone
from django_rq import job
from TTS.api import TTS

from pytubefix import Channel, YouTube
from pytubefix.streams import Stream

from .summary.openai import summarize_video_openai
# from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, pipeline

from apps.main.models import YoutubeChannel, YoutubeVideo


@job('default')
def parse_all_channels():
    print('running parse all channels')


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

    YoutubeVideo.objects.create(
        channel=channel,
        url=last_video.watch_url,
        youtube_id=last_video.video_id,
        title=last_video.title,
    )

    channel.last_parsed_at = timezone.now()
    channel.save()


@job('default')
def parse_video(video: YoutubeVideo):
    print(f'running parse video {str(video)}')

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
    video.audio_file.save(f'{video.youtube_id}.{stream.subtype}', buffer)
    video.save()


@job('ai')
def transcribe_video(video: YoutubeVideo):
    print(f'running transcribe video {str(video)}')

    model = whisper.load_model('medium')
    result = model.transcribe(video.audio_file.path)

    video.transcription_language = result['language']
    video.transcription = result['text']
    video.save()


@job('ai')
def summarize_video(video: YoutubeVideo):
    print(f'running summarize video {str(video)}')

    return summarize_video_openai(video)

    # bnb_config = BitsAndBytesConfig(
    #     load_in_4bit=True,
    #     bnb_4bit_quant_type='nf4',
    #     bnb_4bit_use_double_quant=True,
    # )
    #
    # model = AutoModelForCausalLM.from_pretrained(
    #     'mistralai/Mistral-7B-Instruct-v0.2',
    #     quantization_config=bnb_config
    # )
    #
    # tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
    # messages = [
    #     {"role": "user", "content": TEMPLATE.format(text=text)},
    # ]
    #
    # encodeds = tokenizer.apply_chat_template(messages, return_tensors="pt")
    #
    # model_inputs = encodeds.to('cpu')
    #
    # generated_ids = model.generate(model_inputs, max_new_tokens=1000, do_sample=True)
    # decoded = tokenizer.batch_decode(generated_ids)
    # print(decoded[0])


@job('ai')
def voice_summary(video: YoutubeVideo):
    print(f'running voice summary {str(video)}')

    if not video.summary:
        return

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2').to(device)
    _fd, temp_filename = tempfile.mkstemp()
    try:
        tts.tts_to_file(
            text=video.summary,
            speaker_wav=video.channel.voice_file.path,
            language=video.transcription_language,
            file_path=temp_filename,
        )
        with open(temp_filename, 'rb') as file:
            video.voiced_summary.save(f'{video.youtube_id}.wav', file)
            video.save()
    finally:
        os.remove(temp_filename)
