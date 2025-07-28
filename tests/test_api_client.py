import pytest
import asyncio
import json
import logging
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from aiohttp import ClientSession, ClientError
import aiohttp
import aioresponses

from src.send_request import AsyncAPIHandler as hendler
import src.consts as c

# Тесты для AsyncAPIHandler
class TestAsyncAPIHandler:
    @pytest.fixture
    def handler(self):
        return hendler(base_url="https://test-api.com")

    @pytest.fixture
    def mock_aiohttp_session(self):
        with aioresponses.aioresponses() as m:
            yield m

    @pytest.mark.asyncio
    async def test_aenter_initializes_session(self, handler):
        """Проверка, что __aenter__ корректно инициализирует сессию"""
        async with handler as ctx:
            assert isinstance(ctx.session, ClientSession)
            assert ctx.session.closed is False

    @pytest.mark.asyncio
    async def test_aexit_closes_session(self, handler):
        """Проверка, что __aexit__ закрывает сессию"""
        async with handler as ctx:
            session = ctx.session
            assert not session.closed
        assert session.closed

    @pytest.mark.asyncio
    async def test_make_request_success(self, handler, mock_aiohttp_session):
        """Проверка успешного запроса"""
        mock_aiohttp_session.get(
            "https://test-api.com",
            payload={"data": "test"},
            status=200
        )

        async with handler as ctx:
            result = await ctx._make_request()
            assert result == {"data": "test"}

    @pytest.mark.asyncio
    async def test_make_request_non_200_status(self, handler, mock_aiohttp_session):
        """Проверка обработки ошибки API (не 200)"""
        mock_aiohttp_session.get(
            "https://test-api.com",
            payload={"message": "Ошибка сервера"},
            status=400
        )

        async with handler as ctx:
            with pytest.raises(HTTPException) as exc_info:
                await ctx._make_request()
            assert exc_info.value.status_code == 400
            assert "Ошибка API: Ошибка сервера" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_make_request_client_error(self, handler, mock_aiohttp_session):
        """Проверка обработки сетевой ошибки"""
        mock_aiohttp_session.get("https://test-api.com", exception=ClientError("Network error"))

        async with handler as ctx:
            with pytest.raises(HTTPException) as exc_info:
                await ctx._make_request()
            assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_make_request_json_decode_error(self, handler, mock_aiohttp_session):
        """Проверка ошибки декодирования JSON"""
        mock_aiohttp_session.get(
            "https://test-api.com",
            body="not a json",
            status=200
        )

        async with handler as ctx:
            with pytest.raises(HTTPException) as exc_info:
                await ctx._make_request()
            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_make_request_timeout_error(self, handler):
        """Проверка таймаута"""

        # Мокаем сессию, чтобы выбросить TimeoutError
        async def mock_get(*args, **kwargs):
            raise asyncio.TimeoutError()

        async with handler as ctx:
            ctx.session._request = mock_get  # подменяем метод
            with pytest.raises(HTTPException) as exc_info:
                await ctx._make_request()
            assert exc_info.value.status_code == 504

    # Тесты для decode_data

    @pytest.mark.asyncio
    async def test_decode_data_success(self, caplog):
        """Проверка успешного декодирования (заметим: в коде ошибка — encode вместо decode)"""
        data = "SGVsbG8="
        with patch("base64.b64decode", return_value=b"Hello") as mock_decode:
            result = await hendler.decode_data(data)
            mock_decode.assert_called_once_with(data)
            assert result == b"Hello"

    @pytest.mark.asyncio
    async def test_decode_data_exception(self, caplog):
        """Проверка обработки ошибки в decode_data"""
        with patch("base64.b64decode", side_effect=Exception("Decode error")):
            with caplog.at_level(logging.ERROR):
                result = await hendler.decode_data("invalid")
                assert result == []
                assert "Ошибка при кодировке в Base64" in caplog.text

    # Тесты для get_auth_token

    @pytest.mark.asyncio
    async def test_get_auth_token_success(self, caplog):
        """Проверка успешного получения токена"""
        mock_uuid = "123e4567-e89b-12d3-a456-426614174000"
        mock_data = "base64string"

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"token": "abc123"}
            mock_post.return_value = mock_response

            result = await hendler.get_auth_token(mock_uuid, mock_data)

            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            assert "https://api.mdlp.crpt.ru/api/v1/token" in args[0]
            assert json.loads(kwargs["data"]) == {"code": mock_uuid, "signature": mock_data}
            assert result == {"token": "abc123"}

    @pytest.mark.asyncio
    async def test_get_auth_token_failure(self, caplog):
        """Проверка обработки ошибки при получении токена"""
        with patch("requests.post", side_effect=Exception("Connection failed")):
            with caplog.at_level(logging.ERROR):
                result = await hendler.get_auth_token("uuid", "data")
                assert "Ошибка при получении токена авторизации" in caplog.text
                assert result is None  # или можно вернуть None, но в коде нет return