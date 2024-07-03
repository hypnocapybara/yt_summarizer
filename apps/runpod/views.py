import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django_rq import get_queue

from .models import TranscriptionTask
from .tasks import get_transcription


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

    video = task.video

    get_transcription(video, task_id)

    queue = get_queue('default')
    message = 'Transcription done! Running summarization...'
    queue.enqueue('apps.telegram.tasks.notify_video_progress', video, message)

    ai_queue = get_queue('ai')
    ai_queue.enqueue('apps.main.tasks.summarize_video', video)

    return JsonResponse({
        'ok': True
    })
