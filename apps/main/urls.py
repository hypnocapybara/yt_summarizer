from django.urls import path

from .views import runpod_webhook


urlpatterns = [
    path('runpod_webhook', runpod_webhook),
]
