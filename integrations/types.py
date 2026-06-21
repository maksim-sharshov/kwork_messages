"""
TypedDict модели для интеграций и обработки сообщений
"""

from typing_extensions import TypedDict


class DialogDict(TypedDict, total=False):
    """Структура диалога из Kwork API"""
    user_id: int
    username: str
    last_message_time: str
    unread_count: int


class FileDict(TypedDict, total=False):
    """Структура файла из Kwork API"""
    path: str
    name: str


class MessageDict(TypedDict, total=False):
    """Структура сообщения из Kwork API"""
    MID: str
    mfrom: str
    MSGTO: int
    MSGFROM: int
    message: str
    filesArray: list[FileDict]
    unread: int


class GPTResponseDict(TypedDict, total=False):
    """Структура ответа от GPT Handler"""
    answer: str
    application: str | None
