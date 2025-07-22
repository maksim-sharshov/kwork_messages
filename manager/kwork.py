import asyncio
import random

from aiogram.client.session import aiohttp
from aiogram.types import BufferedInputFile, ReactionTypeEmoji

from integrations.templates import work_time_text
from core.bot import bot
from core.logger import manager_logger as logger, dialogs_logger, error_logger
from db.psql.models.models import Account, Chat, Message, ManagerMode
from db.redis.models.models import MessageAI
from integrations.kwork import KworkAccount
from integrations.openai import GPTHandler
from manager.base import BaseManager
from settings import settings
from utils.kwork import msg_in_chat, split_text_by_length, DocumentParser, clean_text
from utils.time import weekend_time


GPT_PARAMETER = True


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

                # Проверка новых сообщений в чате
                unprocessed_messages = await self.check_messages(
                    dialogs=dialogs['data']['rows'],
                    kwork_account=account_kwork
                )

                logger.info('Не прочитанных сообщений: %d', len(unprocessed_messages))

                # Обновление записи для менеджер/ии
                await self.update_flag_and_check(
                    account_id=account.id,
                    dialogs=dialogs['data']['rows']
                ) 

                # Создание топиков для всех диалогов
                await self.create_topic(
                    account_username=account_kwork.name,
                    account_id=account.id,
                    dialogs=dialogs['data']['rows']
                )

                # Ответ на не прочитанные сообщения (обработка с помощью ИИ)
                await self.process_message_ai(
                    messages=unprocessed_messages,
                    kwork_account=account_kwork,
                    account_id=account.id
                )

                # Ответ на не прочитанные сообщения (обработка менеджером)
                await self.process_messages(
                    messages=unprocessed_messages,
                    kwork_account=account_kwork,
                    account_id=account.id
                )     

                await asyncio.sleep(random.uniform(1, 3))

            except Exception as e:
                logger.exception('Error Kwork Manager. Account ID: %d. Error: %s', account.id, e)

    async def process_message_ai(self, messages: list[dict], kwork_account: KworkAccount, account_id: int) -> None:
        """
        Обрабатывает все новые сообщения с помощью ИИ
        :param messages: Не обработанные сообщения
        :param kwork_account: KworkAccount
        :return:
        """

        if not GPT_PARAMETER:
            return

        for message in messages:
            
            recipient_id = message.get('MSGTO')
            if message['mfrom'].lower() == kwork_account.name.lower():
                kwork_user_id = int(message['MSGTO'])
            else:
                kwork_user_id = int(message['MSGFROM'])

            # Если уже сделан перевод на менеджера
            info_user = await ManagerMode.get(kwork_user_id=kwork_user_id)
            if info_user and info_user.flag:
                continue
            
            # Если это наше ссообщение
            if recipient_id == kwork_user_id:
                continue

            chat = await Chat.get(
                kwork_user_id=kwork_user_id,
                account_id=account_id
            )

            user_message = ""
            document_text = ""

            try:
                # ===== Обработка файлов, если они есть =====
                if files := message.get('filesArray'):
                    for file in files:
                        async with aiohttp.ClientSession(headers=kwork_account.headers) as session:
                            async with session.get(file['path']) as response:
                                content = await response.read()
                                status = response.status

                        if status != 200:
                            logger.error(f"Ошибка загрузки файла {file['path']}. Status: {status}")
                            continue

                        filename = file['path'].split('/')[-1]
                        text_from_file = DocumentParser.extract_text(content, filename)

                        if not text_from_file:

                            await bot.send_message(
                                chat_id=chat.tg_chat_id,
                                message_thread_id=chat.tg_topic_id,
                                text='🚨 Новый заказ\n\n Неизвестный документ',
                                parse_mode=None
                            )

                            await info_user.update(flag=True)
                            await MessageAI.delete_all_for_user(user_id=kwork_user_id)
                            return

                        # Отправляем сам файл (всегда)
                        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif')):
                            photo = BufferedInputFile(
                                file=content,
                                filename=filename
                            )
                            await bot.send_photo(
                                chat_id=chat.tg_chat_id,
                                message_thread_id=chat.tg_topic_id,
                                photo=photo
                            )
                        else:
                            document = BufferedInputFile(
                                file=content,
                                filename=filename
                            )
                            await bot.send_document(
                                chat_id=chat.tg_chat_id,
                                message_thread_id=chat.tg_topic_id,
                                document=document
                            )
                            
                # ===== Обработка обычного текста =====
                if (text := message.get('message', None)):
                    user_message = text

            except Exception as e:
                logger.error(f"Ошибка обработки сообщения {message.get('MID')}: {e}")
                error_logger.error(f"Ошибка обработки сообщения {message.get('MID')}: {e}")
                continue

            # ===== Создаём запись сообщения в БД =====
            response_time = "Не работаем, сейчас выходное время." if weekend_time() else "Работаем, сейчас рабочее время."
            full_input_text = clean_text(user_message + "\n" + document_text + "\n" + response_time )
            for part in split_text_by_length(full_input_text):

                # Отправляем сообщение в ТГ
                tg_msg = await bot.send_message(
                    chat_id=chat.tg_chat_id,
                    message_thread_id=chat.tg_topic_id,
                    text='<u><b>USER:</b></u> ' + user_message,
                    parse_mode='HTML'
                )

                # Сохраняем для ИИ
                await MessageAI.create(
                    kwork_user_id=kwork_user_id,
                    recipient_id=1,
                    sender='user',
                    content=full_input_text
                )

                # Фиксируем, что сообщение прочитано
                await Message.create(
                    kwork_user_id=kwork_user_id,
                    username=message['mfrom'],
                    kwork_msg_id=message['MID'],
                    tg_msg_id=tg_msg.message_id if tg_msg else 0,
                    text=full_input_text,
                    viewed=True
                )

                dialogs_logger.info(f'Пользователь {kwork_user_id} написал gpt: {user_message}')
            
            # Задержка для симуляции живого общения
            await asyncio.sleep(random.uniform(5, 40))

            # Запрос в gpt
            gpt = GPTHandler(kwork_user_id=kwork_user_id, recipient_id=recipient_id)
            answer, application = await gpt.generate_response()

            kwork_message = await kwork_account.send_message(
                user_id=kwork_user_id,
                text=answer
            )
            dialogs_logger.info(f'GPT ответил пользователю {kwork_user_id}: {answer}')

            # Отправляем сообщение в ТГ
            tg_msg = await bot.send_message(
                chat_id=chat.tg_chat_id,
                message_thread_id=chat.tg_topic_id,
                text='<u><b>GPT:</b></u> ' + answer,
                parse_mode='HTML'
            )

            # Сохраняем для ИИ
            await MessageAI.create(
                kwork_user_id=1,
                recipient_id=kwork_user_id,
                sender='ai',
                content=answer
            )  

            # Фиксируем, что сообщение прочитано
            await Message.create(
                kwork_user_id=1,
                username=kwork_message.get('mfrom', ''),
                kwork_msg_id=kwork_message.get('MID', 1),
                tg_msg_id=tg_msg.message_id if tg_msg else 0,
                text=answer,
                viewed=True
            )

            if application: # Перевод на менеджера

                await bot.send_message(
                    chat_id=chat.tg_chat_id,
                    message_thread_id=chat.tg_topic_id,
                    text=application,
                    parse_mode=None
                )

                await info_user.update(flag=True)
                await MessageAI.delete_all_for_user(user_id=kwork_user_id)

    async def process_messages(self, messages: list[dict], kwork_account: KworkAccount, account_id: int) -> None:
        """
        Обрабатывает все новые сообщения
        :param messages: Не обработанные сообщения
        :param kwork_account: KworkAccount
        :return:
        """
        for message in messages:

            # Получаем id пользователя в kwork
            recipient_id = message.get('MSGTO')
            if message['mfrom'].lower() == kwork_account.name.lower():
                kwork_user_id = int(message['MSGTO'])
            else:
                kwork_user_id = int(message['MSGFROM'])

            # Если флаг info_user.flag не установлен (False), то ответ отправляет ИИ
            if GPT_PARAMETER:
                info_user = await ManagerMode.get(kwork_user_id=kwork_user_id)
                if info_user and not info_user.flag:
                    continue

            # Если это наше ссообщение
            if recipient_id == kwork_user_id:
                continue

            chat = await Chat.get(
                kwork_user_id=kwork_user_id,
                account_id=account_id
            )

            # Сохраняем сообщение в топик
            tg_msg = None
            user_message = ""

            try:
                # Если текст без файлов
                recipient_id = message.get('MSGTO')
                if (text := message.get('message', None)) and not message.get('filesArray', None):
                    for text_part in split_text_by_length(text):
                        user_message = text_part
                        tg_msg = await bot.send_message(
                            chat_id=chat.tg_chat_id,
                            message_thread_id=chat.tg_topic_id,
                            text=user_message,
                            parse_mode=None
                        )

                # Если есть файлы
                elif files := message.get('filesArray'):
                    for file in files:
                        async with aiohttp.ClientSession(headers=kwork_account.headers) as session:
                            async with session.get(file['path']) as response:
                                content = await response.read()
                                status = response.status

                        if file['path'].lower().endswith(('.jpg', '.png')):
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

                    # Отправляем текст сообщения, если он есть, после файлов
                    if text := message.get('message', None):
                        for text_part in split_text_by_length(text):
                            user_message = text_part
                            tg_msg = await bot.send_message(
                                chat_id=chat.tg_chat_id,
                                message_thread_id=chat.tg_topic_id,
                                text=user_message,
                                parse_mode=None
                            )

                # Сохраняем в базу
                await Message.create(
                    kwork_user_id=kwork_user_id,
                    username=message['mfrom'],
                    kwork_msg_id=message['MID'],
                    tg_msg_id=tg_msg.message_id if tg_msg else 0,
                    text=user_message
                )
                logger.info('Message resent to Telegram and saved in DB')

            except Exception as e:
                logger.error(f"Error processing message {message.get('MID')}: {e}")


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
            for message in chat_messages:
                try:
                    msg_in_bot = await Message.get(kwork_msg_id=message['MID'])
                    
                    if not msg_in_bot:
                        result.append(message)
                        continue

                    if message.get('unread') == 0 and not msg_in_bot.viewed:
                        if message['mfrom'].lower() == kwork_account.name:
                            if msg_in_bot.tg_msg_id is not None:
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
    
    async def update_flag_and_check(self, account_id: int, dialogs: list[dict]) -> bool:
        """
        Обновляет или создаёт запись ManagerMode с флагом для пользователя.

        :param user_id: Идентификатор пользователя.
        :param account_id: Идентификатор аккаунта.
        :return: True, если запись была создана или обновлена, иначе False.
        """
        
        for dialog in dialogs:

            user_id = dialog['user_id']
            chat_with_user = await Chat.get(kwork_user_id=user_id, account_id=account_id)
            info_user = await ManagerMode.get(kwork_user_id=user_id)

            if chat_with_user and info_user:
                return bool(info_user.flag)
            
            elif not chat_with_user and not info_user:
                await ManagerMode.create(kwork_user_id=user_id, flag=False)
                return False

            elif chat_with_user and not info_user:
                await ManagerMode.create(kwork_user_id=user_id, flag=False)
                return False
            
            elif not chat_with_user and info_user:
                return False

            return False

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