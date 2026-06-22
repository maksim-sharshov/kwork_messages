"""
GPT обработчик для OpenAI моделей
"""

from typing import Optional, Tuple

from openai import AsyncOpenAI

from settings import settings
from .base import AIHandler
from .history_manager import HistoryManager


class GPTHandler(AIHandler):
    """
    Обработчик для OpenAI GPT моделей.

    Используется для генерации ответов через OpenAI API (GPT-4o, GPT-4, и т.д.)
    """

    def __init__(self, kwork_user_id: int, recipient_id: int):
        super().__init__(kwork_user_id, recipient_id)
        self.client = AsyncOpenAI(api_key=settings.openai.TOKEN)

    async def get_history(self) -> list[dict]:
        """
        Получает историю сообщений в формате OpenAI.

        :return: Список сообщений {"role": "...", "content": "..."}
        """
        return await HistoryManager.get_history(
            self.kwork_user_id,
            format_type="openai"
        )

    async def generate_response(self) -> Tuple[str, Optional[str]]:
        """
        Генерирует ответ через GPT-4o.

        Процесс:
        1. Получить историю сообщений
        2. Загрузить системный prompt
        3. Отправить запрос в OpenAI API
        4. Парсить ответ и извлечь заявку (если есть)

        :return: Кортеж (ответ, заявка или None)
        """
        history = await self.get_history()
        prompt = await self.load_prompt()

        full_messages = [{"role": "system", "content": prompt}] + history

        response = await self.client.chat.completions.create(
            model=settings.openai.MODEL,
            messages=full_messages,
        )

        reply = response.choices[0].message.content.strip()

        # Парсить ответ и извлечь заявку
        reply, application = self.parse_and_extract_application(reply)

        return reply, application
