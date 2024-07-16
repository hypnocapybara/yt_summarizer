from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from asgiref.sync import sync_to_async

import django_rq
from django.conf import settings
from pytubefix import YouTube

from apps.telegram.middlewares import UserMiddleware
from apps.telegram.models import TelegramUser, SingleVideoToSend
from apps.main.models import YoutubeVideo
from apps.telegram.tasks import async_send_video_to_user


async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {hbold(message.from_user.full_name)}, you have registered!")


async def message_handler(message: types.Message, user: TelegramUser) -> None:
    if not message.link_preview_options:
        await message.answer("Send me the YouTube video URL!")
        return

    url = message.link_preview_options.url

    if 'youtube.com' not in url and 'youtu.be' not in url:
        await message.answer("Bad URL!")
        return

    if not user.enabled:
        await message.answer("You are not enabled user!")
        return

    youtube_video = YouTube(url)
    video_id = youtube_video.video_id

    try:
        video = await YoutubeVideo.objects.aget(youtube_id=video_id)
    except YoutubeVideo.DoesNotExist:
        video = await YoutubeVideo.objects.acreate(url=url)
        await SingleVideoToSend.objects.acreate(video=video, send_to=user)
        await _schedule_video_for_processing(video)
        await message.answer("Scheduled for processing!")
        return

    # Existing video
    if video.summary:
        bot = Bot(settings.TELEGRAM_BOT_TOKEN)
        await async_send_video_to_user(bot, None, video, user)
    else:
        await message.answer("Video is already being processed! You should get it soon (hopefully)")
        await SingleVideoToSend.objects.acreate(video=video, send_to=user)


@sync_to_async
def _schedule_video_for_processing(video: YoutubeVideo):
    queue = django_rq.get_queue('default')
    queue.enqueue('apps.main.tasks.parse_video', video)


async def run_bot(token: str) -> None:
    dp = Dispatcher()

    dp.message(CommandStart())(command_start_handler)
    dp.message()(message_handler)

    bot = Bot(token)
    dp.message.middleware(UserMiddleware())
    await dp.start_polling(bot)
