# -*- coding: utf-8 -*-

"""
mygeotab.api
~~~~~~~~~~~~

Public objects and methods wrapping the MyGeotab API.
"""

from __future__ import unicode_literals

import copy
import re
import ssl
import sys

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import Timeout
from requests.packages import urllib3
from six.moves.urllib.parse import urlparse

from . import __title__, __version__
from .exceptions import AuthenticationException, MyGeotabException, TimeoutException
from .serializers import json_deserialize, json_serialize

DEFAULT_TIMEOUT = 300


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
        :type proxies: dict or None
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
        self.__reauthorize_count = 0

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
        if method is None:
            raise Exception("A method name must be specified")
        params = process_parameters(parameters)
        if self.credentials and not self.credentials.session_id:
            self.authenticate()
        if "credentials" not in params and self.credentials.session_id:
            params["credentials"] = self.credentials.get_param()

        try:
            result = _query(
                self._server, method, params, self.timeout, verify_ssl=self._is_verify_ssl, proxies=self._proxies
            )
            if result is not None:
                self.__reauthorize_count = 0
            return result
        except MyGeotabException as exception:
            if exception.name == "InvalidUserException":
                if self.__reauthorize_count == 0 and self.credentials.password:
                    self.__reauthorize_count += 1
                    self.authenticate()
                    return self.call(method, **parameters)
                else:
                    raise AuthenticationException(
                        self.credentials.username, self.credentials.database, self.credentials.server
                    )
            raise

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
        formatted_calls = [dict(method=call[0], params=call[1] if len(call) > 1 else {}) for call in calls]
        return self.call("ExecuteMultiCall", calls=formatted_calls)

    def get(self, type_name, **parameters):
        """Gets entities using the API. Shortcut for using call() with the 'Get' method.

        :param type_name: The type of entity.
        :type type_name: str
        :param parameters: Additional parameters to send.
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        :return: The results from the server.
        :rtype: list
        """
        if parameters:
            results_limit = parameters.get("resultsLimit", None)
            if results_limit is not None:
                del parameters["resultsLimit"]
            if "search" in parameters:
                parameters.update(parameters["search"])
                del parameters["search"]
            parameters = dict(search=parameters, resultsLimit=results_limit)
        return self.call("Get", type_name=type_name, **parameters)

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
        return self.call("Add", type_name=type_name, entity=entity)

    def set(self, type_name, entity):
        """Sets an entity using the API. Shortcut for using call() with the 'Set' method.

        :param type_name: The type of entity.
        :type type_name: str
        :param entity: The entity to set.
        :type entity: dict
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        """
        return self.call("Set", type_name=type_name, entity=entity)

    def remove(self, type_name, entity):
        """Removes an entity using the API. Shortcut for using call() with the 'Remove' method.

        :param type_name: The type of entity.
        :type type_name: str
        :param entity: The entity to remove.
        :type entity: dict
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        """
        return self.call("Remove", type_name=type_name, entity=entity)

    def authenticate(self):
        """Authenticates against the API server.

        :raise AuthenticationException: Raises if there was an issue with authenticating or logging in.
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        :return: A Credentials object with a session ID created by the server.
        :rtype: Credentials
        """
        auth_data = dict(
            database=self.credentials.database, userName=self.credentials.username, password=self.credentials.password
        )
        if self.credentials.session_id and not self.credentials.password:
            # Extend the session if only the session ID is present
            auth_data = dict(credentials=dict(auth_data, **{"sessionId": self.credentials.session_id}))

        try:
            result = _query(
                self._server,
                "Authenticate",
                auth_data,
                self.timeout,
                verify_ssl=self._is_verify_ssl,
                proxies=self._proxies,
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
            if exception.name == "InvalidUserException":
                raise AuthenticationException(
                    self.credentials.username, self.credentials.database, self.credentials.server
                )
            raise

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
        return "Credentials(username={username}, database={database})".format(
            username=self.username, database=self.database
        )

    def get_param(self):
        """A simple representation of the credentials object for passing into the API.authenticate() server call.

        :return: The simple credentials object for use by API.authenticate().
        :rtype: dict
        """
        return dict(userName=self.username, sessionId=self.session_id, database=self.database)


class GeotabHTTPAdapter(HTTPAdapter):
    """HTTP adapter to force use of TLS 1.2 for HTTPS connections."""

    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize, block=block, ssl_version=ssl.PROTOCOL_TLSv1_2, **pool_kwargs
        )


def _query(server, method, parameters, timeout=DEFAULT_TIMEOUT, verify_ssl=True, proxies=None):
    """Formats and performs the query against the API.

    :param server: The MyGeotab server.
    :type server: str
    :param method: The method name.
    :type method: str
    :param parameters: The parameters to send with the query.
    :type parameters: dict
    :param timeout: The timeout to make the call, in seconds. By default, this is 300 seconds (or 5 minutes).
    :type timeout: float
    :param verify_ssl: If True, verify the SSL certificate. It's recommended not to modify this.
    :type verify_ssl: bool
    :param proxies: The proxies dictionary to apply to the request.
    :type proxies: dict or None
    :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
    :raise TimeoutException: Raises when the request does not respond after some time.
    :raise urllib2.HTTPError: Raises when there is an HTTP status code that indicates failure.
    :return: The JSON-decoded result from the server.
    """
    api_endpoint = get_api_url(server)
    params = dict(id=-1, method=method, params=parameters or {})
    headers = get_headers()
    with requests.Session() as session:
        session.mount("https://", GeotabHTTPAdapter())
        try:
            response = session.post(
                api_endpoint,
                data=json_serialize(params),
                headers=headers,
                allow_redirects=True,
                timeout=timeout,
                verify=verify_ssl,
                proxies=proxies,
            )
        except Timeout:
            raise TimeoutException(server)
    response.raise_for_status()
    content_type = response.headers.get("Content-Type")
    if content_type and "application/json" not in content_type.lower():
        return response.text
    return _process(json_deserialize(response.text))


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
    :param proxies: The proxies dictionary to apply to the request.
    :type proxies: dict or None
    :param parameters: Additional parameters to send (for example, search=dict(id='b123') ).
    :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
    :raise TimeoutException: Raises when the request does not respond after some time.
    :return: The result from the server.
    """
    if method is None:
        raise Exception("A method name must be specified")
    if server is None:
        raise Exception("A server (eg. my3.geotab.com) must be specified")
    parameters = process_parameters(parameters)
    return _query(server, method, parameters, timeout=timeout, verify_ssl=verify_ssl, proxies=proxies)


def process_parameters(parameters):
    """Allows the use of Pythonic-style parameters with underscores instead of camel-case.

    :param parameters: The parameters object.
    :type parameters: dict
    :return: The processed parameters.
    :rtype: dict
    """
    if not parameters:
        return {}
    params = copy.copy(parameters)
    for param_name in parameters:
        value = parameters[param_name]
        server_param_name = re.sub(r"_(\w)", lambda m: m.group(1).upper(), param_name)
        if isinstance(value, dict):
            value = process_parameters(value)
        params[server_param_name] = value
        if server_param_name != param_name:
            del params[param_name]
    return params


def get_api_url(server):
    """Formats the server URL properly in order to query the API.

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


__all__ = ["API", "Credentials", "MyGeotabException", "AuthenticationException"]
