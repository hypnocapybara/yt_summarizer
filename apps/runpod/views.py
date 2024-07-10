import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import TranscriptionTask
from .tasks import fetch_transcription_task


@csrf_exempt
def webhook(request):
    data = json.loads(request.body)

    task_id = data['id']
    status = data['status']
    if status != 'COMPLETED':
        print('[webhook] the task is not completed')
        return

    try:
        task = TranscriptionTask.objects.get(
            task_id=task_id
        )
    except TranscriptionTask.DoesNotExist:
        print('[webhook] TranscriptionTask was not found')
        return

    fetch_transcription_task.delay(task.video, task_id)

    return JsonResponse({
        'ok': True
    })
