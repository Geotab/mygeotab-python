# -*- coding: utf-8 -*-

from __future__ import unicode_literals

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
import json

import requests


class API(object):
    _reauthorize_count = 0

    def __init__(self, username=None, password=None, database=None, server='my.geotab.com', credentials=None):
        """
        Creates a new instance of this simple Pythonic wrapper for the MyGeotab API.

        :param username: The username used for MyGeotab servers. Usually an email address.
        :param password: The password associated with the username. Optional if `session_id` is provided.
        :param database: The database or company name. Optional as this usually gets resolved upon authentication.
        :param server: The server ie. my23.geotab.com. Optional as this usually gets resolved upon authentication.
        :param credentials: Create the API from an existing Credential object.
        :raise Exception: Raises an Exception if a username, or one of the session_id or password is not provided.
        """
        if credentials:
            self.credentials = credentials
        else:
            if username is None:
                raise Exception('`username` cannot be None')
            if password is None and session_id is None:
                raise Exception('`password` and `session_id` must not both be None')
            self.credentials = Credentials(username, None, database, server, password)

    def _get_api_url(self):
        """
        Formats the server URL properly in order to query the API.

        :rtype: str
        :return: A valid MyGeotab API request URL
        """
        if not self.credentials.server:
            self.credentials.server = 'my.geotab.com'
        parsed = urlparse(self.credentials.server)
        base_url = parsed.netloc if parsed.netloc else parsed.path
        base_url.replace('/', '')
        return 'https://' + base_url + '/apiv1'

    def _query(self, method, parameters):
        """
        Formats and performs the query against the API

        :param method: The method name.
        :param parameters: A dict of parameters to send
        :return: The JSON-decoded result from the server
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        params = dict(id=-1, method=method, params=parameters)
        headers = {'Content-type': 'application/json; charset=UTF-8'}
        r = requests.post(self._get_api_url(), data=json.dumps(params), headers=headers, allow_redirects=True)
        data = r.json()
        if data:
            if 'error' in data:
                raise MyGeotabException(data['error'])
            if 'result' in data:
                return data['result']
            return data
        return None

    def call(self, method, type_name=None, **parameters):
        """
        Makes a call to the API.

        :param method: The method name.
        :param type_name: The type of data returned for generic methods (for example, 'Get')
        :param parameters: Additional parameters to send.
        :return: The JSON-decoded result from the server
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        if method is None:
            raise Exception("Must specify a method name")
        if parameters is None:
            parameters = {}
        if type_name:
            parameters['typeName'] = type_name
        if self.credentials is None:
            self.authenticate()
        if not 'credentials' in parameters and self.credentials.session_id:
            parameters['credentials'] = self.credentials.get_param()

        try:
            result = self._query(method, parameters)
            if result is not None:
                self._reauthorize_count = 0
                return result
        except MyGeotabException as exception:
            if exception.name == 'InvalidUserException' and self._reauthorize_count == 0:
                self._reauthorize_count += 1
                self.authenticate()
                return self.call(method, parameters)
            raise
        return None

    def authenticate(self):
        """
        Authenticates against the API server.

        :return: A Credentials object with a session ID created by the server
        :raise AuthenticationException: Raises if there was an issue with authenticating or logging in
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        auth_data = dict(database=self.credentials.database, userName=self.credentials.username,
                         password=self.credentials.password)
        auth_data['global'] = True
        try:
            result = self._query('Authenticate', auth_data)
            if result:
                new_server = result['path']
                server = self.credentials.server
                if new_server != 'ThisServer':
                    server = new_server
                c = result['credentials']
                self.credentials = Credentials(c['userName'], c['sessionId'], c['database'], server)
                return self.credentials
        except MyGeotabException as exception:
            if exception.name == 'InvalidUserException':
                raise AuthenticationException(self.credentials.username, self.credentials.database,
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
        self.stack_trace = main_error['stackTrace']
        print(self.stack_trace)

    def __str__(self):
        return '{0}\n{1}\n\nStack:\n{2}'.format(self.name, self.message, self.stack_trace)


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
        return 'Cannot authenticate \'{0} @ {1}/{2}\''.format(self.username, self.server, self.database)