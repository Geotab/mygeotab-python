# -*- coding: utf-8 -*-

from __future__ import unicode_literals

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
import json

import requests


class API(object):
    credentials = None
    _reauthorize_count = 0

    def __init__(self, username, password=None, database=None, session_id=None, server='my.geotab.com'):
        if username is None:
            raise Exception('`username` cannot be None')
        if password is None and session_id is None:
            raise Exception('`password` and `session_id` must not both be None')
        self.username = username
        self.password = password
        self.database = database
        self.session_id = session_id
        self.server = server

    @staticmethod
    def load(credentials):
        api = API(username=credentials.username, session_id=credentials.session_id, database=credentials.database,
                  server=credentials.server)
        api.credentials = credentials
        return api

    def _get_server(self):
        if not self.server:
            self.server = 'my.geotab.com'
        parsed = urlparse(self.server)
        base_url = parsed.netloc if parsed.netloc else parsed.path
        base_url.replace('/', '')
        return 'https://' + base_url + '/apiv1'

    def _call_base(self, method, parameters):
        params = dict(id=-1, method=method, params=parameters)
        headers = {'Content-type': 'application/json; charset=UTF-8'}
        r = requests.post(self._get_server(), data=json.dumps(params), headers=headers, allow_redirects=True)
        data = r.json()
        if data:
            if 'error' in data:
                raise MyGeotabException(data['error'])
            if 'result' in data:
                return data['result']
            return data
        return None

    def call(self, method, type_name=None, **parameters):
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
            result = self._call_base(method, parameters)
            if result is not None:
                self._reauthorize_count = 0
                return result
        except MyGeotabException as exception:
            if exception.name == 'InvalidUserException':
                self._reauthorize_count += 1
                self.authenticate()
                return self.call(method, parameters)
            raise exception
        return None

    def authenticate(self):
        auth_data = dict(database=self.database, userName=self.username, password=self.password)
        auth_data['global'] = True
        try:
            result = self._call_base('Authenticate', auth_data)
            if result:
                server = result['path']
                if server != 'ThisServer':
                    self.server = server
                c = result['credentials']
                self.credentials = Credentials(c['userName'], c['sessionId'], c['database'], self.server)
                self.password = None
                return self.credentials
        except MyGeotabException as exception:
            if exception.name == 'InvalidUserException':
                database_name = self.credentials.database if self.credentials else self.database
                server_name = self.credentials.server if self.credentials else self.server
                raise AuthenticationException(self.username, database_name, server_name)
            raise exception


class Credentials(object):
    def __init__(self, username, session_id, database, server, password=None):
        self.username = username
        self.session_id = session_id
        self.database = database
        self.server = server
        self.password = password

    def __str__(self):
        return '{0} @ {1}/{2}'.format(self.username, self.server, self.database)

    def get_param(self):
        return dict(userName=self.username, sessionId=self.session_id, database=self.database)


class MyGeotabException(Exception):
    def __init__(self, full_error):
        self._full_error = full_error
        main_error = full_error['errors'][0]
        self.name = main_error['name']
        self.message = main_error['message']
        self.stack_trace = main_error['stackTrace']

    def __str__(self):
        return '{0}\n\t{1}\n\nStack:\n\t{2}'.format(self.name, self.message, self.stack_trace)


class AuthenticationException(Exception):
    def __init__(self, username, database, server):
        self.username = username
        self.database = database
        self.server = server

    def __str__(self):
        return 'Cannot authenticate \'{0} @ {1}/{2}\''.format(self.username, self.server, self.database)