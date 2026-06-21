"""
Сервис для управления топиками (форум-каналы) в Telegram
"""

from core.bot import bot
from core.exceptions import TelegramAPIError
from core.logger import logger
from db.psql.models.models import Chat, Account
from settings import settings


class TopicService:
    
    """Сервис для создания и управления топиками в Telegram"""

    @staticmethod
    async def create_or_get(dialog: dict, account: Account) -> Chat:
        """
        Создаёт топик если его нет, или возвращает существующий.

        :param dialog: Диалог из Kwork API
        :param account: Объект Account из БД
        :return: Объект Chat с информацией о топике
        :raises TelegramAPIError: если ошибка при создании топика
        """
        # Проверить существует ли уже чат
        existing_chat = await Chat.get(
            kwork_user_id=dialog['user_id'],
            account_id=account.id
        )
        if existing_chat:
            return existing_chat

        # Сформировать название топика
        topic_title = TopicService._format_topic_title(
            dialog['username'],
            account.username
        )

        try:
            # Создать топик в Telegram
            topic = await bot.create_forum_topic(
                chat_id=settings.bot.CHAT_ID,
                name=topic_title
            )

            # Создать запись в БД
            chat = await Chat.create(
                kwork_user_id=dialog['user_id'],
                tg_chat_id=settings.bot.CHAT_ID,
                tg_topic_id=topic.message_thread_id,
                title=topic_title,
                account_id=account.id
            )

            logger.info(
                f'Создан новый топик: {chat.title} '
                f'(user_id={dialog["user_id"]}, topic_id={topic.message_thread_id})'
            )

            return chat

        except Exception as e:
            raise TelegramAPIError(
                f"Ошибка создания топика для пользователя {dialog['username']}: {e}"
            ) from e

    @staticmethod
    def _format_topic_title(username: str, account_username: str) -> str:
        """
        Форматирует название топика.

        :param username: Имя пользователя Kwork
        :param account_username: Имя аккаунта Kwork
        :return: Отформатированное название
        """
        return f'K | {username} | {account_username}'
