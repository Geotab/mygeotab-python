# -*- coding: utf-8 -*-

"""
mygeotab.async.api
~~~~~~~~~~~~~~~~~~

Async/Await-able (Python 3.5+) public objects and methods wrapping the MyGeotab API.
"""

import sys

if sys.version_info < (3, 5):
    raise Exception('Python 3.5+ is required to use the async API')
import asyncio
import json
import ssl
from concurrent.futures import TimeoutError
from typing import Awaitable

import aiohttp

from mygeotab import api
from mygeotab.api import DEFAULT_TIMEOUT
from mygeotab.exceptions import MyGeotabException, TimeoutException
from mygeotab.serializers import object_serializer, object_deserializer


class API(api.API):
    """A simple, asynchronous, and Pythonic wrapper for the MyGeotab API.
    """

    def __init__(self, username, password=None, database=None, session_id=None, server='my.geotab.com',
                 timeout=DEFAULT_TIMEOUT, loop=None):
        """
        Initialize the asynchronous MyGeotab API object with credentials.

        :param username: The username used for MyGeotab servers. Usually an email address.
        :param password: The password associated with the username. Optional if `session_id` is provided.
        :param database: The database or company name. Optional as this usually gets resolved upon authentication.
        :param session_id: A session ID, assigned by the server.
        :param server: The server ie. my23.geotab.com. Optional as this usually gets resolved upon authentication.
        :param timeout: The timeout to make the call, in seconds. By default, this is 300 seconds (or 5 minutes).
        :param loop: The asyncio event loop.
        :raise Exception: Raises an Exception if a username, or one of the session_id or password is not provided.
        """
        self.loop = loop
        super().__init__(username, password, database, session_id, server, timeout)

    async def call_async(self, method, **parameters):
        """Makes an async call to the API.

        :param method: The method name.
        :param params: Additional parameters to send (for example, search=dict(id='b123') )
        :return: The JSON result (decoded into a dict) from the server.abs
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        """
        if method is None:
            raise Exception('A method name must be specified')
        params = api.process_parameters(parameters)
        if self.credentials and not self.credentials.session_id:
            self.authenticate()
        if 'credentials' not in params and self.credentials.session_id:
            params['credentials'] = self.credentials.get_param()

        try:
            result = await _query(self._server, method, params,
                                  verify_ssl=self._is_verify_ssl, loop=self.loop)
            if result is not None:
                self.__reauthorize_count = 0
            return result
        except MyGeotabException as exception:
            if exception.name == 'InvalidUserException' and self.__reauthorize_count == 0:
                self.__reauthorize_count += 1
                self.authenticate()
                return await self.call_async(method, **parameters)
            raise

    async def multi_call_async(self, calls):
        """Performs an async multi-call to the API

        :param calls: A list of call 2-tuples with method name and params (for example, ('Get', dict(typeName='Trip')) )
        :return: The JSON result (decoded into a dict) from the server
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        :raise TimeoutException: Raises when the request does not respond after some time.
        """
        formatted_calls = [dict(method=call[0], params=call[1] if len(call) > 1 else {}) for call in calls]
        return await self.call_async('ExecuteMultiCall', calls=formatted_calls)

    async def get_async(self, type_name, **parameters):
        """Gets entities asynchronously using the API. Shortcut for using async_call() with the 'Get' method.

        :param type_name: The type of entity.
        :param parameters: Additional parameters to send.
        :return: The JSON result (decoded into a dict) from the server.
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        """
        if parameters:
            results_limit = parameters.get('resultsLimit', None)
            if results_limit is not None:
                del parameters['resultsLimit']
            if 'search' in parameters:
                parameters.update(parameters['search'])
            parameters = dict(search=parameters, resultsLimit=results_limit)
        return await self.call_async('Get', type_name=type_name, **parameters)

    async def add_async(self, type_name, entity):
        """
        Adds an entity asynchronously using the API. Shortcut for using async_call() with the 'Add' method.

        :param type_name: The type of entity.
        :param entity: The entity to add.
        :return: The id of the object added.
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        """
        return await self.call_async('Add', type_name=type_name, entity=entity)

    async def set_async(self, type_name, entity):
        """Sets an entity asynchronously using the API. Shortcut for using async_call() with the 'Set' method.

        :param type_name: The type of entity
        :param entity: The entity to set
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        return await self.call_async('Set', type_name=type_name, entity=entity)

    async def remove_async(self, type_name, entity):
        """Removes an entity asynchronously using the API. Shortcut for using async_call() with the 'Remove' method.

        :param type_name: The type of entity.
        :param entity: The entity to remove.
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        """
        return await self.call_async('Remove', type_name=type_name, entity=entity)

    @staticmethod
    def from_credentials(credentials, loop: asyncio.AbstractEventLoop=asyncio.get_event_loop()):
        """Returns a new async API object from an existing Credentials object.

        :param credentials: The existing saved credentials.
        :param loop: The asyncio loop.
        :return: A new API object populated with MyGeotab credentials.
        """
        return API(username=credentials.username, password=credentials.password,
                   database=credentials.database, session_id=credentials.session_id,
                   server=credentials.server, loop=loop)


def run(*tasks: Awaitable, loop: asyncio.AbstractEventLoop=asyncio.get_event_loop()):
    """Helper to run tasks in the event loop

    :param tasks: Tasks to run in the event loop.
    :param loop: The event loop.
    """
    futures = [asyncio.ensure_future(task, loop=loop) for task in tasks]
    return loop.run_until_complete(asyncio.gather(*futures))


async def server_call(method, server, loop: asyncio.AbstractEventLoop=asyncio.get_event_loop(), timeout=DEFAULT_TIMEOUT,
                      verify_ssl=True, **parameters):
    """Makes an asynchronous call to an un-authenticated method on a server.

    :param method: The method name.
    :param server: The MyGeotab server.
    :param loop: The event loop.
    :param timeout: The timeout to make the call, in seconds. By default, this is 300 seconds (or 5 minutes).
    :param verify_ssl: If True, verify the SSL certificate. It's recommended not to modify this.
    :param parameters: Additional parameters to send (for example, search=dict(id='b123') ).
    :return: The JSON result (decoded into a dict) from the server.
    :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
    :raise TimeoutException: Raises when the request does not respond after some time.
    """
    if method is None:
        raise Exception("A method name must be specified")
    if server is None:
        raise Exception("A server (eg. my3.geotab.com) must be specified")
    parameters = api.process_parameters(parameters)
    return await _query(server, method, parameters, timeout=timeout, verify_ssl=verify_ssl, loop=loop)


async def _query(server, method, parameters, timeout=DEFAULT_TIMEOUT, verify_ssl=True,
                 loop: asyncio.AbstractEventLoop=None):
    """Formats and performs the asynchronous query against the API

    :param server: The server to query.
    :param method: The method name.
    :param parameters: A dict of parameters to send
    :param timeout: The timeout to make the call, in seconds. By default, this is 300 seconds (or 5 minutes).
    :param verify_ssl: Whether or not to verify SSL connections
    :return: The JSON-decoded result from the server
    :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
    :raise TimeoutException: Raises when the request does not respond after some time.
    """
    api_endpoint = api.get_api_url(server)
    params = dict(id=-1, method=method, params=parameters)
    headers = {'Content-type': 'application/json; charset=UTF-8'}
    ssl_context = None
    verify = verify_ssl
    if verify_ssl:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    conn = aiohttp.TCPConnector(verify_ssl=verify, ssl_context=ssl_context, loop=loop)
    try:
        async with aiohttp.ClientSession(connector=conn, loop=loop) as session:
            response = await session.post(api_endpoint,
                                          data=json.dumps(params,
                                                          default=object_serializer),
                                          headers=headers,
                                          timeout=timeout,
                                          allow_redirects=True)
            body = await response.text()
    except TimeoutError:
        raise TimeoutException(server)
    return api._process(json.loads(body, object_hook=object_deserializer))
