import asyncio
import logging
import random
import string

import aiohttp
import requests
from bs4 import BeautifulSoup


class KworkAccount:
    _base_url = 'https://kwork.ru'

    def __init__(self, cookie: str) -> None:
        """
            Инициализация API Kwork
        :param cookie: Строка куки из браузера
        """
        self.headers = {
            'Cookie': cookie,
            'Accept': 'application/json, text/plain, */*'
        }
        response = requests.get(
            url=f'{self._base_url}/inbox',
            headers=self.headers
        )
        response.encoding = 'utf-8'

        parse = BeautifulSoup(response.text, 'html.parser')

        self.csrf_token = parse.find('input', {'name': 'csrftoken'})['value']
        self.cookie = cookie
        self.account_url = parse.find('a', {'class': 'user-box'})['href']
        self.name = self.account_url.split('/')[-1]

    def random_alphanumeric_string(self, length: int) -> str:
        """
        Генерация строки из A-z, 0-9

        :param length: Длина строки
        """
        return ''.join(
            random.choices(
                string.ascii_letters + string.digits,
                k=length
            )
        ).lower()
                    
    async def get_dialogs(self) -> dict:
        '''
            Получение диалогов с аккаунта
        :return: Массив с диалогами
        '''
        try:
            timeout = aiohttp.ClientTimeout(total=20)
            async with aiohttp.ClientSession(
                    base_url=self._base_url,
                    headers=self.headers,
                    timeout=timeout
            ) as s:
                async with s.post("/getdialogs") as r:
                    return await r.json()
        except Exception as e:
            logging.warning(f'Ошибка при получении диалогов: {e}')


    async def get_chat_messages(self, user_id: int, all_unread: bool = True, limit: int = 6) -> dict | None:
        """
        Получение сообщений от пользователя с полной защитой от сбоев.
        :param user_id: Идентификатор пользователя
        :param all_unread: ??? не трогать в общем
        :param limit: Лимит сообщений
        :return: Массив с сообщениями
        """
        data = {
            'userId': user_id,
            'allUnread': all_unread,
            'limit': limit
        }

        try:
            timeout = aiohttp.ClientTimeout(total=20)
            async with aiohttp.ClientSession(
                    base_url=self._base_url,
                    headers=self.headers,
                    timeout=timeout
            ) as s:
                async with s.post(
                        url="/inbox_more_messages",
                        json=data
                ) as r:
                    raw = await r.text()
                    try:
                        json_response = await r.json()
                        return json_response
                    except Exception as json_err:
                        logging.warning(f"[get_chat_messages] Не удалось декодировать JSON. Ответ:\n{raw[:1000]}")
                        return None

        except aiohttp.ClientConnectorError as e:
            logging.error(f"[get_chat_messages] Ошибка подключения к серверу: {e}")
        except aiohttp.ServerDisconnectedError as e:
            logging.error(f"[get_chat_messages] Сервер разорвал соединение: {e}")
        except asyncio.TimeoutError:
            logging.error(f"[get_chat_messages] Timeout при попытке получить сообщения.")
        except Exception as e:
            logging.exception(f"[get_chat_messages] Непредвиденная ошибка: {e}")

        return None


    async def get_check_notify(self) -> list[dict]:
        """
            Проверка новых уведомлений
        :return: Массив с информацией об уведомлении
        """

        async with aiohttp.ClientSession(
                base_url=self._base_url,
                headers=self.headers
        ) as s:
            async with s.get("/api/user/checknotify") as r:
                return await r.json()

    async def send_message(self, user_id: int, text: str) -> dict:
        """
        Отправление сообщения пользователю
        :param user_id: Идентификатор пользователя
        :param text: Текст сообщения
        :return: Массив с информацией об отправленном сообщении
        """
        data = {
            'message_body': text,
            'submg': 1,
            'msgto': user_id,
            'want_id': None,
            'message_id': None,
            'allowDialog': None,
            'quoteId': 0,
            'csrftoken': self.csrf_token,
            'message_type': None,
            'messageKey': self.random_alphanumeric_string(8),
            'isMobile': False
        }

        retries = 3

        while retries:
            try:
                timeout = aiohttp.ClientTimeout(total=20)
                async with aiohttp.ClientSession(
                        base_url=self._base_url,
                        headers=self.headers,
                        timeout=timeout
                ) as s:
                    async with s.post(
                            url="/sendmessage",
                            data=data
                    ) as r:
                        r.raise_for_status()
                        return await r.json()

            except Exception as e:
                logging.warning(f"Ошибка при отправке сообщения пользователю: {e}")
                retries -= 1

                await asyncio.sleep(15)

        logging.error("All retry attempts failed")
        raise
