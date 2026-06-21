"""
Fixtures для тестирования проекта kwork-bot-v2
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def event_loop():
    """Fixture для asyncio event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def mock_kwork_account():
    """Mock KworkAccount для тестов"""
    account = AsyncMock()
    account.name = "test_account"
    account.account_url = "https://kwork.ru/test_account"
    account.headers = {"Cookie": "test_cookie"}

    account.get_dialogs = AsyncMock(return_value={
        "data": {
            "rows": [
                {
                    "user_id": 123,
                    "username": "test_user",
                    "last_message_time": "2026-06-20",
                    "unread_count": 1
                }
            ]
        }
    })

    account.get_chat_messages = AsyncMock(return_value={
        "data": {
            "messages": [
                {
                    "MID": "msg_123",
                    "mfrom": "test_user",
                    "MSGTO": 1,
                    "MSGFROM": 123,
                    "message": "Привет",
                    "filesArray": [],
                    "unread": 1
                }
            ]
        }
    })

    account.send_message = AsyncMock(return_value={
        "MID": "msg_response_123",
        "mfrom": "test_account",
        "success": True
    })

    return account


@pytest.fixture
def mock_bot():
    """Mock Telegram Bot"""
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=MagicMock(message_id=1))
    bot.send_photo = AsyncMock(return_value=MagicMock(message_id=2))
    bot.send_document = AsyncMock(return_value=MagicMock(message_id=3))
    bot.create_forum_topic = AsyncMock(
        return_value=MagicMock(message_thread_id=100)
    )
    bot.set_message_reaction = AsyncMock()

    return bot


@pytest.fixture
def mock_gpt_handler():
    """Mock GPTHandler для тестов"""
    handler = AsyncMock()
    handler.generate_response = AsyncMock(
        return_value=("Это ответ от GPT", None)
    )
    return handler


@pytest.fixture
def sample_message():
    """Примерное сообщение из Kwork API"""
    return {
        "MID": "msg_123",
        "mfrom": "customer",
        "MSGTO": 1,
        "MSGFROM": 456,
        "message": "Могу ли я получить консультацию?",
        "filesArray": [],
        "unread": 1
    }


@pytest.fixture
def sample_message_with_file():
    """Примерное сообщение с файлом"""
    return {
        "MID": "msg_124",
        "mfrom": "customer",
        "MSGTO": 1,
        "MSGFROM": 456,
        "message": "Смотрите прикреплённый файл",
        "filesArray": [
            {
                "path": "https://kwork.ru/files/document.pdf",
                "name": "document.pdf"
            }
        ],
        "unread": 1
    }


@pytest.fixture
def sample_dialog():
    """Примерный диалог из Kwork API"""
    return {
        "user_id": 456,
        "username": "customer_user",
        "last_message_time": "2026-06-20T10:30:00",
        "unread_count": 2
    }

