# -*- coding: utf-8 -*-

try:
    import asyncio
except ImportError:
    raise Exception("Python 3.5+ is required to use the async API")
import json

import aiohttp

import mygeotab
import mygeotab.api
import mygeotab.serializers


class API(mygeotab.API):
    def __init__(self, username, password=None, database=None, session_id=None, server='my.geotab.com', verify=True):
        """
        Creates a new instance of this simple asynchronous Pythonic wrapper for the MyGeotab API.

        :param username: The username used for MyGeotab servers. Usually an email address.
        :param password: The password associated with the username. Optional if `session_id` is provided.
        :param database: The database or company name. Optional as this usually gets resolved upon authentication.
        :param session_id: A session ID, assigned by the server.
        :param server: The server ie. my23.geotab.com. Optional as this usually gets resolved upon authentication.
        :param verify: If True, verify SSL certificate. It's recommended not to modify this.
        :raise Exception: Raises an Exception if a username, or one of the session_id or password is not provided.
        """
        super().__init__(username, password, database, session_id, server, verify)

    @staticmethod
    async def _query_async(api_endpoint, method, parameters, verify_ssl=True):
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
        conn = aiohttp.TCPConnector(verify_ssl=verify_ssl)
        with aiohttp.ClientSession(connector=conn) as session:
            r = await session.post(api_endpoint,
                                   data=json.dumps(params,
                                                   default=mygeotab.serializers.object_serializer),
                                   headers=headers,
                                   allow_redirects=True)
            body = await r.text()
        return API._process(json.loads(body, object_hook=mygeotab.serializers.object_deserializer))

    async def call_async(self, method, **parameters):
        """
        Makes an async call to the API.

        :param method: The method name.
        :param parameters: Additional parameters to send (for example, search=dict(id='b123') )
        :return: The JSON result (decoded into a dict) from the server
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        if method is None:
            raise Exception("Must specify a method name")
        parameters = mygeotab.api.process_parameters(parameters)
        if self.credentials is None:
            self.authenticate()
        if 'credentials' not in parameters and self.credentials.session_id:
            parameters['credentials'] = self.credentials.get_param()

        try:
            result = await self._query_async(mygeotab.api.get_api_url(self._server), method, parameters, verify_ssl=self._is_verify_ssl)
            if result is not None:
                self.__reauthorize_count = 0
                return result
        except mygeotab.MyGeotabException as exception:
            if exception.name == 'InvalidUserException' and self.__reauthorize_count == 0:
                self.__reauthorize_count += 1
                self.authenticate()
                return await self.call_async(method, **parameters)
            raise
        return None

    async def multi_call_async(self, *calls):
        """
        Performs an async multi-call to the API

        :param calls: A list of call 2-tuples with method name and params (for example, ('Get', dict(typeName='Trip')) )
        :return: The JSON result (decoded into a dict) from the server
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        formatted_calls = [dict(method=call[0], params=call[1]) for call in calls]
        return await self.call_async('ExecuteMultiCall', calls=formatted_calls)

    async def get_async(self, type_name, **parameters):
        """
        Gets entities asynchronously using the API. Shortcut for using async_call() with the 'Get' method.

        :param type_name: The type of entity
        :param parameters: Additional parameters to send.
        :return: The JSON result (decoded into a dict) from the server
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        return await self.call_async('Get', type_name=type_name, **parameters)

    async def search_async(self, type_name, **parameters):
        """
        Searches for entities asynchronously using the API. Shortcut for using async_get() with a search.

        :param type_name: The type of entity
        :param parameters: Additional parameters to send.
        :return: The JSON result (decoded into a dict) from the server
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        if parameters:
            results_limit = parameters.get('resultsLimit', None)
            if results_limit is not None:
                del parameters['resultsLimit']
            parameters = dict(search=parameters)
            return await self.call_async('Get', type_name=type_name, resultsLimit=results_limit, **parameters)
        return await self.get_async(type_name)

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
