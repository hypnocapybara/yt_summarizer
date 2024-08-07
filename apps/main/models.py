from dataclasses import dataclass
from django.db import models
from pydub import AudioSegment

from .mixins import CreatedUpdatedMixin


class YoutubeChannel(models.Model):
    url = models.URLField()
    enabled = models.BooleanField(default=True)
    title = models.CharField(max_length=200, blank=True, null=True)
    last_parsed_at = models.DateTimeField(blank=True, null=True)
    voice_file = models.FileField(upload_to='channels/', blank=True, null=True)

    class Meta:
        verbose_name = 'Youtube Channel'
        verbose_name_plural = 'Youtube Channels'

    def __str__(self):
        return self.title or self.url


class YoutubeVideo(CreatedUpdatedMixin):
    channel = models.ForeignKey(YoutubeChannel, on_delete=models.SET_NULL, blank=True, null=True)
    url = models.URLField()
    youtube_id = models.CharField(max_length=100, blank=True, null=True)
    title = models.CharField(max_length=200, blank=True, null=True)
    chapters = models.JSONField(default=list, blank=True)
    audio_file = models.FileField(upload_to='videos/audio/', blank=True, null=True)
    transcription = models.TextField(blank=True, null=True)
    transcription_language = models.CharField(max_length=10, blank=True, null=True)
    transcription_segments = models.JSONField(default=list, blank=True)
    summary = models.TextField(blank=True, null=True)
    voiced_summary = models.FileField(upload_to='videos/voiced/', blank=True, null=True)

    class Meta:
        verbose_name = 'Youtube Video'
        verbose_name_plural = 'Youtube Videos'

    def __str__(self):
        return self.title or self.url

    def get_duration(self) -> int | None:
        if self.transcription_segments:
            return int(self.transcription_segments[-1]["end"])

        if self.audio_file:
            audio = AudioSegment.from_file(self.audio_file.path)
            return int(audio.duration_seconds)

        return None


@dataclass
class Chapter:
    title: str
    start: int
    time_label: str
    lines: list[str]
