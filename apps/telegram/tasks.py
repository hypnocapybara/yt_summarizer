from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile
from aiogram.utils.markdown import hbold
from asgiref.sync import async_to_sync
from django.conf import settings
from django_rq import job

from apps.main.models import YoutubeVideo
from apps.telegram.models import TelegramUser, TelegramVideo, VideoNotification


@job('default')
def send_video_notifications(video: YoutubeVideo):
    subscribers = TelegramUser.objects.filter(subscriptions=video.channel)
    if subscribers.count() == 0:
        return

    # If it is a first send, we have no TelegramVideo.
    # And to avoid race condition between multiple workers, it is better to make sure TelegramVideo is created
    # before calling parallel tasks
    first_user = subscribers[0]
    send_video_to_user(video, first_user)

    for subscriber in subscribers[1:]:
        send_video_to_user.delay(video, subscriber)


@job('default')
def send_video_to_user(video: YoutubeVideo, user: TelegramUser):
    bot = Bot(settings.TELEGRAM_BOT_TOKEN, parse_mode=ParseMode.HTML)
    telegram_video = TelegramVideo.objects.filter(video=video).first()

    result = _async_send_video_to_user(bot, telegram_video, video, user)

    if not telegram_video:
        telegram_video = TelegramVideo.objects.create(video=video, telegram_file_id=result.audio.file_id)

    VideoNotification.objects.create(video=telegram_video, user=user)


@async_to_sync(force_new_loop=True)
async def _async_send_video_to_user(bot: Bot, telegram_video: TelegramVideo, video: YoutubeVideo, user: TelegramUser):
    formatted = f'{hbold(video.title)}\n{video.url}\n\n{video.summary}'
    await bot.send_message(user.telegram_id, formatted)

    if telegram_video:
        result = await bot.send_audio(
            user.telegram_id,
            telegram_video.telegram_file_id,
            caption=video.title
        )
    else:
        result = await bot.send_audio(
            user.telegram_id,
            FSInputFile(video.voiced_summary.path),
            caption=video.title
        )

    await bot.session.close()

    return result
