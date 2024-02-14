from django.contrib import admin

from .models import TelegramUser, TelegramVideo, VideoNotification, SingleVideoToSend


admin.site.register(TelegramUser)
admin.site.register(TelegramVideo)
admin.site.register(VideoNotification)
admin.site.register(SingleVideoToSend)
