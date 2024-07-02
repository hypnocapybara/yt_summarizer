from django.http import JsonResponse
from django_rq import get_queue


def webhook(request):
    queue = get_queue('default')
    message = 'Transcription done! Running summarization...'
    queue.enqueue('apps.telegram.tasks.notify_video_progress', video, message)

    return JsonResponse({
        'ok': True
    })
