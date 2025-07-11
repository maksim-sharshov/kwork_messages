from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from settings import settings

default = DefaultBotProperties(
    parse_mode=ParseMode.HTML
)

bot = Bot(
    token=settings.bot.TOKEN,
    default=default
)
