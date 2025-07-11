import asyncio
import random

from aiogram.client.session import aiohttp
from aiogram.types import BufferedInputFile, ReactionTypeEmoji

from integrations.templates import work_time_text
from core.bot import bot
from core.logger import manager_logger as logger
from db.models.models import Account, Chat, Message
from integrations.kwork import KworkAccount
from manager.base import BaseManager
from settings import settings
from utils.kwork import msg_in_chat, split_text_by_length
from utils.time import weekend_time


class KworkManager(BaseManager):
    timeout = 40

    async def run(self):
        logger.info('=== Kwork Manager is running ===')
        while True:
            try:
                await self.task()

            except Exception as e:
                logger.exception("Error on Kwork Manager run: %s", e)

            await asyncio.sleep(self.timeout)

    async def task(self):
        logger.info("=== Kwork Manager run task ===")

        accounts: list[Account] = await Account.all()

        for account in accounts:
            try:
                account_kwork = KworkAccount(cookie=account.cookie)

                if not account.username:
                    await account.update(username=account_kwork.name)

                dialogs = await account_kwork.get_dialogs()
                dialogs['data']['rows'] = dialogs['data']['rows'][:5]

                logger.info('Подключился к %s', account_kwork.account_url)

                # Создание топиков для всех диалогов
                await self.create_topic(
                    account_username=account_kwork.name,
                    account_id=account.id,
                    dialogs=dialogs['data']['rows']
                )

                # Проверка новых сообщений в чате
                unprocessed_messages = await self.check_messages(
                    dialogs=dialogs['data']['rows'],
                    kwork_account=account_kwork
                )

                logger.info('Не прочитанных сообщений: %d', len(unprocessed_messages))

                # Ответ на не прочитанные сообщения
                await self.process_messages(
                    messages=unprocessed_messages,
                    kwork_account=account_kwork,
                    account_id=account.id
                )

                await asyncio.sleep(random.uniform(1, 3))

            except Exception as e:
                logger.exception('Error Kwork Manager. Account ID: %d. Error: %s', account.id, e)

    async def process_messages(self, messages: list[dict], kwork_account: KworkAccount, account_id: int) -> None:
        """
        Обрабатывает все новые сообщения
        :param messages: Не обработанные сообщения
        :param kwork_account: KworkAccount
        :return:
        """
        for message in messages:
            if message['mfrom'].lower() == kwork_account.name.lower():
                chat = await Chat.get(
                    kwork_user_id=int(message['MSGTO']),
                    account_id=account_id
                )
            else:
                chat = await Chat.get(
                    kwork_user_id=int(message['MSGFROM']),
                    account_id=account_id
                )

            # Пересылаем сообщение в топик
            tg_msg = Message

            try:
                if (text := message.get('message', None)) and not message.get('filesArray', None):
                    for text_part in split_text_by_length(text):
                        tg_msg = await bot.send_message(
                            chat_id=chat.tg_chat_id,
                            message_thread_id=chat.tg_topic_id,
                            text=text_part,
                            parse_mode=None
                        )

                elif files := message['filesArray']:
                    for file in files:
                        # Взять контент медиа файла
                        async with aiohttp.ClientSession(headers=kwork_account.headers) as session:
                            async with session.get(file['path']) as response:
                                content = await response.read()
                                status = response.status

                        # Если фотография
                        if file['path'].lower().endswith('.jpg') or file['path'].lower().endswith('.png'):
                            if status == 200:
                                photo = BufferedInputFile(
                                    file=content,
                                    filename=f'{random.randint(0, 9999)}.png'
                                )
                                tg_msg = await bot.send_photo(
                                    chat_id=chat.tg_chat_id,
                                    message_thread_id=chat.tg_topic_id,
                                    photo=photo,
                                    parse_mode=None
                                )
                            else:
                                logger.error(f"Status code {status}, response - {content}")
                                continue

                        # Если файл
                        else:
                            if status == 200:
                                document = BufferedInputFile(
                                    file=content,
                                    filename=file['path'].split('/')[-1]
                                )
                                tg_msg = await bot.send_document(
                                    chat_id=chat.tg_chat_id,
                                    message_thread_id=chat.tg_topic_id,
                                    document=document,
                                    parse_mode=None
                                )
                            else:
                                logger.error(f"Status code {status}, response - {content}")
                                continue

                    if text := message.get('message', None):
                        for text_part in split_text_by_length(text):
                            tg_msg = await bot.send_message(
                                chat_id=chat.tg_chat_id,
                                message_thread_id=chat.tg_topic_id,
                                text=text_part,
                                parse_mode=None
                            )

                await Message.create(
                    kwork_user_id=int(message['MSGFROM']),
                    username=message['mfrom'],
                    kwork_msg_id=message['MID'],
                    tg_msg_id=tg_msg.message_id,
                    text=work_time_text,
                )
                logger.info('Message resented to Telegram')

            except Exception as e:
                logger.error("Error on process_messages: %s", e)

            await asyncio.sleep(3)

    async def check_messages(self, dialogs: list[dict], kwork_account: KworkAccount) -> list[dict]:
        """
        Собирает все новые сообщения от клиентов, устойчиво обрабатывая сбои
        :param dialogs: Диалоги на аккаунте
        :return: Все не прочитанные сообщения
        """
        result = []

        for dialog in dialogs:
            user_id = dialog.get('user_id')
            username = dialog.get('username', 'UNKNOWN')

            if not user_id:
                logger.warning(f"[check_messages] Пропущен диалог без user_id: {dialog}")
                continue

            messages = await kwork_account.get_chat_messages(user_id=user_id)

            if not messages:
                logger.warning(f"[check_messages] Нет ответа от get_chat_messages для user_id={user_id}")
                continue

            if not isinstance(messages, dict) or "data" not in messages or "messages" not in messages["data"]:
                logger.warning(f"[check_messages] Структура ответа неожиданна для user_id={user_id}: {messages}")
                continue

            chat_messages = messages["data"]["messages"]

            # Проверяем, отправлялось ли сообщение про выходной
            try:
                answered = msg_in_chat(messages=chat_messages, text=work_time_text)

                if weekend_time() and dialog.get('unread_count', 0) > 0 and not answered:
                    try:
                        kwork_msg = await kwork_account.send_message(
                            user_id=int(user_id),
                            text=work_time_text
                        )
                        logger.info('Sent weekend time message to %s', username)
                    except Exception as e:
                        logger.error(f"[check_messages] Ошибка при отправке выходного сообщения {username}: {e}")
                        kwork_msg = None
                else:
                    kwork_msg = None
            except Exception as e:
                logger.error(f"[check_messages] Ошибка в msg_in_chat или логике выходного: {e}")
                continue

            for message in chat_messages:
                try:
                    msg_in_bot = await Message.get(kwork_msg_id=message['MID'])

                    if not msg_in_bot:
                        result.append(message)
                        continue

                    if message.get('unread') == 0 and not msg_in_bot.viewed:
                        if message['mfrom'].lower() == kwork_account.name:
                            try:
                                await bot.set_message_reaction(
                                    chat_id=settings.bot.CHAT_ID,
                                    message_id=msg_in_bot.tg_msg_id,
                                    reaction=[ReactionTypeEmoji(emoji='👀')]
                                )
                                await msg_in_bot.update(viewed=True)
                                logger.info('Set message viewed')
                            except Exception as e:
                                logger.error(f'Error set reaction: {e}')

                            await asyncio.sleep(3)

                except Exception as e:
                    logger.error(f"[check_messages] Ошибка при обработке сообщения от {username}: {e}")
                    msg_in_bot = None

            await asyncio.sleep(random.uniform(0.5, 1.5))  # для защиты от блоков

        return result

    async def create_topic(self, account_username: str, account_id: int, dialogs: list[dict]) -> None:
        """
            Для каждого диалога в кворк создаёт свой топик в группе
        :param account_username: Username аккаунта
        :param account_id: Account id
        :param dialogs: Диалоги
        :return:
        """
        for dialog in dialogs:
            if await Chat.get(
                    kwork_user_id=dialog['user_id'],
                    account_id=account_id
            ):
                continue

            topic_title = f'K | {dialog['username']} | {account_username}'

            topic = await bot.create_forum_topic(
                chat_id=settings.bot.CHAT_ID,
                name=topic_title
            )

            chat = await Chat.create(
                kwork_user_id=dialog['user_id'],
                tg_chat_id=settings.bot.CHAT_ID,
                tg_topic_id=topic.message_thread_id,
                title=topic_title,
                account_id=account_id
            )

            logger.info('Создал новый чат: %s', chat.title)

            await asyncio.sleep(3)
