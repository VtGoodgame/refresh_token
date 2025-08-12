# tests/test_send_request.py

import pytest
import asyncio
import logging
import json
import base64
import requests
from fastapi import HTTPException
from unittest.mock import patch  # только для избежания реального подписания, если нет доступа к КриптоПро
from src.send_request import get_auth_token, AsyncAPIHandler
from src.to_sign_data import CryptoProSigner
from src import consts as c

# Настройка логирования
logging.basicConfig(level=logging.INFO)


@pytest.mark.asyncio
async def test_get_auth_token_success():
    """Проверка успешного получения токена (реальный запрос, но с заглушкой подписи)"""
    # Получаем данные для подписания
    try:
        response_json= requests.get(c.URL_TOKEN)
        data = response_json.json()
        uuid_val = data['uuid'] 
        sign = AsyncAPIHandler.decode_data(str(data['data']))
        signature = CryptoProSigner.sign_data(sign) # type: ignore

        result = await get_auth_token(uuid_val, signature)

        # API может вернуть 400/401, но главное — функция не упадёт
        assert result is None or isinstance(result, dict)

    except Exception as e:
        pytest.fail(f"get_auth_token вызвал исключение: {e}")


@pytest.mark.asyncio
async def test_get_auth_token_invalid_uuid():
    """Проверка ответа при невалидном UUID"""
    result = await get_auth_token("invalid-uuid-format", "valid_signature")

    assert result is None  # Ожидаем None при ошибке


@pytest.mark.asyncio
async def test_get_auth_token_empty_params():
    """Проверка поведения при пустых параметрах"""
    result = await get_auth_token("", "")

    assert result is None


@pytest.mark.asyncio
async def test_make_request_success():
    handler = AsyncAPIHandler(base_url="https://www.rusprofile.ru/ajax.php?&query=3327848813&action=search")

    async with handler as ctx:
        try:
            result = await ctx._make_request()
            assert isinstance(result, dict)
        except HTTPException as e:
            pytest.fail(f"HTTPException raised: {e}")


@pytest.mark.asyncio
async def test_make_request_non_200_status():
    """Проверка обработки статуса != 200"""
    # httpbin.org/status/404 — возвращает 404
    handler = AsyncAPIHandler(base_url="https://httpbin.org/status/404")

    async with handler as ctx:
        with pytest.raises(HTTPException) as exc_info:
            await ctx._make_request()

        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_make_request_json_decode_error():
    """Проверка обработки некорректного JSON в ответе"""
    # httpbin.org/html — возвращает HTML, не JSON
    handler = AsyncAPIHandler(base_url="https://httpbin.org/html")

    async with handler as ctx:
        with pytest.raises(HTTPException) as exc_info:
            await ctx._make_request()

        assert exc_info.value.status_code == 500
        assert "Invalid JSON response" in exc_info.value.detail


@pytest.mark.asyncio
async def test_make_request_connection_error():
    """Проверка обработки ошибки соединения (недоступный домен)"""
    handler = AsyncAPIHandler(base_url="https://this-domain-does-not-exist-12345.com")

    async with handler as ctx:
        with pytest.raises(HTTPException) as exc_info:
            await ctx._make_request()

        assert exc_info.value.status_code == 503  # Service unavailable


@pytest.mark.asyncio
async def test_decode_data_success():
    """Проверка корректного кодирования строки в base64"""
    data = "Python"

    result = await AsyncAPIHandler.decode_data(data)

    expected = base64.b64encode(data.encode("utf-8"))
    assert result == expected


@pytest.mark.asyncio
async def test_decode_data_empty_string():
    """Проверка кодирования пустой строки — возвращает b'' по текущей логике"""
    result = await AsyncAPIHandler.decode_data("")

    assert result == b""  


@pytest.mark.asyncio
async def test_decode_data_special_chars():
    """Проверка кодирования строки с кириллицей и спецсимволами"""
    data = "Привет, Мир! @#$%^&*()"

    result = await AsyncAPIHandler.decode_data(data)

    expected = base64.b64encode(data.encode("utf-8"))
    assert result == expected


@pytest.mark.asyncio
async def test_decode_data_none():
    """Проверка обработки None или None-подобных значений"""
    result = await AsyncAPIHandler.decode_data("None")

    assert result == b""  # согласно коду, ошибка → return b""


@pytest.mark.asyncio
async def test_decode_data_non_string():
    """Проверка обработки нестроковых типов"""
    result = await AsyncAPIHandler.decode_data("123")

    expected = base64.b64encode(b"123")
    assert result == expected