# -*- coding: utf-8 -*-

import sys
if sys.version_info < (3, 5):
    raise Exception('Python 3.5+ is required to use the async API')
import asyncio
import json
import ssl
import typing
import types
import warnings

import aiohttp

import mygeotab
import mygeotab.api
import mygeotab.serializers


class API(mygeotab.API):
    def __init__(self, username, password=None, database=None, session_id=None, server='my.geotab.com', verify=True, loop=None):
        """
        Creates a new instance of this simple asynchronous Pythonic wrapper for the MyGeotab API.

        :param username: The username used for MyGeotab servers. Usually an email address.
        :param password: The password associated with the username. Optional if `session_id` is provided.
        :param database: The database or company name. Optional as this usually gets resolved upon authentication.
        :param session_id: A session ID, assigned by the server.
        :param server: The server ie. my23.geotab.com. Optional as this usually gets resolved upon authentication.
        :param verify: If True, verify SSL certificate. It's recommended not to modify this.
        :param loop: The asyncio event loop
        :raise Exception: Raises an Exception if a username, or one of the session_id or password is not provided.
        """
        self.loop = loop
        super().__init__(username, password, database, session_id, server, verify)

    async def call_async(self, method, **parameters):
        """
        Makes an async call to the API.

        :param method: The method name.
        :param params: Additional parameters to send (for example, search=dict(id='b123') )
        :return: The JSON result (decoded into a dict) from the server
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        if method is None:
            raise Exception('A method name must be specified')
        params = mygeotab.api.process_parameters(parameters)
        if self.credentials and not self.credentials.session_id:
            self.authenticate()
        if 'credentials' not in params and self.credentials.session_id:
            params['credentials'] = self.credentials.get_param()

        try:
            result = await _query(mygeotab.api.get_api_url(self._server), method, params, verify_ssl=self._is_verify_ssl, loop=self.loop)
            if result is not None:
                self.__reauthorize_count = 0
            return result
        except mygeotab.MyGeotabException as exception:
            if exception.name == 'InvalidUserException' and self.__reauthorize_count == 0:
                self.__reauthorize_count += 1
                self.authenticate()
                return await self.call_async(method, **parameters)
            raise

    async def multi_call_async(self, calls):
        """
        Performs an async multi-call to the API

        :param calls: A list of call 2-tuples with method name and params (for example, ('Get', dict(typeName='Trip')) )
        :return: The JSON result (decoded into a dict) from the server
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        formatted_calls = [dict(method=call[0], params=call[1] if len(call) > 1 else {}) for call in calls]
        return await self.call_async('ExecuteMultiCall', calls=formatted_calls)

    async def get_async(self, type_name, **parameters):
        """
        Gets entities asynchronously using the API. Shortcut for using async_call() with the 'Get' method.

        :param type_name: The type of entity
        :param parameters: Additional parameters to send.
        :return: The JSON result (decoded into a dict) from the server
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        if parameters:
            results_limit = parameters.get('resultsLimit', None)
            if results_limit is not None:
                del parameters['resultsLimit']
            if 'search' in parameters:
                parameters.update(parameters['search'])
            parameters = dict(search=parameters, resultsLimit=results_limit)
        return await self.call_async('Get', type_name=type_name, **parameters)

    async def search_async(self, type_name, **parameters):
        """
        Searches for entities asynchronously using the API. Shortcut for using async_get() with a search.

        :param type_name: The type of entity
        :param parameters: Additional parameters to send.
        :return: The JSON result (decoded into a dict) from the server
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        warnings.simplefilter('always', DeprecationWarning)  # turn off filter
        warnings.warn("'search_async()' is deprecated. Use 'get_async()' instead", DeprecationWarning, stacklevel=2)
        warnings.simplefilter('default', DeprecationWarning)  # turn off filter
        return await self.get_async(type_name, **parameters)

    async def add_async(self, type_name, entity):
        """
        Adds an entity asynchronously using the API. Shortcut for using async_call() with the 'Add' method.

        :param type_name: The type of entity
        :param entity: The entity to add
        :return: The id of the object added
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        return await self.call_async('Add', type_name=type_name, entity=entity)

    async def set_async(self, type_name, entity):
        """
        Sets an entity asynchronously using the API. Shortcut for using async_call() with the 'Set' method.

        :param type_name: The type of entity
        :param entity: The entity to set
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        return await self.call_async('Set', type_name=type_name, entity=entity)

    async def remove_async(self, type_name, entity):
        """
        Removes an entity asynchronously using the API. Shortcut for using async_call() with the 'Remove' method.

        :param type_name: The type of entity
        :param entity: The entity to remove
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        return await self.call_async('Remove', type_name=type_name, entity=entity)


def run(*tasks: typing.List[types.CoroutineType], loop: asyncio.AbstractEventLoop=asyncio.get_event_loop()):
    futures = [asyncio.ensure_future(task, loop=loop) for task in tasks]
    return loop.run_until_complete(asyncio.gather(*futures))


def from_credentials(credentials, loop: asyncio.AbstractEventLoop=None):
    """
    Returns a new async API object from an existing Credentials object

    :param credentials: The existing saved credentials
    :param loop: The asyncio loop
    :return: A new API object populated with MyGeotab credentials
    """
    return API(username=credentials.username, password=credentials.password,
               database=credentials.database, session_id=credentials.session_id,
               server=credentials.server, loop=loop)

async def server_call(method, server, loop: asyncio.AbstractEventLoop=asyncio.get_event_loop(), verify=True, **parameters):
    """
    Makes an asynchronous call to an un-authenticated method on a server

    :param method: The method name
    :param server: The MyGeotab server
    :param loop: The asyncio loop
    :param verify: If True, verify SSL certificate. It's recommended not to modify this.
    :param parameters: Additional parameters to send (for example, search=dict(id='b123') )
    :return: The JSON result (decoded into a dict) from the server
    :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
    """
    if method is None:
        raise Exception("A method name must be specified")
    if server is None:
        raise Exception("A server (eg. my3.geotab.com) must be specified")
    parameters = mygeotab.api.process_parameters(parameters)
    return await _query(mygeotab.api.get_api_url(server), method, parameters, verify_ssl=verify, loop=loop)

async def _query(api_endpoint, method, parameters, verify_ssl=True, loop: asyncio.AbstractEventLoop=None):
    """
    Formats and performs the asynchronous query against the API

    :param api_endpoint: The API endpoint to query
    :param method: The method name.
    :param parameters: A dict of parameters to send
    :param verify_ssl: Whether or not to verify SSL connections
    :return: The JSON-decoded result from the server
    :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
    """
    params = dict(id=-1, method=method, params=parameters)
    headers = {'Content-type': 'application/json; charset=UTF-8'}
    ssl_context = None
    verify = verify_ssl
    if verify_ssl:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    conn = aiohttp.TCPConnector(verify_ssl=verify, ssl_context=ssl_context, loop=loop)
    async with aiohttp.ClientSession(connector=conn, loop=loop) as session:
        r = await session.post(api_endpoint,
                               data=json.dumps(params,
                                               default=mygeotab.serializers.object_serializer),
                               headers=headers,
                               allow_redirects=True)
        body = await r.text()
    return mygeotab.api._process(json.loads(body, object_hook=mygeotab.serializers.object_deserializer))
