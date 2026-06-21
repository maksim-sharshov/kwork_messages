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
    headers = {"Cookie": "test_cookie"}

    # Правильно мокируем async context manager
    mock_response = AsyncMock()
    mock_response.read = AsyncMock(return_value=content)
    mock_response.status = 200
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = AsyncMock()
    mock_session.get = MagicMock(return_value=mock_response)  # ← Возвращаем mock, не coroutine
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch('services.file_service.aiohttp.ClientSession') as mock_session_class:
        mock_session_class.return_value = mock_session

        result_content, result_filename = await FileService.download_file(file_path, headers)

        assert result_content == content
        assert result_filename == filename


@pytest.mark.asyncio
async def test_download_file_http_error():
    """Тест ошибки HTTP при загрузке файла"""
    file_path = "https://kwork.ru/files/test.pdf"
    headers = {"Cookie": "test_cookie"}

    mock_response = AsyncMock()
    mock_response.status = 404
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = AsyncMock()
    mock_session.get = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch('services.file_service.aiohttp.ClientSession') as mock_session_class:
        mock_session_class.return_value = mock_session

        with pytest.raises(FileProcessingError):
            await FileService.download_file(file_path, headers)


def test_parse_document_success():
    """Тест успешного парсинга документа"""
    content = b"test content"
    filename = "test.txt"

    with patch('services.file_service.DocumentParser') as mock_parser:
        mock_parser.extract_text = MagicMock(return_value="Extracted text")

        result = FileService.parse_document(content, filename)

        assert result == "Extracted text"
        mock_parser.extract_text.assert_called_once_with(content, filename)


def test_parse_document_unsupported_format():
    """Тест парсинга неподдерживаемого формата"""
    content = b"unknown format"
    filename = "test.unknown"

    with patch('services.file_service.DocumentParser') as mock_parser:
        mock_parser.extract_text = MagicMock(return_value=None)

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
        mock_input_file.return_value = MagicMock()

        await FileService.send_to_telegram(content, filename, chat_id, topic_id)

        mock_bot.send_photo.assert_called_once()
        call_kwargs = mock_bot.send_photo.call_args[1]
        assert call_kwargs['chat_id'] == chat_id
        assert call_kwargs['message_thread_id'] == topic_id


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
        mock_input_file.return_value = MagicMock()

        await FileService.send_to_telegram(content, filename, chat_id, topic_id)

        mock_bot.send_document.assert_called_once()
        call_kwargs = mock_bot.send_document.call_args[1]
        assert call_kwargs['chat_id'] == chat_id
        assert call_kwargs['message_thread_id'] == topic_id


@pytest.mark.asyncio
async def test_send_to_telegram_error():
    """Тест ошибки при отправке в Telegram"""
    content = b"photo content"
    filename = "photo.jpg"
    chat_id = 123
    topic_id = 100

    with patch('services.file_service.bot') as mock_bot, \
         patch('services.file_service.BufferedInputFile') as mock_input_file:

        mock_bot.send_photo = AsyncMock(side_effect=Exception("API Error"))
        mock_input_file.return_value = MagicMock()

        with pytest.raises(TelegramAPIError):
            await FileService.send_to_telegram(content, filename, chat_id, topic_id)


@pytest.mark.asyncio
async def test_process_files_from_message_success():
    """Тест обработки файлов из сообщения"""
    files_array = [
        {
            "path": "https://kwork.ru/files/document.pdf",
            "name": "document.pdf"
        }
    ]
    headers = {"Cookie": "test_cookie"}
    chat_id = 123
    topic_id = 100

    with patch.object(FileService, 'download_file') as mock_download, \
         patch.object(FileService, 'parse_document') as mock_parse, \
         patch.object(FileService, 'send_to_telegram') as mock_send:

        mock_download.return_value = (b"content", "document.pdf")
        mock_parse.return_value = "Extracted text"
        mock_send.return_value = None

        result = await FileService.process_files_from_message(
            files_array,
            headers,
            chat_id,
            topic_id
        )

        assert "Extracted text" in result
        mock_download.assert_called_once()
        mock_parse.assert_called_once()
        mock_send.assert_called_once()


