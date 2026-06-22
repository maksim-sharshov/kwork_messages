"""
Менеджер для работы с историей сообщений
"""

from typing import Literal

from db.redis.models.models import MessageAI


class HistoryManager:
    """
    Менеджер для получения истории сообщений в разных форматах.

    Поддерживает различные форматы в зависимости от требований модели:
    - openai: {"role": "user", "content": "..."}
    - gemini: {"role": "user", "parts": [{"text": "..."}]}
    """

    @staticmethod
    async def get_history(
        kwork_user_id: int,
        format_type: Literal["openai", "gemini"] = "openai"
    ) -> list[dict]:
        """
        Получает историю сообщений в нужном формате.

        :param kwork_user_id: ID пользователя Kwork
        :param format_type: Формат ("openai" или "gemini")
        :return: Список сообщений в формате модели
        """
        # Сообщения пользователя
        user_messages = await MessageAI.filter(
            kwork_user_id=kwork_user_id,
            recipient_id=1
        )

        # Ответы ИИ
        assistant_messages = await MessageAI.filter(
            kwork_user_id=1,
            recipient_id=kwork_user_id
        )

        # Объединяем и сортируем по времени
        all_messages = list(user_messages) + list(assistant_messages)
        all_messages.sort(key=lambda x: x.created_at)

        history = []

        for msg in all_messages:
            if not msg.content:
                continue

            if format_type == "openai":
                history.append(HistoryManager._format_openai(msg, kwork_user_id))
            elif format_type == "gemini":
                history.append(HistoryManager._format_gemini(msg, kwork_user_id))

        return history

    @staticmethod
    def _format_openai(msg, kwork_user_id: int) -> dict:
        """Форматирует сообщение для OpenAI API"""
        role = "user" if msg.kwork_user_id == kwork_user_id else "assistant"
        return {
            "role": role,
            "content": msg.content
        }

    @staticmethod
    def _format_gemini(msg, kwork_user_id: int) -> dict:
        """Форматирует сообщение для Google Gemini API"""
        role = "user" if msg.kwork_user_id == kwork_user_id else "model"
        return {
            "role": role,
            "parts": [{"text": msg.content}]
        }
