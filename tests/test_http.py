"""Tests for mygeotab.http module — SSL context, headers, URL formatting, and query paths."""

import asyncio
import ssl
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from mygeotab.exceptions import TimeoutException
from mygeotab.http import (
    _create_ssl_context,
    _query_async,
    get_api_url,
    get_headers,
)


class TestGetApiUrl:
    def test_plain_host(self):
        assert get_api_url("my3.geotab.com") == "https://my3.geotab.com/apiv1"

    def test_https_url(self):
        assert get_api_url("https://my3.geotab.com") == "https://my3.geotab.com/apiv1"

    def test_strips_trailing_slash(self):
        assert get_api_url("my3.geotab.com/") == "https://my3.geotab.com/apiv1"


class TestGetHeaders:
    def test_contains_user_agent_and_content_type(self):
        headers = get_headers()
        assert "Content-type" in headers
        assert "application/json" in headers["Content-type"]
        assert "User-Agent" in headers
        assert "Python/" in headers["User-Agent"]
        assert "mygeotab-python/" in headers["User-Agent"]


class TestCreateSslContext:
    def test_no_verify_no_cert_returns_false(self):
        result = _create_ssl_context(verify_ssl=False, cert=None)
        assert result is False

    def test_verify_ssl_returns_context(self):
        ctx = _create_ssl_context(verify_ssl=True, cert=None)
        assert isinstance(ctx, ssl.SSLContext)

    def test_cert_string(self):
        with patch.object(ssl.SSLContext, "load_cert_chain") as mock_load, \
             patch.object(ssl.SSLContext, "load_default_certs"):
            ctx = _create_ssl_context(verify_ssl=True, cert="/path/to/cert.pem")
            assert isinstance(ctx, ssl.SSLContext)
            mock_load.assert_called_once_with("/path/to/cert.pem")

    def test_cert_tuple(self):
        with patch.object(ssl.SSLContext, "load_cert_chain") as mock_load, \
             patch.object(ssl.SSLContext, "load_default_certs"):
            ctx = _create_ssl_context(verify_ssl=True, cert=("/path/cert.cer", "/path/key.key"))
            assert isinstance(ctx, ssl.SSLContext)
            mock_load.assert_called_once_with("/path/cert.cer", "/path/key.key")

    def test_no_verify_with_cert_still_creates_context(self):
        with patch.object(ssl.SSLContext, "load_cert_chain"), \
             patch.object(ssl.SSLContext, "load_default_certs"):
            ctx = _create_ssl_context(verify_ssl=False, cert="/path/to/cert.pem")
            assert isinstance(ctx, ssl.SSLContext)


class TestQueryAsync:
    @pytest.mark.asyncio
    async def test_non_json_content_type_returns_body(self):
        """When server returns non-JSON content type, return raw body text."""
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text = AsyncMock(return_value="<html>Not JSON</html>")

        mock_session = AsyncMock(spec=aiohttp.ClientSession)
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await _query_async("my.geotab.com", "SomeMethod", {}, session=mock_session)
        assert result == "<html>Not JSON</html>"

    @pytest.mark.asyncio
    async def test_json_content_type_processes_result(self):
        """When server returns JSON, process through _process."""
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = AsyncMock(return_value='{"result": [{"id": "b1"}]}')

        mock_session = AsyncMock(spec=aiohttp.ClientSession)
        mock_session.post = AsyncMock(return_value=mock_response)

        result = await _query_async("my.geotab.com", "Get", {}, session=mock_session)
        assert result == [{"id": "b1"}]

    @pytest.mark.asyncio
    async def test_creates_session_when_none_provided(self):
        """When no session is provided, create a new one."""
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = AsyncMock(return_value='{"result": "ok"}')

        with patch("mygeotab.http.aiohttp.ClientSession") as mock_cls, \
             patch("mygeotab.http.aiohttp.TCPConnector"):
            mock_session_instance = AsyncMock()
            mock_session_instance.post = AsyncMock(return_value=mock_response)
            mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_session_instance

            result = await _query_async("my.geotab.com", "Get", {}, session=None)
            assert result == "ok"

    @pytest.mark.asyncio
    async def test_timeout_raises_timeout_exception(self):
        """asyncio.TimeoutError should be wrapped in TimeoutException."""
        mock_session = AsyncMock(spec=aiohttp.ClientSession)
        mock_session.post = AsyncMock(side_effect=asyncio.TimeoutError())

        with pytest.raises(TimeoutException) as excinfo:
            await _query_async("my.geotab.com", "Get", {}, session=mock_session)
        assert excinfo.value.server == "my.geotab.com"
