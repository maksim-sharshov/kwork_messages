import time


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
