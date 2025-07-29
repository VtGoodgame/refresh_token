# src/send_request.py

from . import consts as c
import json
import logging
import base64
import uuid
from typing import Optional
from fastapi import HTTPException
from aiohttp import ClientSession, ClientError
import asyncio

async def get_auth_token(uuid_val: str, signature: str) -> Optional[dict]:
    """Получение токена авторизации через внешний API"""
    url = "https://api.mdlp.crpt.ru/api/v1/token  "
    params = {
        'code': uuid_val,
        'signature': signature
    }
    try:
        # Предполагается, что сессия будет доступна извне (например, передана или создана временно)
        # Поэтому создадим временную сессию на время запроса.
        async with ClientSession() as session:
            async with session.post(url.strip(), json=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logging.error(f"Token request failed: {resp.status}")
                    return None
    except Exception as e:
        logging.error(f"Token request failed: {e}")
        return None

class AsyncAPIHandler:
    """Асинхронный класс для обработки запросов к API Честный знак"""

    def __init__(self, base_url: str = c.URL_TOKEN):
        self.base_url = base_url.strip()  # Убираем лишние пробелы
        self.session = None

    async def __aenter__(self):
        self.session = ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _make_request(self):
        """Асинхронный базовый метод для выполнения GET-запросов"""
        try:
            async with self.session.get(self.base_url) as response:
                if response.status != 200:
                    try:
                        error_data = await response.json()
                    except json.JSONDecodeError:
                        error_data = {}
                    error_msg = error_data.get("message", "Неизвестная ошибка")
                    logging.error(f"Ошибка сервера: {error_msg}")
                    raise HTTPException(status_code=response.status, detail=error_msg)
                return await response.json()
        except ClientError as e:
            logging.error(f"Ошибка соединения: {str(e)}")
            raise HTTPException(status_code=503, detail="Service unavailable")
        except json.JSONDecodeError:
            logging.error("Ошибка декодирования JSON")
            raise HTTPException(status_code=500, detail="Invalid JSON response")
        except asyncio.TimeoutError:
            logging.error("Таймаут запроса")
            raise HTTPException(status_code=504, detail="Request timeout")

    @staticmethod
    async def decode_data(data: str) -> bytes:
        """кодирует строку в base64"""
        try:
            base_data = base64.b64encode(bytes(data,'utf-8'))
            return base_data
        except Exception as e:
            logging.error(f"Ошибка при кодировании в Base64: {e}")
            return b""  

    