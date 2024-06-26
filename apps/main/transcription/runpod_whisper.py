import requests

from django.conf import settings

from apps.main.models import YoutubeVideo


def transcribe_video_runpod_whisper(video: YoutubeVideo):
    url = f'https://{settings.BASE_DOMAIN}{video.audio_file.url}'
    print('Audio URL', url)

    data = {
        'input': {
            'audio': url,
            'model': 'large-v3',
        }
    }

    endpoint_id = settings.MY_WHISPER_ID
    url = f'https://api.runpod.ai/v2/{endpoint_id}/run'
    result = requests.post(url, json=data, headers={
        'Authorization': settings.RUNPOD_API_KEY
    })
    result.raise_for_status()

    print(result.json())


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
