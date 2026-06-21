"""
Менеджер для автоматизации работы с диалогами на Kwork.

Ответственность:
- Проверка новых сообщений в диалогах
- Создание топиков в Telegram для каждого диалога
- Оркестрация обработки сообщений (AI или менеджер)
- Управление флагами режима обработки
"""

import asyncio
import random

from aiogram.types import ReactionTypeEmoji

from core.bot import bot
from core.logger import manager_logger as logger
from db.psql.models.models import Account, Message, ManagerMode
from integrations.kwork import KworkAccount
from manager.base import BaseManager
from services.message_processor import AIMessageProcessor, ManagerMessageProcessor
from services.topic_service import TopicService
from settings import settings


class KworkManager(BaseManager):
    """
    Менеджер для автоматизации работы с диалогами на Kwork.

    Процесс:
    1. Получить диалоги для каждого аккаунта
    2. Проверить новые сообщения
    3. Создать топики в TG для новых диалогов
    4. Обработать сообщения (AI или менеджер)
    5. Обновить флаги режима
    """

    timeout = 40

    def __init__(self):
        super().__init__()
        self.topic_service = TopicService()
        self.processors = [
            AIMessageProcessor(),
            ManagerMessageProcessor()
        ]

    async def run(self):
        """Запускает менеджер в бесконечном цикле"""
        logger.info('=== Kwork Manager is running ===')
        while True:
            try:
                await self.task()
            except Exception as e:
                logger.exception("Error on Kwork Manager run: %s", e)

            await asyncio.sleep(self.timeout)

    async def task(self):
        """
        Основная задача менеджера, выполняется каждые 40 сек.

        Процесс:
        1. Получить диалоги для каждого аккаунта
        2. Проверить новые сообщения
        3. Создать топики в TG для новых диалогов
        4. Обработать сообщения (AI или менеджер)
        """
        logger.info("=== Kwork Manager run task ===")

        accounts: list[Account] = await Account.all()

        for account in accounts:
            try:
                account_kwork = KworkAccount(cookie=account.cookie)

                if not account.username:
                    await account.update(username=account_kwork.name)

                # Получить диалоги
                dialogs = await account_kwork.get_dialogs()
                dialogs['data']['rows'] = dialogs['data']['rows'][:5]

                logger.info('Подключился к %s', account_kwork.account_url)

                # 1. Проверить новые сообщения
                unprocessed_messages = await self.check_messages(
                    dialogs=dialogs['data']['rows'],
                    kwork_account=account_kwork
                )

                logger.info('Не прочитанных сообщений: %d', len(unprocessed_messages))

                # 2. Обновить флаги режима
                await self.update_flag_and_check(
                    dialogs=dialogs['data']['rows']
                )

                # 3. Создать топики для новых диалогов
                for dialog in dialogs['data']['rows']:
                    try:
                        await self.topic_service.create_or_get(dialog, account)
                    except Exception as e:
                        logger.error(
                            f"Ошибка создания топика для диалога {dialog.get('user_id')}: {e}"
                        )

                # 4. Обработать сообщения через процессоры
                for message in unprocessed_messages:
                    try:
                        processed = False
                        for processor in self.processors:
                            if await processor.can_process(message):
                                asyncio.create_task(
                                    processor.process(message, account_kwork, account.id)
                                )
                                processed = True
                                break
                        if not processed:
                            logger.warning(
                                f"Сообщение {message.get('MID')} не обработано ни одним процессором"
                            )
                    except Exception as e:
                        logger.error(
                            f"Ошибка обработки сообщения {message.get('MID')}: {e}"
                        )

                await asyncio.sleep(random.uniform(1, 3))

            except Exception as e:
                logger.exception(
                    'Error Kwork Manager. Account ID: %d. Error: %s', account.id, e
                )

    async def check_messages(
        self,
        dialogs: list[dict],
        kwork_account: KworkAccount
    ) -> list[dict]:
        """
        Собирает все новые (непроцессированные) сообщения от клиентов.

        :param dialogs: Диалоги на аккаунте
        :param kwork_account: KworkAccount объект
        :return: Список непроцессированных сообщений
        """
        result = []

        for dialog in dialogs:
            user_id = dialog.get('user_id')
            username = dialog.get('username', 'UNKNOWN')

            if not user_id:
                logger.warning(f"[check_messages] Пропущен диалог без user_id: {dialog}")
                continue

            try:
                messages = await kwork_account.get_chat_messages(user_id=user_id)

                if not messages:
                    logger.warning(
                        f"[check_messages] Нет ответа от get_chat_messages для user_id={user_id}"
                    )
                    continue

                if not isinstance(messages, dict) or "data" not in messages:
                    logger.warning(
                        f"[check_messages] Структура ответа неожиданна для user_id={user_id}"
                    )
                    continue

                chat_messages = messages["data"].get("messages", [])

                for message in chat_messages:
                    try:
                        msg_in_bot = await Message.get(kwork_msg_id=message['MID'])

                        if not msg_in_bot:
                            result.append(message)
                            continue

                        # Если сообщение уже было обработано но не отмечено как просмотренное
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
                        logger.error(f"[check_messages] Ошибка при обработке сообщения: {e}")

                await asyncio.sleep(random.uniform(0.5, 1.5))

            except Exception as e:
                logger.error(f"[check_messages] Ошибка для user_id={user_id}: {e}")

        return result

    async def update_flag_and_check(self, dialogs: list[dict]) -> None:
        """
        Обновляет или создаёт запись ManagerMode для каждого пользователя.

        :param account_id: ID аккаунта
        :param dialogs: Список диалогов
        """
        for dialog in dialogs:
            user_id = dialog['user_id']

            try:
                info_user = await ManagerMode.get(kwork_user_id=user_id)

                if not info_user:
                    await ManagerMode.create(kwork_user_id=user_id, flag=False)

            except Exception as e:
                logger.error(f"Ошибка обновления флага для user_id={user_id}: {e}")
