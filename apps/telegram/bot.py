from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold

from apps.telegram.middlewares import UserMiddleware


async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {hbold(message.from_user.full_name)}, you have registered!")


async def echo_handler(message: types.Message) -> None:
    try:
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        await message.answer("Nice try!")


async def run_bot(token: str) -> None:
    dp = Dispatcher()

    dp.message(CommandStart())(command_start_handler)
    dp.message()(echo_handler)

    bot = Bot(token, parse_mode=ParseMode.HTML)
    dp.message.middleware(UserMiddleware())
    await dp.start_polling(bot)
