import django_rq
from django.db import models

from aiogram.types import User

from apps.main.models import YoutubeVideo
from apps.main.mixins import CreatedUpdatedMixin


class TelegramUser(CreatedUpdatedMixin):
    telegram_id = models.BigIntegerField(primary_key=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    username = models.CharField(max_length=100, blank=True, null=True)

    subscriptions = models.ManyToManyField('main.YoutubeChannel', related_name='+')

    def __str__(self):
        parts = []

        if self.first_name:
            parts.append(self.first_name)

        if self.last_name:
            parts.append(self.last_name)

        if self.username:
            parts.append(f'({self.username})')

        parts.append(f'[{self.telegram_id}]')

        return ' '.join(parts)

    @staticmethod
    async def get_or_create_from_telegram_user(tg_user: User):
        try:
            user = await TelegramUser.objects.aget(pk=tg_user.id)
        except TelegramUser.DoesNotExist:
            user = await TelegramUser.objects.acreate(
                pk=tg_user.id,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
                username=tg_user.username
            )

        return user


class TelegramVideo(CreatedUpdatedMixin):
    video = models.ForeignKey('main.YoutubeVideo', on_delete=models.CASCADE)
    telegram_file_id = models.CharField(max_length=200)
    sent_to = models.ManyToManyField(TelegramUser, through='VideoNotification', related_name='videos')

    def __str__(self):
        return str(self.video)


class VideoNotification(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    video = models.ForeignKey(TelegramVideo, on_delete=models.CASCADE)


class SingleVideoToSend(CreatedUpdatedMixin):
    video = models.ForeignKey('main.YoutubeVideo', on_delete=models.CASCADE)
    send_to = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    is_sent = models.BooleanField(default=False)

    @staticmethod
    async def schedule_to_send(url: str, user: TelegramUser) -> YoutubeVideo | None:
        if 'youtube.com' not in url or 'youtu.be' not in url:
            return

        video = await YoutubeVideo.objects.acreate(url=url)
        SingleVideoToSend.objects.acreate(video=video, user=user)

        return video
