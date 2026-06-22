"""
Абстрактный базовый класс для AI обработчиков
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple

from db.redis.models.models import MessageAI
from .application_parser import ApplicationParser


class AIHandler(ABC):
    """
    Абстрактный обработчик для работы с AI моделями.

    Определяет интерфейс и общую логику для всех AI провайдеров.
    """

    def __init__(self, kwork_user_id: int, recipient_id: int):
        self.kwork_user_id = kwork_user_id
        self.recipient_id = recipient_id
        self.prompt_path = Path("data/prompt.txt")

    async def load_prompt(self) -> str:
        """
        Загружает системный prompt из файла.

        :return: Текст prompt'а или пустая строка если файл не существует
        """
        if self.prompt_path.exists():
            return self.prompt_path.read_text(encoding='utf-8')
        return ""

    async def get_history(self) -> list[dict]:
        """
        Получает историю сообщений между пользователем и ИИ из Redis.

        Должна быть переопределена в подклассах для формата конкретной модели.

        :return: Список сообщений в формате модели
        """
        # Сообщения пользователя
        user_messages = await MessageAI.filter(
            kwork_user_id=self.kwork_user_id,
            recipient_id=1
        )

        # Ответы ИИ
        assistant_messages = await MessageAI.filter(
            kwork_user_id=1,
            recipient_id=self.kwork_user_id
        )

        # Объединяем и сортируем по времени
        all_messages = list(user_messages) + list(assistant_messages)
        all_messages.sort(key=lambda x: x.created_at)

        return all_messages

    @abstractmethod
    async def generate_response(self) -> Tuple[str, Optional[str]]:
        """
        Генерирует ответ от ИИ модели.

        :return: Кортеж (ответ, заявка или None)
        :raises: AIProcessingError если ошибка при генерации
        """
        pass

    def parse_and_extract_application(self, reply: str) -> Tuple[str, Optional[str]]:
        """
        Парсит ответ и извлекает заявку (если есть).

        :param reply: Ответ от модели
        :return: Кортеж (ответ без заявки, заявка или None)
        """
        return ApplicationParser.extract_application(reply)
