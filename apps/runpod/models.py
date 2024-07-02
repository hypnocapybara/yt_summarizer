from django.db import models

from apps.main.mixins import CreatedUpdatedMixin


class TranscriptionTask(CreatedUpdatedMixin):
    video = models.ForeignKey('main.YoutubeVideo', on_delete=models.CASCADE)
    task_id = models.CharField(max_length=100, db_index=True)
    is_completed = models.BooleanField(default=False)
