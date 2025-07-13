from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram import types

from bot.filters.chat import IsGroup
from core.logger import logger
from db.psql.models.models import Chat, Account, Message
from integrations.kwork import KworkAccount

router = Router()
router.message.filter(IsGroup())
router.callback_query.filter(IsGroup())


@router.message(F.text)
async def msg_to_customer_handler(msg: types.Message, state: FSMContext):
    """
        Пересылает сообщение в кворк чат
    :param msg: Message
    :param state: FSMContext
    :return:
    """
    chat = await Chat.get(
        tg_chat_id=msg.chat.id,
        tg_topic_id=msg.message_thread_id
    )
    account = await Account.get(id=chat.account_id)
    kwork_account = KworkAccount(cookie=account.cookie)

    kwork_message = await kwork_account.send_message(
        user_id=chat.kwork_user_id,
        text=msg.text
    )

    logger.info('New message in Topic %s. Message: %s', chat.title, msg.text)

    if kwork_message.get('status') == 'error':
        return await msg.answer(
            text='🤖: ' + kwork_message['response']
        )

    await Message.create(
        kwork_user_id=0,
        username=kwork_account.name,
        kwork_msg_id=kwork_message['MID'],
        tg_msg_id=msg.message_id,
        text=msg.text
    )
