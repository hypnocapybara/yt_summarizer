from django.http import JsonResponse


def runpod_webhook(request):
    return JsonResponse({
        'ok': True
    })
