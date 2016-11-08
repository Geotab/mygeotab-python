# -*- coding: utf-8 -*-

import unittest
import os

from mygeotab import api


class TestAttributes(unittest.TestCase):
    def test_should_verify_ssl(self):
        my_api = api.API('test@example.com', session_id=123, server='my3.geotab.com')
        self.assertTrue(my_api._is_verify_ssl)
        my_api = api.API('test@example.com', session_id=123, server='127.0.0.1')
        self.assertFalse(my_api._is_verify_ssl)
        my_api = api.API('test@example.com', session_id=123, server='localhost')
        self.assertFalse(my_api._is_verify_ssl)
        my_api = api.API('test@example.com', session_id=123, server='my3.geotab.com', verify=False)
        self.assertFalse(my_api._is_verify_ssl)


class TestProcessParameters(unittest.TestCase):
    def setUp(self):
        self.api = api.API('test@example.com', session_id=123)

    def test_camel_case_transformer(self):
        params = dict(search=dict(device_search=dict(id=123),
                                  include_overlapped_trips=True))
        fixed_params = api.process_parameters(params)
        self.assertIsNotNone(fixed_params)
        self.assertTrue('search' in fixed_params)
        self.assertTrue('deviceSearch' in fixed_params['search'])
        self.assertTrue('id' in fixed_params['search']['deviceSearch'])
        self.assertEqual(123, fixed_params['search']['deviceSearch']['id'])
        self.assertTrue('includeOverlappedTrips' in fixed_params['search'])
        self.assertEqual(True, fixed_params['search']['includeOverlappedTrips'])


class TestProcessResults(unittest.TestCase):
    def setUp(self):
        self.api = api.API('test@example.com', session_id=123)

    def test_handle_server_exception(self):
        exception_response = dict(error=dict(errors=[dict(
            message=(
            u'The method "Get" could not be found. Verify the method name and ensure all method parameters are '
                    u'included. Request Json: {"params": {"typeName": "Passwords", "credentials": {"userName": '
                    u'"test@example.com", "sessionId": "12345678901234567890", "database": "my_company"}}, "method": '
            u'"Get", "id": -1}'),
            name=u'MissingMethodException',
            stackTrace=(u'   at Geotab.Checkmate.Web.APIV1.ProcessRequest(IHttpRequest httpRequest, HttpResponse '
                       u'httpResponse, String methodName, Dictionary`2 parameters, Action`2 parametersJSONToTokens, '
                       u'Action`1 handleException, IProfiler profile, Credentials credentials, Int32 requestIndex, '
                       u'Object requestJsonOrHashMap, Boolean& isAsync) in '
                       u'c:\\ProgramData\\GEOTAB\\Checkmate\\BuildServer\\master\\WorkingDirectory\\Checkmate\\CheckmateServer\\Geotab\\Checkmate\\Web\\APIV1.cs:line 813\r\n   '
                       u'at Geotab.Checkmate.Web.APIV1.<>c__DisplayClass13.<ProcessRequest>b__b() '
                       u'in c:\\ProgramData\\GEOTAB\\Checkmate\\BuildServer\\master\\WorkingDirectory\\Checkmate\\CheckmateServer\\Geotab\\Checkmate\\Web\\APIV1.cs:line 558\r\n   '
                       u'at Geotab.Checkmate.Web.APIV1.ExecuteHandleException(Action action) in '
                        u'c:\\ProgramData\\GEOTAB\\Checkmate\\BuildServer\\master\\WorkingDirectory\\Checkmate\\CheckmateServer\\Geotab\\Checkmate\\Web\\APIV1.cs:line 632'))],
            message=(
            u'The method "Get" could not be found. Verify the method name and ensure all method parameters are '
                    u'included. Request Json: {"params": {"typeName": "Passwords", "credentials": {"userName": '
                    u'"test@example.com", "sessionId": "12345678901234567890", "database": "my_company"}}, "method": '
            u'"Get", "id": -1}'),
            name=u'JSONRPCError'), requestIndex=0)
        with self.assertRaises(api.MyGeotabException) as cm:
            api._process(exception_response)
        ex = cm.exception
        self.assertEqual(ex.name, 'MissingMethodException')
        self.assertEqual(ex.message,
                         'The method "Get" could not be found. Verify the method name and ensure all method '
                         'parameters are included. Request Json: {"params": {"typeName": "Passwords", '
                         '"credentials": {"userName": "test@example.com", "sessionId": "12345678901234567890", '
                         '"database": "my_company"}}, "method": "Get", "id": -1}')

    def test_handle_server_results(self):
        results_response = {'result': [
            dict(
                id='b123',
                name='test@example.com'
            )
        ]}
        result = api._process(results_response)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'test@example.com')
        self.assertEqual(result[0]['id'], 'b123')

    def test_handle_none(self):
        result = api._process(None)
        self.assertIsNone(result)


