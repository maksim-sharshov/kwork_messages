"""
Фабрика для создания AI обработчиков
"""

from typing import Literal

from .base import AIHandler
from .gpt import GPTHandler
from .gemini import GeminiHandler


class AIHandlerFactory:
    """
    Фабрика для создания обработчиков AI моделей.

    Поддерживает различные провайдеры и позволяет легко добавлять новые.
    """

    _providers = {
        "gpt": GPTHandler,
        "gemini": GeminiHandler,
    }

    @classmethod
    def create(
        cls,
        provider: Literal["gpt", "gemini"],
        kwork_user_id: int,
        recipient_id: int
    ) -> AIHandler:
        """
        Создаёт обработчик нужного типа.

        :param provider: Тип провайдера ("gpt" или "gemini")
        :param kwork_user_id: ID пользователя Kwork
        :param recipient_id: ID получателя
        :return: Экземпляр AIHandler
        :raises ValueError: Если провайдер не поддерживается
        """
        if provider not in cls._providers:
            raise ValueError(
                f"Неизвестный провайдер: {provider}. "
                f"Поддерживаемые: {list(cls._providers.keys())}"
            )

        handler_class = cls._providers[provider]
        return handler_class(kwork_user_id, recipient_id)

    @classmethod
    def register(cls, name: str, handler_class: type) -> None:
        """
        Регистрирует новый тип обработчика.

        Позволяет динамически добавлять новых провайдеров.

        :param name: Имя провайдера
        :param handler_class: Класс обработчика (подкласс AIHandler)
        """
        if not issubclass(handler_class, AIHandler):
            raise TypeError(
                f"{handler_class} должен быть подклассом AIHandler"
            )
        cls._providers[name] = handler_class

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """
        Возвращает список доступных провайдеров.

        :return: Список имён провайдеров
        """
        return list(cls._providers.keys())
