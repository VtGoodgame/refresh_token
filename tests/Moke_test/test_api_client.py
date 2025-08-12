# Moke tests/test_api.py

import pytest
import asyncio
import logging
from unittest.mock import patch
from fastapi import HTTPException
from aiohttp import ClientSession, ClientError
import aioresponses
from src import send_request as send
from src.send_request import AsyncAPIHandler as Handler

class TestAsyncAPIHandler:

    @pytest.fixture
    def handler(self):
        return Handler(base_url="https://test-api.com")

    @pytest.fixture
    def mock_aiohttp_session(self):
        with aioresponses.aioresponses() as m:
            yield m

    # === Тесты для __aenter__ и __aexit__ ===

    @pytest.mark.asyncio
    async def test_aenter_initializes_session(self, handler):
        """Проверка, что __aenter__ инициализирует сессию"""
        async with handler as ctx:
            assert isinstance(ctx.session, ClientSession)
            assert not ctx.session.closed

    @pytest.mark.asyncio
    async def test_aexit_closes_session(self, handler):
        """Проверка, что __aexit__ закрывает сессию"""
        async with handler as ctx:
            session = ctx.session
        assert session.closed

    # === Тесты для _make_request ===

    @pytest.mark.asyncio
    async def test_make_request_success(self, handler, mock_aiohttp_session):
        """Успешный запрос"""
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
        """Обработка ошибки API (не 200)"""
        mock_aiohttp_session.get(
            "https://test-api.com",
            payload={"message": "Ошибка сервера"},
            status=400
        )
        async with handler as ctx:
            with pytest.raises(HTTPException) as exc_info:
                await ctx._make_request()
            assert exc_info.value.status_code == 400
            assert "Ошибка сервера" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_make_request_client_error(self, handler, mock_aiohttp_session):
        """Обработка сетевой ошибки"""
        mock_aiohttp_session.get("https://test-api.com", exception=ClientError("Network error"))
        async with handler as ctx:
            with pytest.raises(HTTPException) as exc_info:
                await ctx._make_request()
            assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_make_request_json_decode_error(self, handler, mock_aiohttp_session):
        """Обработка ошибки декодирования JSON"""
        mock_aiohttp_session.get("https://test-api.com", body="not json", status=200)
        async with handler as ctx:
            with pytest.raises(HTTPException) as exc_info:
                await ctx._make_request()
            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_make_request_timeout_error(self, handler):
        """Обработка таймаута"""
        async with handler as ctx:
            with patch.object(ctx.session, '_request', side_effect=asyncio.TimeoutError):
                with pytest.raises(HTTPException) as exc_info:
                    await ctx._make_request()
                assert exc_info.value.status_code == 504

    # === Тесты для decode_data ===

    @pytest.mark.asyncio
    async def test_decode_data_success(self, caplog):
        """Проверка успешного кодирования """
        data = "Hello"
        with caplog.at_level(logging.ERROR):
            result = await Handler.decode_data(data)
            assert len(result) > 0  
            


    # === Тесты для get_auth_token ===

    @pytest.mark.asyncio
    async def test_get_auth_token_success(self, mock_aiohttp_session):
        """Успешное получение токена"""
        mock_uuid = "7375daeb-4427-48d8-919d-276073fc4e7f"
        mock_signature = await Handler.decode_data("await Handler.decode_data")

        mock_aiohttp_session.post(
            "https://api.mdlp.crpt.ru/api/v1/token",
            payload={"token": "abc123"},
            status=200
        )
        result = await send.get_auth_token(uuid_val=mock_uuid, signature=mock_signature) # type: ignore
        assert result == {"token": "abc123"}

    @pytest.mark.asyncio
    async def test_get_auth_token_failure(self, mock_aiohttp_session, caplog):
        """Обработка ошибки при получении токена"""
        mock_aiohttp_session.post(
            "https://api.mdlp.crpt.ru/api/v1/token",
            status=500
        )
        with caplog.at_level(logging.ERROR):
            result = await send.get_auth_token(uuid_val="uuid", signature="data")
            assert result is None
            assert "Token request failed" in caplog.text