"""
Unit тесты для MessageProcessor
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.message_processor import AIMessageProcessor, ManagerMessageProcessor
from core.exceptions import TelegramAPIError


@pytest.mark.asyncio
async def test_ai_processor_can_process_when_flag_false():
    """Тест что AI процессор может обработать когда флаг False"""
    message = {
        "MID": "msg_123",
        "mfrom": "customer",
        "MSGFROM": 456,
        "MSGTO": 1
    }

    with patch('services.message_processor.ManagerMode') as mock_manager_mode, \
         patch('services.message_processor.settings') as mock_settings:
        mock_info_user = AsyncMock()
        mock_info_user.flag = False
        mock_manager_mode.get = AsyncMock(return_value=mock_info_user)
        mock_settings.openai.GPT_ENABLED = True

        processor = AIMessageProcessor()
        result = await processor.can_process(message)
        assert result is True


@pytest.mark.asyncio
async def test_ai_processor_cannot_process_when_flag_true():
    """Тест что AI процессор не может обработать когда флаг True"""
    processor = AIMessageProcessor()
    message = {
        "MID": "msg_123",
        "mfrom": "customer",
        "MSGFROM": 456,
        "MSGTO": 1
    }

    with patch('services.message_processor.ManagerMode') as mock_manager_mode, \
         patch('services.message_processor.settings') as mock_settings:
        mock_info_user = AsyncMock()
        mock_info_user.flag = True
        mock_info_user.update = AsyncMock()
        mock_manager_mode.get = AsyncMock(return_value=mock_info_user)
        mock_settings.openai.GPT_ENABLED = True

        result = await processor.can_process(message)
        assert result is False


@pytest.mark.asyncio
async def test_manager_processor_can_process():
    """Тест что Manager процессор может обработать"""
    processor = ManagerMessageProcessor()
    message = {
        "MID": "msg_123",
        "mfrom": "customer",
        "MSGFROM": 456,
        "MSGTO": 1
    }

    with patch('services.message_processor.ManagerMode') as mock_manager_mode:
        mock_manager_mode.get = AsyncMock(return_value=None)

        result = await processor.can_process(message)
        assert result is True


def test_extract_kwork_user_id_from_mfrom():
    """Тест извлечения ID пользователя из mfrom (если это наш аккаунт)"""
    message = {
        "mfrom": "account_name",
        "MSGFROM": 123,
        "MSGTO": 456
    }

    user_id = AIMessageProcessor._extract_kwork_user_id(message, "account_name")
    assert user_id == 456  # Если это наш аккаунт (mfrom == account_name), то берём MSGTO


def test_extract_kwork_user_id_from_msgfrom():
    """Тест извлечения ID пользователя из MSGFROM (если это чужой аккаунт)"""
    message = {
        "mfrom": "customer",
        "MSGFROM": 123,
        "MSGTO": 1
    }

    user_id = AIMessageProcessor._extract_kwork_user_id(message, "account_name")
    assert user_id == 123  # Если это не наш аккаунт (mfrom != account_name), то берём MSGFROM


@pytest.mark.asyncio
async def test_send_to_telegram_success():
    """Тест успешной отправки сообщения в Telegram"""
    text = "Test message"
    chat_id = 123
    topic_id = 100

    with patch('services.message_processor.bot') as mock_bot, \
         patch('services.message_processor.split_text_by_length') as mock_split:

        mock_split.return_value = [text]
        mock_msg = MagicMock()
        mock_msg.message_id = 42
        mock_bot.send_message = AsyncMock(return_value=mock_msg)

        result = await AIMessageProcessor._send_to_telegram(text, chat_id, topic_id)

        assert result == 42
        mock_bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_send_to_telegram_error():
    """Тест ошибки при отправке в Telegram"""
    text = "Test message"
    chat_id = 123
    topic_id = 100

    with patch('services.message_processor.bot') as mock_bot, \
         patch('services.message_processor.split_text_by_length') as mock_split:

        mock_split.return_value = [text]
        mock_bot.send_message = AsyncMock(side_effect=Exception("API Error"))

        with pytest.raises(TelegramAPIError):
            await AIMessageProcessor._send_to_telegram(text, chat_id, topic_id)


