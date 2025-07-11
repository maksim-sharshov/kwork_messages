import asyncio
import logging

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommandScopeDefault

from core.bot import bot
from db.crud.base import create_tables
from bot.handlers import routers
from settings import settings

dp = Dispatcher(
    bot=bot,
    storage=MemoryStorage()
)
dp.include_routers(
    *routers
)


async def startup(bot: Bot) -> None:
    """
        Активируется при выключении
    :param bot: Bot
    :return:
    """
    logging.basicConfig(level=logging.INFO)

    await create_tables()
    await bot.set_my_commands(
        commands=settings.bot.COMMANDS,
        scope=BotCommandScopeDefault()
    )
    await bot.delete_webhook()


async def shutdown(bot: Bot) -> None:
    """
        Активируется при выключении
    :param bot: Bot
    :return:
    """
    await bot.close()
    await dp.stop_polling()


async def main() -> None:
    """
        Запускает проект
    :return:
    """
    dp.shutdown.register(shutdown)
    dp.startup.register(startup)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
