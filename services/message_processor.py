"""
Абстрактные процессоры сообщений для обработки диалогов Kwork
"""

import asyncio
import random
from abc import ABC, abstractmethod

from core.bot import bot
from core.exceptions import AIProcessingError, TelegramAPIError
from core.logger import logger, dialogs_logger, error_logger
from db.psql.models.models import Chat, Message, ManagerMode
from db.redis.models.models import MessageAI
from integrations.kwork import KworkAccount
from integrations.openai import GPTHandler
from services.file_service import FileService
from settings import settings
from utils.kwork import split_text_by_length, clean_text
from utils.time import weekend_time


class MessageProcessor(ABC):
    
    """Абстрактный процессор сообщений"""

    @abstractmethod
    async def can_process(self, message: dict, account_id: int) -> bool:
        """
        Проверяет, может ли этот процессор обработать сообщение.

        :param message: Сообщение из Kwork API
        :param account_id: ID аккаунта
        :return: True если может обработать
        """
        pass

    @abstractmethod
    async def process(
        self,
        message: dict,
        kwork_account: KworkAccount,
        account_id: int
    ) -> None:
        """
        Обрабатывает сообщение.

        :param message: Сообщение из Kwork API
        :param kwork_account: Объект KworkAccount
        :param account_id: ID аккаунта
        """
        pass

    @staticmethod
    def _extract_kwork_user_id(message: dict, kwork_account_name: str) -> int:
        """
        Извлекает ID пользователя из сообщения (унификация логики).

        :param message: Сообщение
        :param kwork_account_name: Имя аккаунта
        :return: ID пользователя в Kwork
        """
        if message['mfrom'].lower() == kwork_account_name.lower():
            return int(message['MSGTO'])
        else:
            return int(message['MSGFROM'])

    @staticmethod
    async def _send_to_telegram(text: str, chat_id: int, topic_id: int) -> int | None:
        """
        Отправляет текстовое сообщение в Telegram.

        :param text: Текст сообщения
        :param chat_id: ID чата
        :param topic_id: ID топика
        :return: ID отправленного сообщения или None
        """
        try:
            for text_part in split_text_by_length(text):
                tg_msg = await bot.send_message(
                    chat_id=chat_id,
                    message_thread_id=topic_id,
                    text=text_part,
                    parse_mode=None
                )
            return tg_msg.message_id if tg_msg else None
        except Exception as e:
            raise TelegramAPIError(f"Ошибка отправки в Telegram: {e}") from e


