"""
Пользовательские исключения для проекта kwork-bot-v2
"""


class KworkBotException(Exception):
    """Базовое исключение для проекта"""
    pass


class KworkAPIError(KworkBotException):
    """Ошибка API Kwork"""
    pass


class DatabaseError(KworkBotException):
    """Ошибка БД"""
    pass


class MessageProcessingError(KworkBotException):
    """Ошибка обработки сообщения"""
    pass


class AIProcessingError(KworkBotException):
    """Ошибка обработки ИИ"""
    pass


class FileProcessingError(KworkBotException):
    """Ошибка обработки файла"""
    pass


class TelegramAPIError(KworkBotException):
    """Ошибка Telegram API"""
    pass
