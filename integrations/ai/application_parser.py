"""
Парсер для извлечения заявок из ответов ИИ
"""

from typing import Optional, Tuple


class ApplicationParser:
    """
    Выделенный парсер для работы с заявками.

    Ищет блок заявки (🚨 Новый заказ) в ответе модели
    и отделяет его от основного ответа.
    """

    APPLICATION_MARKER = "🚨 Новый заказ"

    @staticmethod
    def extract_application(reply: str) -> Tuple[str, Optional[str]]:
        """
        Извлекает заявку из ответа.

        Логика:
        - Ищет строку с маркером 🚨 Новый заказ
        - Извлекает блок заявки до первой пустой строки
        - Удаляет заявку из основного ответа
        - Если остаток ответа пуст, добавляет стандартное сообщение

        :param reply: Ответ от модели
        :return: Кортеж (ответ без заявки, заявка или None)
        """
        application_text = None

        if ApplicationParser.APPLICATION_MARKER not in reply:
            return reply.replace('`', ''), None

        lines = reply.splitlines()
        start = None
        end = None

        # Найти начало блока заявки
        for i, line in enumerate(lines):
            if ApplicationParser.APPLICATION_MARKER in line:
                start = i
            elif start is not None and line.strip() == "":
                end = i
                break

        # Если нашли блок заявки
        if start is not None:
            end = end if end is not None else len(lines)
            application_text = "\n".join(lines[start:end]).strip()

            # Убираем заявку из ответа
            reply = "\n".join(lines[:start] + lines[end:]).strip()

            # Если остался пустой ответ - добавляем стандартное сообщение
            if not reply.strip() and application_text:
                reply = "Спасибо! Мы приняли заявку. Ожидайте, пожалуйста, обратной связи."

        return reply.replace('`', ''), (application_text.replace('`', '') if application_text else None)
