from django.contrib import admin

from .models import Speaker, Transcription

admin.site.register(Speaker)
admin.site.register(Transcription)
