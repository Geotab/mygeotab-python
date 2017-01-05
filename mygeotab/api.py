# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import copy
import json
import re
import ssl
import warnings

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
from six.moves.urllib.parse import urlparse

from . import __title__, __version__
import mygeotab.serializers

try:
    requests.packages.urllib3.disable_warnings()
except:
    pass


class API(object):
    def __init__(self, username, password=None, database=None, session_id=None, server='my.geotab.com', verify=True):
        """
        Creates a new instance of this simple Pythonic wrapper for the MyGeotab API.

        :param username: The username used for MyGeotab servers. Usually an email address.
        :param password: The password associated with the username. Optional if `session_id` is provided.
        :param database: The database or company name. Optional as this usually gets resolved upon authentication.
        :param session_id: A session ID, assigned by the server.
        :param server: The server ie. my23.geotab.com. Optional as this usually gets resolved upon authentication.
        :param verify: If True, verify SSL certificate. It's recommended not to modify this.
        :raise Exception: Raises an Exception if a username, or one of the session_id or password is not provided.
        """
        if username is None:
            raise Exception('`username` cannot be None')
        if password is None and session_id is None:
            raise Exception('`password` and `session_id` must not both be None')
        self.credentials = Credentials(username, session_id, database, server, password)
        self.__verify_ssl = verify
        self.__reauthorize_count = 0

    @property
    def _server(self):
        if not self.credentials.server:
            self.credentials.server = 'my.geotab.com'
        return self.credentials.server

    @property
    def _is_verify_ssl(self):
        """
        Whether or not SSL be verified.

        :rtype: bool
        :return: True if the calls are being made locally
        """
        if not self.__verify_ssl:
            return False
        return not any(s in get_api_url(self._server) for s in ['127.0.0.1', 'localhost'])

    def call(self, method, **parameters):
        """
        Makes a call to the API.

        :param method: The method name.
        :param parameters: Additional parameters to send (for example, search=dict(id='b123') )
        :return: The JSON result (decoded into a dict) from the server
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        if method is None:
            raise Exception('A method name must be specified')
        params = process_parameters(parameters)
        if self.credentials and not self.credentials.session_id:
            self.authenticate()
        if 'credentials' not in params and self.credentials.session_id:
            params['credentials'] = self.credentials.get_param()

        try:
            result = _query(get_api_url(self._server), method, params, verify_ssl=self._is_verify_ssl)
            if result is not None:
                self.__reauthorize_count = 0
            return result
        except MyGeotabException as exception:
            if exception.name == 'InvalidUserException' and self.__reauthorize_count == 0:
                self.__reauthorize_count += 1
                self.authenticate()
                return self.call(method, **parameters)
            raise

    def multi_call(self, calls):
        """
        Performs a multi-call to the API

        :param calls: A list of call 2-tuples with method name and params (for example, ('Get', dict(typeName='Trip')) )
        :return: The JSON result (decoded into a dict) from the server
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        formatted_calls = [dict(method=call[0], params=call[1] if len(call) > 1 else {}) for call in calls]
        return self.call('ExecuteMultiCall', calls=formatted_calls)

    def get(self, type_name, **parameters):
        """
        Gets entities using the API. Shortcut for using call() with the 'Get' method.

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
        return self.call('Get', type_name=type_name, **parameters)

    def search(self, type_name, **parameters):
        """
        Searches for entities using the API. Shortcut for using get() with a search.

        :param type_name: The type of entity
        :param parameters: Additional parameters to send.
        :return: The JSON result (decoded into a dict) from the server
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        warnings.simplefilter('always', DeprecationWarning)  # turn off filter
        warnings.warn("'search()' is deprecated. Use 'get()' instead", DeprecationWarning, stacklevel=2)
        warnings.simplefilter('default', DeprecationWarning)  # turn off filter
        return self.get(type_name=type_name, **parameters)

    def add(self, type_name, entity):
        """
        Adds an entity using the API. Shortcut for using call() with the 'Add' method.

        :param type_name: The type of entity
        :param entity: The entity to add
        :return: The id of the object added
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        return self.call('Add', type_name=type_name, entity=entity)

    def set(self, type_name, entity):
        """
        Sets an entity using the API. Shortcut for using call() with the 'Set' method.

        :param type_name: The type of entity
        :param entity: The entity to set
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        return self.call('Set', type_name=type_name, entity=entity)

    def remove(self, type_name, entity):
        """
        Removes an entity using the API. Shortcut for using call() with the 'Remove' method.

        :param type_name: The type of entity
        :param entity: The entity to remove
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        return self.call('Remove', type_name=type_name, entity=entity)

    def authenticate(self, is_global=True):
        """
        Authenticates against the API server.

        :param is_global: If True, authenticate globally. Local login if False.
        :return: A Credentials object with a session ID created by the server
        :raise AuthenticationException: Raises if there was an issue with authenticating or logging in
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        auth_data = dict(database=self.credentials.database, userName=self.credentials.username,
                         password=self.credentials.password)
        auth_data['global'] = is_global
        try:
            result = _query(get_api_url(self._server), 'Authenticate', auth_data, verify_ssl=self._is_verify_ssl)
            if result:
                new_server = result['path']
                server = self.credentials.server
                if new_server != 'ThisServer':
                    server = new_server
                c = result['credentials']
                self.credentials = Credentials(c['userName'], c['sessionId'], c['database'],
                                               server)
                return self.credentials
        except MyGeotabException as exception:
            if exception.name == 'InvalidUserException':
                raise AuthenticationException(self.credentials.username,
                                              self.credentials.database,
                                              self.credentials.server)
            raise


