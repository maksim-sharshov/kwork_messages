from aiogram.enums import ChatType
from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery

from settings import settings


class IsPrivate(Filter):
    async def __call__(self, msg: Message | CallbackQuery) -> bool:
        if isinstance(msg, CallbackQuery):
            msg = msg.message

        return msg.chat.type == ChatType.PRIVATE


class IsGroup(Filter):
    async def __call__(self, msg: Message | CallbackQuery) -> bool:
        if isinstance(msg, CallbackQuery):
            msg = msg.message

        return msg.chat.id == settings.bot.CHAT_ID and msg.message_thread_id