class AIMessageProcessor(MessageProcessor):
    """Обработка сообщений с помощью ИИ (GPT)"""

    def __init__(self):
        self.enabled = settings.openai.GPT_ENABLED
        self.message_semaphore = asyncio.Semaphore(5)

    async def can_process(self, message: dict) -> bool:
        """
        Может обработать, если флаг ManagerMode не установлен (False).
        """
        kwork_user_id = int(message.get('MSGFROM') or message.get('MSGTO'))
        info_user = await ManagerMode.get(kwork_user_id=kwork_user_id)
        
        if info_user and info_user.flag or not self.enabled:
            await info_user.update(flag=True) # Если ИИ выключен вручную, то переключаем на менеджера
            return False

        return True

    async def process(
        self,
        message: dict,
        kwork_account: KworkAccount,
        account_id: int
    ) -> None:
        """
        Обрабатывает сообщение с помощью ИИ: загружает файлы, генерирует ответ, отправляет.
        """
        async with self.message_semaphore:
            try:
                recipient_id = message.get('MSGTO')
                kwork_user_id = self._extract_kwork_user_id(message, kwork_account.name)

                # Если это наше сообщение, пропускаем
                if recipient_id == kwork_user_id:
                    return

                # Получить чат
                chat = await Chat.get(
                    kwork_user_id=kwork_user_id,
                    account_id=account_id
                )
                if not chat:
                    logger.warning(f"Chat не найден для user_id={kwork_user_id}")
                    return

                # Получить или создать ManagerMode запись
                info_user = await ManagerMode.get(kwork_user_id=kwork_user_id)
                if not info_user:
                    info_user = await ManagerMode.create(kwork_user_id=kwork_user_id, flag=False)

                # Обработать файлы
                user_message = message.get('message', '')
                document_text = ''

                if files := message.get('filesArray'):
                    document_text = await FileService.process_files_from_message(
                        files,
                        kwork_account.headers,
                        chat.tg_chat_id,
                        chat.tg_topic_id
                    )

                # Формирование полного текста для GPT
                response_time = (
                    "Не работаем, сейчас выходное время."
                    if weekend_time()
                    else "Работаем, сейчас рабочее время."
                )
                full_input_text = clean_text(
                    user_message + "\n" + document_text + "\n" + response_time
                )

                # Отправить в Telegram
                for part in split_text_by_length(full_input_text):
                    tg_msg = await bot.send_message(
                        chat_id=chat.tg_chat_id,
                        message_thread_id=chat.tg_topic_id,
                        text='<u><b>USER:</b></u> ' + user_message,
                        parse_mode='HTML'
                    )

                    # Сохранить в БД
                    await MessageAI.create(
                        kwork_user_id=kwork_user_id,
                        recipient_id=1,
                        sender='user',
                        content=full_input_text
                    )

                    await Message.create(
                        kwork_user_id=kwork_user_id,
                        recipient_kwork_user_id=recipient_id,
                        username=message['mfrom'],
                        kwork_msg_id=message['MID'],
                        tg_msg_id=tg_msg.message_id if tg_msg else 0,
                        text=full_input_text,
                        viewed=True
                    )

                    dialogs_logger.info(
                        f'Пользователь {kwork_user_id} написал gpt: {user_message}'
                    )

                # Задержка перед ответом ИИ
                await asyncio.sleep(random.uniform(90, 180))

                # Генерация ответа GPT
                gpt = GPTHandler(kwork_user_id=kwork_user_id, recipient_id=recipient_id)
                answer, application = await gpt.generate_response()

                # Отправить ответ в Kwork
                kwork_message = await kwork_account.send_message(
                    user_id=kwork_user_id,
                    text=answer
                )

                dialogs_logger.info(f'GPT ответил пользователю {kwork_user_id}: {answer}')

                # Отправить ответ в Telegram
                tg_msg = await bot.send_message(
                    chat_id=chat.tg_chat_id,
                    message_thread_id=chat.tg_topic_id,
                    text='<u><b>GPT:</b></u> ' + answer,
                    parse_mode='HTML'
                )

                # Сохранить ответ в БД
                await MessageAI.create(
                    kwork_user_id=1,
                    recipient_id=kwork_user_id,
                    sender='ai',
                    content=answer
                )

                await Message.create(
                    kwork_user_id=1,
                    username=kwork_message.get('mfrom', ''),
                    recipient_kwork_user_id=recipient_id,
                    kwork_msg_id=kwork_message.get('MID', 1),
                    tg_msg_id=tg_msg.message_id if tg_msg else 0,
                    text=answer,
                    viewed=True
                )

                # Если есть заявка, отправить и установить флаг
                if application:
                    await bot.send_message(
                        chat_id=chat.tg_chat_id,
                        message_thread_id=chat.tg_topic_id,
                        text=application,
                        parse_mode=None
                    )
                    await info_user.update(flag=True)
                    await MessageAI.delete_all_for_user(user_id=kwork_user_id)

            except AIProcessingError as e:
                logger.error(f"Ошибка обработки сообщения ИИ {message.get('MID')}: {e}")
                error_logger.error(f"Ошибка обработки сообщения ИИ {message.get('MID')}: {e}")
            except Exception as e:
                logger.error(f"Неожиданная ошибка при обработке сообщения {message.get('MID')}: {e}")
                error_logger.error(f"Неожиданная ошибка {message.get('MID')}: {e}")


class ManagerMessageProcessor(MessageProcessor):
    """Обработка сообщений менеджером (без ИИ)"""

    async def can_process(self, message: dict) -> bool:
        """
        Может обработать, если флаг ManagerMode установлен (True) или нет режима ИИ.
        """
        kwork_user_id = int(message.get('MSGFROM') or message.get('MSGTO'))
        info_user = await ManagerMode.get(kwork_user_id=kwork_user_id)
        if info_user and not info_user.flag:
            # ИИ ещё обрабатывает, пропускаем
            return False

        return True

    async def process(
        self,
        message: dict,
        kwork_account: KworkAccount,
        account_id: int
    ) -> None:
        """
        Обрабатывает сообщение для менеджера: загружает файлы, отправляет в Telegram.
        """
        try:
            recipient_id = message.get('MSGTO')
            if not recipient_id:
                return

            kwork_user_id = self._extract_kwork_user_id(message, kwork_account.name)
            if recipient_id == kwork_user_id:
                return

            chat = await Chat.get(
                kwork_user_id=kwork_user_id,
                account_id=account_id
            )
            if not chat:
                logger.warning(f"Chat не найден для user_id={kwork_user_id}")
                return

            if files := message.get('filesArray'):
                await FileService.process_files_from_message(
                    files,
                    kwork_account.headers,
                    chat.tg_chat_id,
                    chat.tg_topic_id
                )

            text = message.get('message')
            tg_msg = None

            if text:
                for part in split_text_by_length(text):
                    tg_msg = await bot.send_message(
                        chat_id=chat.tg_chat_id,
                        message_thread_id=chat.tg_topic_id,
                        text=part,
                        parse_mode=None
                    )

            await Message.create(
                kwork_user_id=kwork_user_id,
                recipient_kwork_user_id=recipient_id,
                username=message.get('mfrom'),
                kwork_msg_id=message.get('MID'),
                tg_msg_id=tg_msg.message_id if tg_msg else 0,
                text=text or ""
            )

            logger.info("Message resent to Telegram and saved in DB")

        except Exception as e:
            logger.error(f"Ошибка обработки {message.get('MID')}: {e}")

        await asyncio.sleep(3)