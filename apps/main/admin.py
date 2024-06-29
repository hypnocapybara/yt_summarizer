from django.contrib import admin

from .models import YoutubeChannel, YoutubeVideo
from .tasks import parse_video


@admin.action(description="Enable selected channels")
def channels_enable(modeladmin, request, queryset):
    queryset.update(enabled=True)


@admin.action(description="Disable selected channels")
def channels_disable(modeladmin, request, queryset):
    queryset.update(enabled=False)


@admin.register(YoutubeChannel)
class YoutubeChannelAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'enabled']
    actions = [channels_enable, channels_disable]


@admin.action(description="Run the pipeline")
def videos_run_pipeline(modeladmin, request, queryset):
    for video in queryset:
        parse_video.delay(video)


@admin.register(YoutubeVideo)
class YoutubeVideoAdmin(admin.ModelAdmin):
    actions = [videos_run_pipeline]