class TestCallApi(unittest.TestCase):
    def setUp(self):
        self.username = os.environ.get('MYGEOTAB_USERNAME')
        self.password = os.environ.get('MYGEOTAB_PASSWORD')
        self.database = os.environ.get('MYGEOTAB_DATABASE')
        if self.username and self.password:
            self.api = api.API(self.username, password=self.password, database=self.database, server=None)
            self.api.authenticate()
        else:
            self.skipTest(
                'Can\'t make calls to the API without the MYGEOTAB_USERNAME and MYGEOTAB_PASSWORD environment '
                'variables being set')

    def test_get_version(self):
        version = self.api.call('GetVersion')
        version_split = version.split('.')
        self.assertEqual(len(version_split), 4)

    def test_get_user(self):
        user = self.api.get('User', name='{0}'.format(self.username))
        self.assertEqual(len(user), 1)
        user = user[0]
        self.assertEqual(user['name'], self.username)

    def test_get_user_search(self):
        user = self.api.search('User', name='{0}'.format(self.username))
        self.assertEqual(len(user), 1)
        user = user[0]
        self.assertEqual(user['name'], self.username)

    def test_multi_call(self):
        calls = [
            ['Get', dict(typeName='User', search=dict(name='{0}'.format(self.username)))],
            ['GetVersion']
        ]
        results = self.api.multi_call(calls)
        self.assertEqual(len(results), 2)
        self.assertIsNotNone(results[0])
        self.assertEqual(len(results[0]), 1)
        self.assertIsNotNone(results[0][0]['name'], self.username)
        self.assertIsNotNone(results[1])
        version_split = results[1].split('.')
        self.assertEqual(len(version_split), 4)

    def test_pythonic_parameters(self):
        users = self.api.get('User')
        count_users = self.api.call('Get', type_name='User')
        self.assertGreaterEqual(len(count_users), 1)
        self.assertEqual(len(count_users), len(users))

    def test_api_from_credentials(self):
        new_api = api.from_credentials(self.api.credentials)
        users = new_api.get('User')
        self.assertGreaterEqual(len(users), 1)

    def test_results_limit(self):
        users = self.api.get('User', resultsLimit=1)
        self.assertEqual(len(users), 1)

    def test_session_expired(self):
        credentials = self.api.credentials
        credentials.password = self.password
        credentials.session_id = 'abc123'
        test_api = api.from_credentials(credentials)
        users = test_api.get('User')
        self.assertGreaterEqual(len(users), 1)


class TestAuthentication(unittest.TestCase):
    def setUp(self):
        self.username = os.environ.get('MYGEOTAB_USERNAME')
        self.database = os.environ.get('MYGEOTAB_DATABASE')
        if not self.username:
            self.skipTest(
                'Can\'t make calls to the API without the MYGEOTAB_USERNAME and MYGEOTAB_PASSWORD environment '
                'variables being set')

    def test_invalid_session(self):
        test_api = api.API(self.username, session_id='abc123', database=self.database)
        with self.assertRaises(api.AuthenticationException):
            test_api.get('User')

    def test_auth_exception(self):
        test_api = api.API(self.username, password='abc123', database='this_database_does_not_exist')
        with self.assertRaises(api.MyGeotabException) as cm:
            test_api.authenticate(False)
        self.assertEqual(cm.exception.name, 'DbUnavailableException')

    def test_username_password_exists(self):
        with self.assertRaises(Exception) as cm1:
            api.API(None)
        with self.assertRaises(Exception) as cm2:
            api.API(self.username)
        self.assertTrue('username' in str(cm1.exception))
        self.assertTrue('password' in str(cm2.exception))


class TestServerCallApi(unittest.TestCase):
    def test_get_version(self):
        version = api.server_call('GetVersion', server='my3.geotab.com')
        version_split = version.split('.')
        self.assertEqual(len(version_split), 4)

    def test_invalid_server_call(self):
        with self.assertRaises(Exception) as cm1:
            api.server_call(None, None)
        with self.assertRaises(Exception) as cm2:
            api.server_call('GetVersion', None)
        self.assertTrue('method' in str(cm1.exception))
        self.assertTrue('server' in str(cm2.exception))

if __name__ == '__main__':
    unittest.main()
