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
            self.api._process(exception_response)
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
        result = self.api._process(results_response)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'test@example.com')
        self.assertEqual(result[0]['id'], 'b123')


class TestCallApi(unittest.TestCase):
    def setUp(self):
        self.username = os.environ.get('MYGEOTAB_USERNAME')
        password = os.environ.get('MYGEOTAB_PASSWORD')
        self.database = os.environ.get('MYGEOTAB_DATABASE')
        if self.username and password:
            self.api = api.API(self.username, password=password, database=self.database)
            self.api.authenticate()
            del password
        else:
            self.skipTest(
                'Can\'t make calls to the API without the MYGEOTAB_USERNAME and MYGEOTAB_PASSWORD environment '
                'variables being set')

    def test_get_version(self):
        version = self.api.call('GetVersion')
        version_split = version.split('.')
        self.assertEqual(len(version_split), 4)

    def test_get_user(self):
        user = self.api.search('User', name='{0}'.format(self.username))
        self.assertEqual(len(user), 1)
        user = user[0]
        self.assertEqual(user['name'], self.username)

    def test_pythonic_parameters(self):
        users = self.api.get('User')
        count_users = self.api.call('GetCountOf', type_name='User')
        self.assertGreaterEqual(count_users, 1)
        self.assertEqual(count_users, len(users))


class TestServerCallApi(unittest.TestCase):
    def test_get_version(self):
        version = api.API.server_call('GetVersion', server='my3.geotab.com')
        version_split = version.split('.')
        self.assertEqual(len(version_split), 4)

if __name__ == '__main__':
    unittest.main()
