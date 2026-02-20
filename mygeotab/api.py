# -*- coding: utf-8 -*-

"""
mygeotab.api
~~~~~~~~~~~~

Public objects and methods wrapping the MyGeotab API.
"""

from __future__ import unicode_literals

import aiohttp

from .exceptions import AuthenticationException, MyGeotabException
from .http import (
    DEFAULT_TIMEOUT,
    _process,
    _query_async,
    _run_sync,
    get_api_url,
)
from .parameters import camelcaseify_parameters, convert_get_parameters


class API(object):
    """A simple and Pythonic wrapper for the MyGeotab API."""

    def __init__(
        self,
        username,
        password=None,
        database=None,
        session_id=None,
        server="my.geotab.com",
        timeout=DEFAULT_TIMEOUT,
        proxies=None,
        cert=None,
        http_session=None,
    ):
        """Initialize the MyGeotab API object with credentials.

        :param username: The username used for MyGeotab servers. Usually an email address.
        :type username: str
        :param password: The password associated with the username. Optional if `session_id` is provided.
        :type password: str
        :param database: The database or company name. Optional as this usually gets resolved upon authentication.
        :type database: str
        :param session_id: A session ID, assigned by the server.
        :type session_id: str
        :param server: The server ie. my23.geotab.com. Optional as this usually gets resolved upon authentication.
        :type server: str or None
        :param timeout: The timeout to make the call, in seconds. By default, this is 300 seconds (or 5 minutes).
        :type timeout: float or None
        :param proxies: The proxies dictionary to apply to the request.
                        (Not supported with aiohttp, kept for API compatibility)
        :type proxies: dict or None
        :param cert: The path to client certificate. A single path to .pem file or a Tuple (.cer file, .key file).
        :type cert: str or Tuple or None
        :param http_session: An optional aiohttp.ClientSession to reuse for connection pooling.
        :type http_session: aiohttp.ClientSession or None
        :raise Exception: Raises an Exception if a username, or one of the session_id or password is not provided.
        """
        if username is None:
            raise Exception("`username` cannot be None")
        if password is None and session_id is None:
            raise Exception("`password` and `session_id` must not both be None")
        self.credentials = Credentials(
            username=username, session_id=session_id, database=database, server=server, password=password
        )
        self.timeout = timeout
        self._proxies = proxies
        self._reauthorize_count = 0
        self._cert = cert
        self._http_session = http_session
        self._owns_session = False

    @property
    def _server(self):
        if not self.credentials.server:
            self.credentials.server = "my.geotab.com"
        return self.credentials.server

    @property
    def _is_verify_ssl(self):
        """Whether or not SSL be verified.

        :rtype: bool
        :return: True if the calls are being made locally.
        """
        return not any(s in get_api_url(self._server) for s in ["127.0.0.1", "localhost"])

    def __enter__(self):
        """Sync context manager entry - creates a managed session."""
        self._http_session = _run_sync(self._create_session())
        self._owns_session = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context manager exit - closes the managed session."""
        if self._owns_session and self._http_session is not None:
            _run_sync(self._http_session.close())
            self._http_session = None
            self._owns_session = False
        return False

    async def __aenter__(self):
        """Async context manager entry - creates a managed session."""
        self._http_session = await self._create_session()
        self._owns_session = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - closes the managed session."""
        if self._owns_session and self._http_session is not None:
            await self._http_session.close()
            self._http_session = None
            self._owns_session = False
        return False

    async def _create_session(self):
        """Creates a new aiohttp ClientSession."""
        return aiohttp.ClientSession()

    def close(self):
        """Closes the HTTP session if one is managed by this API instance."""
        if self._owns_session and self._http_session is not None:
            _run_sync(self._http_session.close())
            self._http_session = None
            self._owns_session = False

    async def close_async(self):
        """Asynchronously closes the HTTP session if one is managed by this API instance."""
        if self._owns_session and self._http_session is not None:
            await self._http_session.close()
            self._http_session = None
            self._owns_session = False

    async def call_async(self, method, **parameters):
        """Makes an async call to the API.

        :param method: The method name.
        :type method: str
        :param parameters: Additional parameters to send (for example, search=dict(id='b123') ).
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        :return: The results from the server.
        :rtype: dict or list
        """
        if method is None:
            raise Exception("A method name must be specified")
        params = camelcaseify_parameters(parameters)
        if self.credentials and not self.credentials.session_id:
            await self.authenticate_async()
        if "credentials" not in params and self.credentials.session_id:
            params["credentials"] = self.credentials.get_param()

        try:
            result = await _query_async(
                self._server,
                method,
                params,
                self.timeout,
                verify_ssl=self._is_verify_ssl,
                cert=self._cert,
                session=self._http_session,
            )
            if result is not None:
                self._reauthorize_count = 0
            return result
        except MyGeotabException as exception:
            if exception.name == "InvalidUserException" or (
                exception.name == "DbUnavailableException" and "Initializing" in exception.message
            ):
                if self._reauthorize_count == 0 and self.credentials.password:
                    self._reauthorize_count += 1
                    await self.authenticate_async()
                    return await self.call_async(method, **parameters)
                else:
                    raise AuthenticationException(
                        self.credentials.username, self.credentials.database, self.credentials.server
                    ) from exception
            raise

    def call(self, method, **parameters):
        """Makes a call to the API.

        :param method: The method name.
        :type method: str
        :param parameters: Additional parameters to send (for example, search=dict(id='b123') ).
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        :return: The results from the server.
        :rtype: dict or list
        """
        return _run_sync(self.call_async(method, **parameters))

    async def multi_call_async(self, calls):
        """Performs an async multi-call to the API.

        :param calls: A list of call 2-tuples with method name and params
                      (for example, ('Get', dict(typeName='Trip')) ).
        :type calls: list((str, dict))
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        :return: The results from the server.
        :rtype: list
        """
        formatted_calls = [dict(method=call[0], params=call[1] if len(call) > 1 else {}) for call in calls]
        return await self.call_async("ExecuteMultiCall", calls=formatted_calls)

    def multi_call(self, calls):
        """Performs a multi-call to the API.

        :param calls: A list of call 2-tuples with method name and params
                      (for example, ('Get', dict(typeName='Trip')) ).
        :type calls: list((str, dict))
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        :return: The results from the server.
        :rtype: list
        """
        return _run_sync(self.multi_call_async(calls))

    async def get_async(self, type_name, **parameters):
        """Gets entities asynchronously using the API. Shortcut for using call_async() with the 'Get' method.

        :param type_name: The type of entity.
        :type type_name: str
        :param parameters: Additional parameters to send.
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        :return: The results from the server.
        :rtype: list
        """
        return await self.call_async("Get", type_name=type_name, **convert_get_parameters(parameters))

    def get(self, type_name, **parameters):
        """Gets entities using the API. Shortcut for using call() with the 'Get' method.

        :param type_name: The type of entity.
        :type type_name: str
        :param parameters: Additional parameters to send. A parameter called `resultsLimit`
                           or `results_limit` will limit the number of entries returned. A
                           `search` parameter can further limit results, for example
                           search=dict(id='b123'). If a parameter called `search` is
                           omitted, any additional parameters are automatically added
                           to a `search` dictionary. This simplifies basic usage.
                           The following are equivalent calls:
                           api.get("Device", search={"id":"b2"})
                           api.get("Device", id="b2)
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        :return: The results from the server.
        :rtype: list
        """
        return _run_sync(self.get_async(type_name, **parameters))

    async def add_async(self, type_name, entity):
        """Adds an entity asynchronously using the API. Shortcut for using call_async() with the 'Add' method.

        :param type_name: The type of entity.
        :type type_name: str
        :param entity: The entity to add.
        :type entity: dict
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        :return: The id of the object added.
        :rtype: str
        """
        return await self.call_async("Add", type_name=type_name, entity=entity)

    def add(self, type_name, entity):
        """Adds an entity using the API. Shortcut for using call() with the 'Add' method.

        :param type_name: The type of entity.
        :type type_name: str
        :param entity: The entity to add.
        :type entity: dict
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        :return: The id of the object added.
        :rtype: str
        """
        return _run_sync(self.add_async(type_name, entity))

    async def set_async(self, type_name, entity):
        """Sets an entity asynchronously using the API. Shortcut for using call_async() with the 'Set' method.

        :param type_name: The type of entity.
        :type type_name: str
        :param entity: The entity to set.
        :type entity: dict
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        """
        return await self.call_async("Set", type_name=type_name, entity=entity)

    def set(self, type_name, entity):
        """Sets an entity using the API. Shortcut for using call() with the 'Set' method.

        :param type_name: The type of entity.
        :type type_name: str
        :param entity: The entity to set.
        :type entity: dict
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        """
        return _run_sync(self.set_async(type_name, entity))

    async def remove_async(self, type_name, entity):
        """Removes an entity asynchronously using the API. Shortcut for using call_async() with the 'Remove' method.

        :param type_name: The type of entity.
        :type type_name: str
        :param entity: The entity to remove.
        :type entity: dict
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        """
        return await self.call_async("Remove", type_name=type_name, entity=entity)

    def remove(self, type_name, entity):
        """Removes an entity using the API. Shortcut for using call() with the 'Remove' method.

        :param type_name: The type of entity.
        :type type_name: str
        :param entity: The entity to remove.
        :type entity: dict
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        """
        return _run_sync(self.remove_async(type_name, entity))

    async def authenticate_async(self):
        """Authenticates asynchronously against the API server.

        :raise AuthenticationException: Raises if there was an issue with authenticating or logging in.
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        :return: A Credentials object with a session ID created by the server.
        :rtype: Credentials
        """
        try:
            if self.credentials.session_id and not self.credentials.password:
                # Extend the session if only the session ID is present
                extend_session_data = dict(
                    database=self.credentials.database,
                    userName=self.credentials.username,
                    sessionId=self.credentials.session_id,
                )
                await _query_async(
                    self._server,
                    "ExtendSession",
                    extend_session_data,
                    self.timeout,
                    verify_ssl=self._is_verify_ssl,
                    cert=self._cert,
                    session=self._http_session,
                )
                return self.credentials

            auth_data = dict(
                database=self.credentials.database,
                userName=self.credentials.username,
                password=self.credentials.password,
            )
            result = await _query_async(
                self._server,
                "Authenticate",
                auth_data,
                self.timeout,
                verify_ssl=self._is_verify_ssl,
                cert=self._cert,
                session=self._http_session,
            )
            if result:
                if "path" not in result and self.credentials.session_id:
                    # Session was extended
                    return self.credentials
                new_server = result["path"]
                server = self.credentials.server
                if new_server != "ThisServer":
                    server = new_server
                credentials = result["credentials"]
                self.credentials = Credentials(
                    credentials["userName"], credentials["sessionId"], credentials["database"], server
                )
                return self.credentials
        except MyGeotabException as exception:
            if exception.name == "InvalidUserException" or (
                exception.name == "DbUnavailableException"
                and ("Initializing" in exception.message or "UnknownDatabase" in exception.message)
            ):
                raise AuthenticationException(
                    self.credentials.username, self.credentials.database, self.credentials.server
                ) from exception
            raise

    def authenticate(self):
        """Authenticates against the API server.

        :raise AuthenticationException: Raises if there was an issue with authenticating or logging in.
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        :return: A Credentials object with a session ID created by the server.
        :rtype: Credentials
        """
        return _run_sync(self.authenticate_async())

    @staticmethod
    def from_credentials(credentials):
        """Returns a new API object from an existing Credentials object.

        :param credentials: The existing saved credentials.
        :type credentials: Credentials
        :return: A new API object populated with MyGeotab credentials.
        :rtype: API
        """
        return API(
            username=credentials.username,
            password=credentials.password,
            database=credentials.database,
            session_id=credentials.session_id,
            server=credentials.server,
        )


