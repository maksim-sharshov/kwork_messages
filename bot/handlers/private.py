import re

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, BotCommandScopeChat

from bot.filters.chat import IsPrivate
from bot.filters.admin import IsManager
from bot.templates import commands as tcommands
from core.bot import bot
from db.psql.models.models import User
from settings import settings

router = Router()
router.message.filter(IsPrivate())
router.callback_query.filter(IsPrivate())


@router.message(Command('start'))
async def start_command(msg: Message, state: FSMContext):
    """
        Команда start
    :param msg: Message
    :param state: FSMContext
    :return:
    """
    user = await User.get(tg_id=msg.from_user.id)
    if not user:
        await User.create(
            tg_id=msg.from_user.id,
            username=msg.from_user.username
        )

    await msg.answer(
        text=tcommands.start_text
    )

#
# @router.message(Command('project'))
# async def project_command(msg: Message, state: FSMContext):
#     """
#         Команда project для получения актуального номера проекта
#     :param msg: Message
#     :param state: FSMContext
#     :return:
#     """
#     await bot.set_my_commands(
#         commands=settings.bot.COMMANDS + settings.bot.MANAGER_COMMANDS,
#         scope=BotCommandScopeChat(chat_id=msg.chat.id)
#     )
#
#     projects = await otask.get_projects()
#     project_id_list = []
#
#     for data in projects['projects']:
#         project_id = data['name'][-4:]
#         project_id = re.sub(r'\D', '', project_id)
#         if project_id:
#             project_id_list.append(int(project_id))
#
#     await msg.answer(
#         text=tcommands.last_project_text.format(
#             project_id=max(project_id_list)
#         )
#     )
