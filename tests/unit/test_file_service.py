"""
Unit тесты для FileService
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.exceptions import FileProcessingError, TelegramAPIError
from services.file_service import FileService


@pytest.mark.asyncio
async def test_download_file_success():
    """Тест успешной загрузки файла"""
    content = b"test file content"
    filename = "test.pdf"
    file_path = f"https://kwork.ru/files/{filename}"

    with patch('services.file_service.aiohttp.ClientSession') as mock_session_class:
        mock_response = AsyncMock()
        mock_response.read = AsyncMock(return_value=content)
        mock_response.status = 200

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_class.return_value.__aexit__ = AsyncMock(return_value=False)

        headers = {"Cookie": "test_cookie"}

        result_content, result_filename = await FileService.download_file(file_path, headers)

        assert result_content == content
        assert result_filename == filename


@pytest.mark.asyncio
async def test_download_file_http_error():
    """Тест ошибки HTTP при загрузке файла"""
    file_path = "https://kwork.ru/files/test.pdf"

    with patch('services.file_service.aiohttp.ClientSession') as mock_session_class:
        mock_response = AsyncMock()
        mock_response.status = 404

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_class.return_value.__aexit__ = AsyncMock(return_value=False)

        headers = {"Cookie": "test_cookie"}

        with pytest.raises(FileProcessingError):
            await FileService.download_file(file_path, headers)


def test_parse_document_success():
    """Тест успешного парсинга документа"""
    content = b"test content"
    filename = "test.txt"

    with patch('services.file_service.DocumentParser') as mock_parser:
        mock_parser.extract_text.return_value = "Extracted text"

        result = FileService.parse_document(content, filename)

        assert result == "Extracted text"
        mock_parser.extract_text.assert_called_once_with(content, filename)


def test_parse_document_unsupported_format():
    """Тест парсинга неподдерживаемого формата"""
    content = b"unknown format"
    filename = "test.unknown"

    with patch('services.file_service.DocumentParser') as mock_parser:
        mock_parser.extract_text.return_value = None

        result = FileService.parse_document(content, filename)

        assert result is None


@pytest.mark.asyncio
async def test_send_to_telegram_photo():
    """Тест отправки фотографии в Telegram"""
    content = b"photo content"
    filename = "photo.jpg"
    chat_id = 123
    topic_id = 100

    with patch('services.file_service.bot') as mock_bot, \
         patch('services.file_service.BufferedInputFile') as mock_input_file:

        mock_bot.send_photo = AsyncMock()

        await FileService.send_to_telegram(content, filename, chat_id, topic_id)

        mock_bot.send_photo.assert_called_once()
        assert mock_bot.send_photo.call_args[1]['chat_id'] == chat_id
        assert mock_bot.send_photo.call_args[1]['message_thread_id'] == topic_id


@pytest.mark.asyncio
async def test_send_to_telegram_document():
    """Тест отправки документа в Telegram"""
    content = b"document content"
    filename = "document.pdf"
    chat_id = 123
    topic_id = 100

    with patch('services.file_service.bot') as mock_bot, \
         patch('services.file_service.BufferedInputFile') as mock_input_file:

        mock_bot.send_document = AsyncMock()

        await FileService.send_to_telegram(content, filename, chat_id, topic_id)

        mock_bot.send_document.assert_called_once()
        assert mock_bot.send_document.call_args[1]['chat_id'] == chat_id