class Credentials(object):
    """The MyGeotab Credentials object."""

    def __init__(self, username, session_id, database, server, password=None):
        """Initialize the Credentials object.

        :param username: The username used for MyGeotab servers. Usually an email address.
        :type username: str
        :param session_id: A session ID, assigned by the server.
        :type session_id: str
        :param database: The database or company name. Optional as this usually gets resolved upon authentication.
        :type database: str or None
        :param server: The server ie. my23.geotab.com. Optional as this usually gets resolved upon authentication.
        :type server: str or None
        :param password: The password associated with the username. Optional if `session_id` is provided.
        :type password: str or None
        """
        self.username = username
        self.session_id = session_id
        self.database = database
        self.server = server
        self.password = password

    def __str__(self):
        return "{0} @ {1}/{2}".format(self.username, self.server, self.database)

    def __repr__(self):
        return "Credentials(username={username}, database={database})".format(username=self.username, database=self.database)

    def get_param(self):
        """A simple representation of the credentials object for passing into the API.authenticate() server call.

        :return: The simple credentials object for use by API.authenticate().
        :rtype: dict
        """
        return dict(userName=self.username, sessionId=self.session_id, database=self.database)


def server_call(method, server, timeout=DEFAULT_TIMEOUT, verify_ssl=True, proxies=None, **parameters):
    """Makes a call to an un-authenticated method on a server

    :param method: The method name.
    :type method: str
    :param server: The MyGeotab server.
    :type server: str
    :param timeout: The timeout to make the call, in seconds. By default, this is 300 seconds (or 5 minutes).
    :type timeout: float
    :param verify_ssl: If True, verify the SSL certificate. It's recommended not to modify this.
    :type verify_ssl: bool
    :param proxies: The proxies dictionary to apply to the request. (Not supported with aiohttp, kept for API compatibility)
    :type proxies: dict or None
    :param parameters: Additional parameters to send (for example, search=dict(id='b123') ).
    :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
    :raise TimeoutException: Raises when the request does not respond after some time.
    :return: The result from the server.
    """
    return _run_sync(server_call_async(method, server, timeout=timeout, verify_ssl=verify_ssl, **parameters))


async def server_call_async(method, server, timeout=DEFAULT_TIMEOUT, verify_ssl=True, **parameters):
    """Makes an asynchronous call to an un-authenticated method on a server.

    :param method: The method name.
    :type method: str
    :param server: The MyGeotab server.
    :type server: str
    :param timeout: The timeout to make the call, in seconds. By default, this is 300 seconds (or 5 minutes).
    :type timeout: float
    :param verify_ssl: If True, verify the SSL certificate. It's recommended not to modify this.
    :type verify_ssl: bool
    :param parameters: Additional parameters to send (for example, search=dict(id='b123') ).
    :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
    :raise TimeoutException: Raises when the request does not respond after some time.
    :return: The result from the server.
    """
    if method is None:
        raise Exception("A method name must be specified")
    if server is None:
        raise Exception("A server (eg. my3.geotab.com) must be specified")
    parameters = camelcaseify_parameters(parameters)
    return await _query_async(server, method, parameters, timeout=timeout, verify_ssl=verify_ssl)


__all__ = [
    "API",
    "Credentials",
    "MyGeotabException",
    "AuthenticationException",
    "server_call",
    "server_call_async",
    "_process",
]
