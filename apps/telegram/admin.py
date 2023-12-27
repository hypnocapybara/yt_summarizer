from django.contrib import admin

from .models import TelegramUser, TelegramVideo


admin.site.register(TelegramUser)
admin.site.register(TelegramVideo)
