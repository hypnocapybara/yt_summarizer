import requests

from django.conf import settings
from django_rq import job, get_queue

from apps.main.models import YoutubeVideo
from .models import TranscriptionTask


@job('default')
def transcribe_video_runpod_whisper(video: YoutubeVideo):
    url = f'https://{settings.BASE_DOMAIN}{video.audio_file.url}'
    print('Audio URL', url)
    webhook_url = f'https://{settings.BASE_DOMAIN}/runpod/webhook'

    data = {
        'input': {
            'audio': url,
            'model': 'large-v3',
        },
        'webhook': webhook_url,
    }

    endpoint_id = settings.MY_WHISPER_ID
    url = f'https://api.runpod.ai/v2/{endpoint_id}/run'
    result = requests.post(url, json=data, headers={
        'Authorization': settings.RUNPOD_API_KEY
    })
    result.raise_for_status()

    output = result.json()
    task_id = output['id']

    TranscriptionTask.objects.create(
        video=video,
        task_id=task_id
    )


def get_transcription(video: YoutubeVideo, task_id: str):
    endpoint_id = settings.MY_WHISPER_ID
    url = f'https://api.runpod.ai/v2/{endpoint_id}/status/{task_id}'

    response = requests.get(url, headers={
        'Authorization': settings.RUNPOD_API_KEY
    })

    response.raise_for_status()

    data = response.json()
    if data['status'] != 'COMPLETED':
        print('The task is not completed yet')
        return

    output = data['output']

    video.transcription_language = output['detected_language']
    video.transcription = output['transcription']
    video.transcription_segments = [
        {
            key: s[key]
            for key in ['start', 'end', 'text']
        }
        for s in output['segments']
    ]

    video.save()


@job('default')
def fetch_transcription_task(video: YoutubeVideo, task_id: str):
    get_transcription(video, task_id)

    queue = get_queue('default')
    message = 'Transcription done! Running summarization...'
    queue.enqueue('apps.telegram.tasks.notify_video_progress', video, message)

    ai_queue = get_queue('ai')
    ai_queue.enqueue('apps.main.tasks.summarize_video', video)
