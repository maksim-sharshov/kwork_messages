"""
Сервис для работы с файлами из Kwork
"""

import random
from aiogram.types import BufferedInputFile
from aiogram.client.session import aiohttp

from core.bot import bot
from core.exceptions import FileProcessingError, TelegramAPIError
from core.logger import logger
from utils.kwork import DocumentParser


class FileService:
    
    """Сервис для загрузки, парсинга и отправки файлов в Telegram"""

    @staticmethod
    async def download_file(file_path: str, headers: dict) -> tuple[bytes, str]:
        """
        Загружает файл с сервера Kwork.

        :param file_path: URL файла
        :param headers: HTTP заголовки с куками/токенами
        :return: (содержимое файла, имя файла)
        :raises FileProcessingError: если ошибка при загрузке
        """
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(file_path) as response:
                    content = await response.read()
                    status = response.status

            if status != 200:
                raise FileProcessingError(
                    f"Ошибка загрузки файла {file_path}. HTTP Status: {status}"
                )

            filename = file_path.split('/')[-1]
            return content, filename

        except aiohttp.ClientError as e:
            raise FileProcessingError(f"Сетевая ошибка при загрузке {file_path}: {e}") from e

    @staticmethod
    def parse_document(content: bytes, filename: str) -> str | None:
        """
        Парсит документ и извлекает текст.

        :param content: Содержимое файла
        :param filename: Имя файла
        :return: Текст из документа или None если формат не поддерживается
        """
        try:
            text = DocumentParser.extract_text(content, filename)
            return text
        except Exception as e:
            logger.warning(f"Ошибка парсинга документа {filename}: {e}")
            return None

    @staticmethod
    async def send_to_telegram(
        content: bytes,
        filename: str,
        chat_id: int,
        topic_id: int | None = None
    ) -> None:
        """
        Отправляет файл в Telegram (фото или документ).

        :param content: Содержимое файла
        :param filename: Имя файла
        :param chat_id: ID чата в Telegram
        :param topic_id: ID топика (для форум-каналов)
        :raises TelegramAPIError: если ошибка при отправке
        """
        try:
            input_file = BufferedInputFile(file=content, filename=filename)

            # Определяем тип файла
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif')):
                await bot.send_photo(
                    chat_id=chat_id,
                    message_thread_id=topic_id,
                    photo=input_file
                )
            else:
                await bot.send_document(
                    chat_id=chat_id,
                    message_thread_id=topic_id,
                    document=input_file
                )
        except Exception as e:
            raise TelegramAPIError(f"Ошибка отправки файла {filename} в Telegram: {e}") from e

    @staticmethod
    async def process_files_from_message(
        files_array: list[dict],
        headers: dict,
        chat_id: int,
        topic_id: int | None = None
    ) -> str:
        """
        Обрабатывает все файлы из сообщения: загружает, парсит, отправляет в TG.

        :param files_array: Список файлов из API Kwork
        :param headers: HTTP заголовки для загрузки
        :param chat_id: ID чата для отправки
        :param topic_id: ID топика (опционально)
        :return: Объединённый текст из всех документов
        """
        document_text = ""

        for file_info in files_array:
            file_path = file_info.get('path')
            if not file_path:
                logger.warning("Файл без пути в сообщении")
                continue

            try:
                # Загрузить файл
                content, filename = await FileService.download_file(file_path, headers)

                # Парсить документ
                parsed_text = FileService.parse_document(content, filename)

                if not parsed_text:
                    logger.warning(f"Не удалось парсить документ: {filename}")
                    # Отправим в TG даже если не парсится
                    await FileService.send_to_telegram(content, filename, chat_id, topic_id)
                    continue

                document_text += "\n" + parsed_text

                # Отправить файл в Telegram
                await FileService.send_to_telegram(content, filename, chat_id, topic_id)

            except (FileProcessingError, TelegramAPIError) as e:
                logger.error(f"Ошибка обработки файла {file_path}: {e}")
                # Продолжаем с остальными файлами
                continue

        return document_text
