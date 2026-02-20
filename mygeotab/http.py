# -*- coding: utf-8 -*-

"""
mygeotab.http
~~~~~~~~~~~~~

Shared HTTP layer using aiohttp for all API communication.
"""

from __future__ import unicode_literals

import asyncio
import ssl
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import aiohttp

from . import __title__, __version__
from .exceptions import MyGeotabException, TimeoutException
from .serializers import json_deserialize, json_serialize

DEFAULT_TIMEOUT = 300


def get_api_url(server):
    """Formats the server URL properly in order to query the API.

    :param server: The server to format.
    :type server: str
    :return: A valid MyGeotab API request URL.
    :rtype: str
    """
    parsed = urlparse(server)
    base_url = parsed.netloc if parsed.netloc else parsed.path
    base_url.replace("/", "")
    return "https://" + base_url + "/apiv1"


def get_headers():
    """Gets the request headers.

    :return: The user agent
    :rtype: dict
    """
    return {
        "Content-type": "application/json; charset=UTF-8",
        "User-Agent": "Python/{py_version[0]}.{py_version[1]} {title}/{version}".format(
            py_version=sys.version_info, title=__title__, version=__version__
        ),
    }


def _create_ssl_context(verify_ssl=True, cert=None):
    """Creates an SSL context for aiohttp connections.

    :param verify_ssl: Whether to verify SSL certificates.
    :type verify_ssl: bool
    :param cert: Client certificate path or tuple (cert, key).
    :type cert: str or tuple or None
    :return: SSL context or False if SSL verification is disabled.
    :rtype: ssl.SSLContext or bool
    """
    if not verify_ssl and not cert:
        return False

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.load_default_certs()
    if hasattr(ssl, "OP_ENABLE_MIDDLEBOX_COMPAT"):
        ssl_context.options |= ssl.OP_ENABLE_MIDDLEBOX_COMPAT

    if cert:
        if isinstance(cert, str):
            ssl_context.load_cert_chain(cert)
        elif isinstance(cert, tuple):
            cer, key = cert
            ssl_context.load_cert_chain(cer, key)

    return ssl_context


def _process(data):
    """Processes the returned JSON from the server.

    :param data: The JSON data in dict form.
    :raise MyGeotabException: Raises when a server exception was encountered.
    :return: The result data.
    """
    if data:
        if "error" in data:
            raise MyGeotabException(data["error"])
        if "result" in data:
            return data["result"]
    return data


async def _query_async(
    server,
    method,
    parameters,
    timeout=DEFAULT_TIMEOUT,
    verify_ssl=True,
    cert=None,
    session=None,
):
    """Formats and performs the asynchronous query against the API.

    :param server: The server to query.
    :type server: str
    :param method: The method name.
    :type method: str
    :param parameters: A dict of parameters to send.
    :type parameters: dict
    :param timeout: The timeout to make the call, in seconds.
    :type timeout: float
    :param verify_ssl: Whether or not to verify SSL connections.
    :type verify_ssl: bool
    :param cert: The path to client certificate.
    :type cert: str or tuple or None
    :param session: An optional aiohttp.ClientSession to reuse.
    :type session: aiohttp.ClientSession or None
    :return: The JSON-decoded result from the server.
    :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
    :raise TimeoutException: Raises when the request does not respond after some time.
    :raise aiohttp.ClientResponseError: Raises when there is an HTTP status code that indicates failure.
    """
    api_endpoint = get_api_url(server)
    params = dict(id=-1, method=method, params=parameters or {})
    headers = get_headers()

    ssl_context = _create_ssl_context(verify_ssl, cert)
    client_timeout = aiohttp.ClientTimeout(total=timeout)

    async def do_request(client_session):
        response = await client_session.post(
            api_endpoint,
            data=json_serialize(params),
            headers=headers,
            timeout=client_timeout,
            allow_redirects=True,
            ssl=ssl_context,
        )
        response.raise_for_status()
        content_type = response.headers.get("Content-Type")
        body = await response.text()
        if content_type and "application/json" not in content_type.lower():
            return body
        return _process(json_deserialize(body))

    try:
        if session is not None:
            return await do_request(session)
        else:
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as new_session:
                return await do_request(new_session)
    except asyncio.TimeoutError as exc:
        raise TimeoutException(server) from exc


def _run_sync(coro):
    """Runs an async coroutine synchronously.

    Handles both cases:
    1. No event loop running -> use asyncio.run()
    2. Event loop already running (Jupyter, nested async) -> run in thread pool

    :param coro: The coroutine to run.
    :return: The result of the coroutine.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is None:
        return asyncio.run(coro)
    else:
        # Event loop is already running (e.g., Jupyter, nested async)
        # Run in a separate thread to avoid blocking
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
