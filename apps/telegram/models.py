from django.db import models

from aiogram.types import User


class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
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
    async def from_telegram_user(tg_user: User):
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
