import asyncio
import logging

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommandScopeDefault

from core.bot import bot
from settings import settings
from bot.handlers import routers
from db.psql.crud.base import create_tables
from services.report_timer import reporter_loop


dp = Dispatcher(
    bot=bot,
    storage=MemoryStorage()
)
dp.include_routers(
    *routers
)


async def startup(bot: Bot) -> None:
    """
    Выполняется при запуске бота
    """
    logging.basicConfig(level=logging.INFO)

    # Инициализация таблиц PostgreSQL
    await create_tables()

    asyncio.create_task(reporter_loop()) # Фоновая задача

    # Команды и webhook
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
