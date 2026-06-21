import asyncio
import json
import logging
import random
import string

import aiohttp
import requests
from bs4 import BeautifulSoup

from core.exceptions import KworkAPIError
from core.logger import logger


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
        :raises KworkAPIError: если ошибка при получении
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
        except asyncio.TimeoutError as e:
            raise KworkAPIError(f"Timeout при получении диалогов") from e
        except aiohttp.ClientError as e:
            raise KworkAPIError(f"Сетевая ошибка при получении диалогов: {e}") from e
        except json.JSONDecodeError as e:
            raise KworkAPIError(f"Невалидный JSON в ответе диалогов: {e}") from e
        except Exception as e:
            raise KworkAPIError(f"Ошибка при получении диалогов: {e}") from e


    async def get_chat_messages(self, user_id: int, all_unread: bool = True, limit: int = 6) -> dict | None:
        """
        Получение сообщений от пользователя с полной защитой от сбоев.
        :param user_id: Идентификатор пользователя
        :param all_unread: ??? не трогать в общем
        :param limit: Лимит сообщений
        :return: Массив с сообщениями или None при ошибке
        :raises KworkAPIError: при сетевых ошибках
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
                    try:
                        return await r.json()
                    except json.JSONDecodeError as json_err:
                        raw = await r.text()
                        logger.warning(
                            f"[get_chat_messages] Не удалось декодировать JSON. "
                            f"Status: {r.status}, Response: {raw[:500]}"
                        )
                        return None

        except asyncio.TimeoutError as e:
            logger.error(f"[get_chat_messages] Timeout при получении сообщений для user_id={user_id}")
            raise KworkAPIError(f"Timeout при получении сообщений от user_id={user_id}") from e

        except aiohttp.ClientConnectorError as e:
            logger.error(f"[get_chat_messages] Ошибка подключения: {e}")
            raise KworkAPIError(f"Ошибка подключения при получении сообщений: {e}") from e

        except aiohttp.ServerDisconnectedError as e:
            logger.error(f"[get_chat_messages] Сервер разорвал соединение: {e}")
            raise KworkAPIError(f"Сервер разорвал соединение: {e}") from e

        except aiohttp.ClientError as e:
            logger.error(f"[get_chat_messages] Сетевая ошибка: {e}")
            raise KworkAPIError(f"Сетевая ошибка при получении сообщений: {e}") from e

        except Exception as e:
            logger.exception(f"[get_chat_messages] Непредвиденная ошибка: {e}")
            raise KworkAPIError(f"Непредвиденная ошибка при получении сообщений: {e}") from e


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
        Отправление сообщения пользователю с 3 попытками переотправки.
        :param user_id: Идентификатор пользователя
        :param text: Текст сообщения
        :return: Ответ с информацией об отправленном сообщении
        :raises KworkAPIError: если все попытки отправки не удались
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
                async with aiohttp.ClientSession(
                        base_url=self._base_url,
                        headers=self.headers
                ) as s:
                    async with s.post(
                            url="/sendmessage",
                            data=data
                    ) as r:
                        r.raise_for_status()
                        return await r.json()

            except asyncio.TimeoutError as e:
                logger.warning(f"Timeout при отправке сообщения user_id={user_id}. Попыток осталось: {retries - 1}")
                retries -= 1
                await asyncio.sleep(15)

            except aiohttp.ClientError as e:
                logger.warning(f"Сетевая ошибка при отправке сообщения user_id={user_id}: {e}. Попыток осталось: {retries - 1}")
                retries -= 1
                await asyncio.sleep(15)

            except Exception as e:
                logger.warning(f"Ошибка при отправке сообщения user_id={user_id}: {e}. Попыток осталось: {retries - 1}")
                retries -= 1
                await asyncio.sleep(15)

        logger.error(f"Все попытки отправки сообщения user_id={user_id} исчерпаны")
        raise KworkAPIError(f"Не удалось отправить сообщение пользователю {user_id} после 3 попыток")
