"""
Gemini обработчик для Google Gemini моделей
"""

from typing import Optional, Tuple

from google import genai
from google.genai.types import GenerateContentConfig

from settings import settings
from .base import AIHandler
from .history_manager import HistoryManager


class GeminiHandler(AIHandler):
    """
    Обработчик для Google Gemini моделей.

    Используется для генерации ответов через Google Gemini API (2.5 Flash, Pro, и т.д.)
    """

    def __init__(self, kwork_user_id: int, recipient_id: int):
        super().__init__(kwork_user_id, recipient_id)
        self.client = genai.Client(api_key=settings.gemini.TOKEN)

    async def get_history(self) -> list[dict]:
        """
        Получает историю сообщений в формате Gemini.

        :return: Список сообщений {"role": "...", "parts": [{"text": "..."}]}
        """
        history = await HistoryManager.get_history(
            self.kwork_user_id,
            format_type="gemini"
        )

        return history

    async def generate_response(self) -> Tuple[str, Optional[str]]:
        """
        Генерирует ответ через Gemini 2.5 Flash.

        Процесс:
        1. Получить историю сообщений в формате Gemini
        2. Загрузить системный prompt
        3. Отправить запрос в Gemini API
        4. Парсить ответ и извлечь заявку (если есть)

        :return: Кортеж (ответ, заявка или None)
        """
        history = await self.get_history()
        prompt = await self.load_prompt()

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=history,
            config=GenerateContentConfig(
                system_instruction=prompt
            ),
        )

        reply = response.text.strip()
        reply, application = self.parse_and_extract_application(reply)

        return reply, application
