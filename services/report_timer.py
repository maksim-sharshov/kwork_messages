import asyncio

from core.bot import bot
from core.logger import notification_loger
from integrations.kwork import KworkAccount
from db.psql.models.models import Message, Account, Chat, ManagerMode

async def run_one_minutes():
    
    notification_loger.info("🚀 Активируем задачу.")
    await check_for_ignore()

    notification_loger.info("🔁 Запущено ожидание 1 минуты")
    await asyncio.sleep(60)
    

async def check_for_ignore():

    """
    Отправляет сообщения клиентом о том, актуален ли проект
    """

    all_kwork_user_ignore = await Message.get_users_for_reminder()

    for user_id in all_kwork_user_ignore:

        try:

            # Если ИИ отключён, то пропускаем
            info_user = await ManagerMode.get(kwork_user_id=user_id)
            if info_user and info_user.flag:
                continue

            # Данные + отправка сообщения
            chat = await Chat.get(kwork_user_id=user_id)
            account = await Account.get(id=chat.account_id)
            kwork_account = KworkAccount(cookie=account.cookie)

            text = 'Подскажите пожалуйста, ваш проект ещё актуален?'
            kwork_message = await kwork_account.send_message(
                user_id=chat.kwork_user_id,
                text=text
            )

            tg_msg = await bot.send_message(
                chat_id=chat.tg_chat_id,
                message_thread_id=chat.tg_topic_id,
                text='<u><b>GPT:</b></u> '+ text,
                parse_mode='HTML'
            )

            # Сохраняем сообщение
            recipient_id = kwork_message.get('MSGTO')
            await Message.create(
                kwork_user_id=0,
                recipient_kwork_user_id=recipient_id,
                username=kwork_account.name,
                kwork_msg_id=kwork_message['MID'],
                tg_msg_id=tg_msg.message_id,
                text=text
            )

        except Exception as e:
            notification_loger.error(f"Произошла ошибка при отправке уведомления пользователю {chat.kwork_user_id}: {e}")
        
            
# Главный цикл репортера, запускается раз в 1 минуту
async def reporter_loop():
    while True:
        try:
            await run_one_minutes()

        except Exception as e:
            notification_loger.error(f"Произошла ошибка: {e}")
