import io
import docx
import time
import PyPDF2
from core.logger import manager_logger as logger


class DocumentParser:
    @staticmethod
    def extract_text(content: bytes, filename: str) -> str:
        filename = filename.lower()
        try:
            if filename.endswith('.txt'):
                return content.decode(errors='ignore')
            elif filename.endswith('.docx'):
                file_stream = io.BytesIO(content)
                doc = docx.Document(file_stream)
                return '\n'.join([para.text for para in doc.paragraphs])
            elif filename.endswith('.pdf'):
                file_stream = io.BytesIO(content)
                reader = PyPDF2.PdfReader(file_stream)
                return '\n'.join([page.extract_text() or '' for page in reader.pages])
        except Exception as e:
            logger.error(f"Ошибка при извлечении текста из документа {filename}: {e}")
        return ""
    

def msg_in_chat(messages: list, text: str, time_space: int = 43200) -> bool:
    """
        Есть ли сообщение с определённым текстом в чате
    :param messages: Все сообщения в чате
    :param text: Текст, который мы ищем в чате
    :param time_space: Пробел времени в секундах после которого
    даже если сообщение есть в чате то оно не считается
    :return: bool
    """
    return bool([
        msg for msg in messages
        if text in msg['message']
           and time.time() - msg['time'] <= time_space
    ])


def split_text_by_length(text: str, length: int = 4096):
    return [text[i:i + length] for i in range(0, len(text), length)]

def clean_text(text: str) -> str:
    if text:
        # удаляем символы с кодом 0 (null byte)
        return text.replace('\x00', '')
    return text
