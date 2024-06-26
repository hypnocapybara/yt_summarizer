from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from asgiref.sync import sync_to_async

import django_rq

from apps.telegram.middlewares import UserMiddleware
from apps.telegram.models import TelegramUser, SingleVideoToSend
from apps.main.models import YoutubeVideo


async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {hbold(message.from_user.full_name)}, you have registered!")


async def message_handler(message: types.Message, user: TelegramUser) -> None:
    if not message.link_preview_options:
        await message.answer("Send me the YouTube video URL!")
        return

    url = message.link_preview_options.url
    video = await SingleVideoToSend.schedule_to_send(url, user)
    if not video:
        await message.answer("Bad URL!")
        return

    await _schedule_video_for_processing(video)
    await message.answer("Scheduled for processing!")


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
