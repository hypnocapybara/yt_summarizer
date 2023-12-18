from django.contrib import admin

from .models import YoutubeChannel, YoutubeVideo

admin.site.register(YoutubeChannel)
admin.site.register(YoutubeVideo)
