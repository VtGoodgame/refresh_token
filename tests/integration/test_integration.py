# tests/integration/test_integration_auth.py

import pytest
import asyncio
import logging
from typing import Dict, Optional

# Импорты из проекта
from src.send_request import get_auth_token, AsyncAPIHandler
from src.to_sign_data import CryptoProSigner  # Предполагается, что у тебя есть этот модуль
from src import consts as c

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Пропускать интеграционные тесты, если явно не запущены
pytestmark = pytest.mark.integration


class IntegrationTestAuth:
    """Класс для интеграционного теста полного цикла авторизации"""

    def __init__(self):
        self.signer = CryptoProSigner()
        self.uuid_val: Optional[str] = None
        self.data_to_sign: Optional[str] = None

    async def fetch_auth_challenge(self) -> bool:
        """Получение challenge (uuid и data) от сервера"""
        try:
            async with AsyncAPIHandler(base_url=c.URL_TOKEN) as handler:
                response = await handler._make_request()
                if isinstance(response, dict) and "uuid" in response and "data" in response:
                    self.uuid_val = response["uuid"]
                    self.data_to_sign = response["data"]
                    logger.info(f"Получен challenge: uuid={self.uuid_val}")
                    return True
                else:
                    logger.error("Ответ не содержит uuid или data")
                    return False
        except Exception as e:
            logger.error(f"Ошибка при получении challenge: {e}")
            return False

    async def sign_data(self) -> Optional[str]:
        """Подписание данных с помощью КриптоПро"""
        if not self.data_to_sign:
            logger.error("Нет данных для подписания")
            return None

        try:
            # Инициализация хранилища
            if not self.signer.initialize_store(store_location=3):  # Current User
                logger.error("Не удалось инициализировать хранилище")
                return None

            # Выбор сертификата (первого доступного)
            if not self.signer.select_certificate():
                logger.error("Не удалось выбрать сертификат")
                return None

            # Кодируем данные в base64
            encoded_data = await AsyncAPIHandler.decode_data(self.data_to_sign)

            # Подписываем
            signature = self.signer.sign_data(encoded_data, detached=True)
            if not signature:
                logger.error("Подпись не была создана")
                return None

            logger.info("Данные успешно подписаны")
            return signature
        except Exception as e:
            logger.error(f"Ошибка при подписании: {e}")
            return None

    async def request_auth_token(self, signature: str) -> Optional[Dict]:
        """Запрос токена авторизации"""
        try:
            token_data = await get_auth_token(self.uuid_val, signature)
            if token_data:
                logger.info(f"Токен получен: {token_data}")
            else:
                logger.error("Токен не получен")
            return token_data
        except Exception as e:
            logger.error(f"Ошибка при запросе токена: {e}")
            return None


@pytest.mark.asyncio
async def test_full_auth_integration():
    """Интеграционный тест: полный цикл авторизации через API"""
    test = IntegrationTestAuth()

    # Шаг 1: Получить challenge (uuid и data)
    success = await test.fetch_auth_challenge()
    assert success is True, "Не удалось получить challenge от сервера"
    assert test.uuid_val is not None, "uuid не получен"
    assert test.data_to_sign is not None, "data не получено"

    # Шаг 2: Подписать данные
    signature = await test.sign_data()
    assert signature is not None, "Не удалось создать подпись"

    # Шаг 3: Запросить токен
    token = await test.request_auth_token(signature)
    assert token is not None, "Токен не был получен"

    # Проверяем, что токен содержит ожидаемые поля (пример)
    assert "access_token" in token or "token" in token or "jwt" in token.lower(), "Токен не содержит ожидаемых полей"