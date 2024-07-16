import urllib.parse as urlparse
from urllib.parse import urlencode

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile
from aiogram.utils.markdown import hbold, hlink
from asgiref.sync import async_to_sync
from django.conf import settings
from django_rq import job
from typing import TYPE_CHECKING

from apps.main.utils import split_chaptered_summary_into_parts
from apps.telegram.models import TelegramUser, TelegramVideo, VideoNotification, SingleVideoToSend

if TYPE_CHECKING:
    from apps.main.models import YoutubeVideo


MAX_MESSAGE_LEN = 4000


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
    bot = Bot(settings.TELEGRAM_BOT_TOKEN)
    telegram_video = TelegramVideo.objects.filter(video=video).first()

    result = sync_async_send_video_to_user(bot, telegram_video, video, user)

    if not telegram_video and result:
        telegram_video = TelegramVideo.objects.create(video=video, telegram_file_id=result.audio.file_id)
        VideoNotification.objects.create(video=telegram_video, user=user)


async def async_send_video_to_user(
        bot: Bot, telegram_video: TelegramVideo | None, video: 'YoutubeVideo', user: TelegramUser
):
    if video.chapters and video.summary:
        await send_summary_by_chapters(bot, video, user)
    else:
        await send_summary_by_limit(bot, video, user)

    if telegram_video:
        result = await bot.send_audio(
            user.telegram_id,
            telegram_video.telegram_file_id,
            caption=video.title
        )
    elif video.voiced_summary:
        result = await bot.send_audio(
            user.telegram_id,
            FSInputFile(video.voiced_summary.path),
            caption=video.title
        )
    else:
        result = None

    # Since we create a new bot instance and session, we should close it, to avoid asyncio warnings
    await bot.session.close()

    return result


async def send_summary_by_chapters(bot: Bot, video: 'YoutubeVideo', user: TelegramUser):
    def video_url_with_timestamp(timestamp: int) -> str:
        params = {'t': str(timestamp)}

        url_parts = list(urlparse.urlparse(video.url))
        query = dict(urlparse.parse_qsl(url_parts[4]))
        query.update(params)

        url_parts[4] = urlencode(query)

        return str(urlparse.urlunparse(url_parts))

    chapters = split_chaptered_summary_into_parts(video.summary)
    chapters_as_text = []
    for chapter in chapters:
        url = video_url_with_timestamp(chapter.start)
        time_part = f'[{chapter.time_label}]'
        header = hlink(time_part, url) + ' ' + chapter.title
        chapters_as_text.append(header + '\n' + '\n'.join(chapter.lines))

    buffer = f'{hbold(video.title)}\n{video.url}'
    for chapter in chapters_as_text:
        if len(buffer) + len(chapter) > MAX_MESSAGE_LEN:
            await bot.send_message(user.telegram_id, buffer, parse_mode=ParseMode.HTML)
            buffer = ''
        else:
            buffer = buffer + '\n\n' + chapter

    if buffer:
        await bot.send_message(user.telegram_id, buffer, parse_mode=ParseMode.HTML)


async def send_summary_by_limit(bot: Bot, video: 'YoutubeVideo', user: TelegramUser):
    formatted = f'{hbold(video.title)}\n{video.url}\n\n{video.summary}'

    for i in range(0, len(formatted), MAX_MESSAGE_LEN):
        await bot.send_message(user.telegram_id, formatted[i:i + MAX_MESSAGE_LEN], parse_mode=ParseMode.HTML)


sync_async_send_video_to_user = async_to_sync(force_new_loop=True)(async_send_video_to_user)


@job('default')
def notify_video_progress(video: 'YoutubeVideo', message: str):
    video_requests = SingleVideoToSend.objects.filter(video=video, is_sent=False)
    if video_requests.count() == 0:
        return

    bot = Bot(settings.TELEGRAM_BOT_TOKEN)
    telegram_users = [video_request.send_to for video_request in video_requests]
    _async_send_message_to_users(bot, telegram_users, message)


@async_to_sync(force_new_loop=True)
async def _async_send_message_to_users(bot: Bot, users: list[TelegramUser], message: str):
    for user in users:
        await bot.send_message(user.telegram_id, message)

    await bot.session.close()
