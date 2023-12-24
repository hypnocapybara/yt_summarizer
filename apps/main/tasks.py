import io
import whisper

from pytube import Channel, YouTube
from pytube.streams import Stream

# from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, pipeline

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
    video.audio_file.save(f'{video.youtube_id}.{stream.subtype}', buffer)
    video.save()


def transcribe_video(video: YoutubeVideo):
    model = whisper.load_model('medium')
    result = model.transcribe(video.audio_file.path)

    video.transcription_language = result['language']
    video.transcription = result['text']
    video.save()


# def summarize_video(video: YoutubeVideo):
#     if not video.transcription or not video.transcription_language:
#         return
#
#     bnb_config = BitsAndBytesConfig(
#         load_in_4bit=True,
#         bnb_4bit_quant_type='nf4',
#         bnb_4bit_use_double_quant=True,
#     )
#
#     model = AutoModelForCausalLM.from_pretrained(
#         'mistralai/Mistral-7B-Instruct-v0.2',
#         quantization_config=bnb_config
#     )
#
#     tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
#     messages = [
#         {"role": "user", "content": TEMPLATE.format(text=text)},
#     ]
#
#     encodeds = tokenizer.apply_chat_template(messages, return_tensors="pt")
#
#     model_inputs = encodeds.to('cpu')
#
#     generated_ids = model.generate(model_inputs, max_new_tokens=1000, do_sample=True)
#     decoded = tokenizer.batch_decode(generated_ids)
#     print(decoded[0])