class Credentials(object):
    def __init__(self, username, session_id, database, server, password=None):
        """
        Creates a new instance of a MyGeotab credentials object

        :param username: The username used for MyGeotab servers. Usually an email address.
        :param session_id: A session ID, assigned by the server.
        :param database: The database or company name. Optional as this usually gets resolved upon authentication.
        :param server: The server ie. my23.geotab.com. Optional as this usually gets resolved upon authentication.
        :param password: The password associated with the username. Optional if `session_id` is provided.
        """
        self.username = username
        self.session_id = session_id
        self.database = database
        self.server = server
        self.password = password

    def __str__(self):
        return '{0} @ {1}/{2}'.format(self.username, self.server, self.database)

    def get_param(self):
        """
        A simple representation of the credentials object for passing into the API.authenticate() server call

        :return: The simple credentials object for use by API.authenticate()
        """
        return dict(userName=self.username, sessionId=self.session_id, database=self.database)


class MyGeotabException(Exception):
    def __init__(self, full_error):
        """
        Creates a Pythonic exception for server-side exceptions

        :param full_error: The full JSON-decoded error
        """
        self._full_error = full_error
        main_error = full_error['errors'][0]
        self.name = main_error['name']
        self.message = main_error['message']
        self.stack_trace = main_error.get('stackTrace')

    def __str__(self):
        error_str = '{0}\n{1}'.format(self.name, self.message)
        if self.stack_trace:
            error_str += '\n\nStacktrace:\n{0}'.format(self.stack_trace)
        return error_str


class AuthenticationException(Exception):
    def __init__(self, username, database, server):
        """
        An exception raised on an unsuccessful authentication with the server

        :param username: The username used for MyGeotab servers. Usually an email address.
        :param database: The database or company name.
        :param server: The server ie. my23.geotab.com.
        """
        self.username = username
        self.database = database
        self.server = server

    def __str__(self):
        return 'Cannot authenticate \'{0} @ {1}/{2}\''.format(self.username, self.server,
                                                              self.database)


class GeotabHTTPAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_TLSv1_2,
                                       **pool_kwargs)


def _query(api_endpoint, method, parameters, verify_ssl=True):
    """
    Formats and performs the query against the API

    :param api_endpoint: The API endpoint to query
    :param method: The method name
    :param parameters: A dict of parameters to send
    :param verify_ssl: Whether or not to verify SSL connections
    :return: The JSON-decoded result from the server
    :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
    """
    params = dict(id=-1, method=method, params=parameters or {})
    headers = {
        'Content-type': 'application/json; charset=UTF-8',
        'User-Agent': '{title}/{version}'.format(title=__title__, version=__version__)
    }
    with requests.Session() as s:
        s.mount('https://', GeotabHTTPAdapter())
        r = s.post(api_endpoint,
                   data=json.dumps(params,
                                   default=mygeotab.serializers.object_serializer),
                   headers=headers, allow_redirects=True, verify=verify_ssl)
    return _process(r.json(object_hook=mygeotab.serializers.object_deserializer))


def _process(data):
    """
    Processes the returned JSON from the server.

    :param data: The JSON data in dict form
    :return: The result dict
    :raise MyGeotabException: Raises when a server exception was encountered
    """
    if data:
        if 'error' in data:
            raise MyGeotabException(data['error'])
        if 'result' in data:
            return data['result']
    return data


def from_credentials(credentials):
    """
    Returns a new API object from an existing Credentials object

    :param credentials: The existing saved credentials
    :return: A new API object populated with MyGeotab credentials
    """
    return API(username=credentials.username, password=credentials.password,
               database=credentials.database, session_id=credentials.session_id,
               server=credentials.server)


def server_call(method, server, **parameters):
    """
    Makes a call to an un-authenticated method on a server

    :param method: The method name
    :param server: The MyGeotab server
    :param parameters: Additional parameters to send (for example, search=dict(id='b123') )
    :return: The JSON result (decoded into a dict) from the server
    :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
    """
    if method is None:
        raise Exception("A method name must be specified")
    if server is None:
        raise Exception("A server (eg. my3.geotab.com) must be specified")
    parameters = process_parameters(parameters)
    return _query(get_api_url(server), method, parameters, True)


def process_parameters(parameters):
    """
    Allows the use of Pythonic-style parameters with underscores instead of camel-case

    :param parameters: The parameters object dict
    :return: The processed parameters
    """
    if not parameters:
        return {}
    params = copy.copy(parameters)
    for param_name in parameters:
        value = parameters[param_name]
        server_param_name = re.sub(r'_(\w)', lambda m: m.group(1).upper(), param_name)
        if isinstance(value, dict):
            value = process_parameters(value)
        params[server_param_name] = value
        if server_param_name != param_name:
            del params[param_name]
    return params


def get_api_url(server):
    """
    Formats the server URL properly in order to query the API.

    :rtype: str
    :return: A valid MyGeotab API request URL
    """
    parsed = urlparse(server)
    base_url = parsed.netloc if parsed.netloc else parsed.path
    base_url.replace('/', '')
    return 'https://' + base_url + '/apiv1'

__all__ = ['API', 'Credentials', 'MyGeotabException', 'AuthenticationException']
