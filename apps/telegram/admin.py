from django.db import models
from django.contrib import admin
from django.forms import CheckboxSelectMultiple

from .models import TelegramUser, TelegramVideo, VideoNotification, SingleVideoToSend


class TelegramUserAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }


admin.site.register(TelegramUser, TelegramUserAdmin)
admin.site.register(TelegramVideo)
admin.site.register(VideoNotification)
admin.site.register(SingleVideoToSend)
