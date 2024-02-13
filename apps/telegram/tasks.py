from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile
from aiogram.utils.markdown import hbold
from asgiref.sync import async_to_sync
from django.conf import settings
from django_rq import job
from typing import TYPE_CHECKING

from apps.telegram.models import TelegramUser, TelegramVideo, VideoNotification, SingleVideoToSend

if TYPE_CHECKING:
    from apps.main.models import YoutubeVideo


@job('default')
def send_video_notifications(video: 'YoutubeVideo'):
    subscribers = TelegramUser.objects.filter(subscriptions=video.channel)
    if subscribers.count() == 0:
        _send_video_single_requests.delay(video)
        return

    # If it is a first send, we have no TelegramVideo.
    # And to avoid race condition between multiple workers, it is better to make sure TelegramVideo is created
    # before calling parallel tasks
    first_user = subscribers[0]
    send_video_to_user(video, first_user)

    for subscriber in subscribers[1:]:
        send_video_to_user.delay(video, subscriber)

    _send_video_single_requests.delay(video)


@job('default')
def _send_video_single_requests(video: 'YoutubeVideo'):
    video_requests = SingleVideoToSend.objects.filter(video=video, is_sent=False)
    if video_requests.count() == 0:
        return

    first_request = video_requests[0]
    send_video_to_user(video, first_request.send_to)
    first_request.is_sent = True
    first_request.save()

    for video_request in video_requests[1:]:
        send_video_to_user.delay(video, video_request.send_to)
        video_request.is_sent = True
        video_request.save()


@job('default')
def send_video_to_user(video: 'YoutubeVideo', user: TelegramUser):
    bot = Bot(settings.TELEGRAM_BOT_TOKEN, parse_mode=ParseMode.HTML)
    telegram_video = TelegramVideo.objects.filter(video=video).first()

    result = _async_send_video_to_user(bot, telegram_video, video, user)

    if not telegram_video:
        telegram_video = TelegramVideo.objects.create(video=video, telegram_file_id=result.audio.file_id)

    VideoNotification.objects.create(video=telegram_video, user=user)


@async_to_sync(force_new_loop=True)
async def _async_send_video_to_user(
        bot: Bot, telegram_video: TelegramVideo | None, video: 'YoutubeVideo', user: TelegramUser
):
    formatted = f'{hbold(video.title)}\n{video.url}\n\n{video.summary}'

    for i in range(0, len(formatted), 4000):
        await bot.send_message(user.telegram_id, formatted[i:i+4000])

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

    # Since we create a new bot instance and session, we should close it, to avoid asyncio warnings
    await bot.session.close()

    return result
