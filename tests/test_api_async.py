# -*- coding: utf-8 -*-

import sys
import unittest
if sys.version_info < (3, 5):
    raise unittest.SkipTest('Python 3.5+ is required to run the async API tests.')
import asyncio
import os
import warnings

from mygeotab import AuthenticationException, MyGeotabException
from mygeotab.ext.async import API, run, from_credentials, server_call


class TestAsyncCallApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.get_event_loop() or asyncio.new_event_loop()
        cls.username = os.environ.get('MYGEOTAB_USERNAME')
        cls.password = os.environ.get('MYGEOTAB_PASSWORD')
        cls.database = os.environ.get('MYGEOTAB_DATABASE')
        cls.trailer_name = 'myg-python-test'
        if cls.username and cls.password:
            cls.api = API(cls.username, password=cls.password, database=cls.database, loop=cls.loop, verify=True)
            cls.api.authenticate()
            try:
                cls.tearDownClass()
            except:
                pass
        else:
            raise unittest.SkipTest(
                'Can\'t make calls to the API without the MYGEOTAB_USERNAME and MYGEOTAB_PASSWORD environment '
                'variables being set')

    @classmethod
    def tearDownClass(cls):
        try:
            trailers = cls.api.get('Trailer', name=cls.trailer_name)
            for trailer in trailers:
                cls.api.remove('Trailer', trailer)
        except:
            pass

    def test_get_version(self):
        version = run(self.api.call_async('GetVersion'), loop=self.loop)
        self.assertEqual(len(version), 1)
        version_split = version[0].split('.')
        self.assertEqual(len(version_split), 4)

    def test_get_user(self):
        user = run(self.api.get_async('User', name='{0}'.format(self.username)), loop=self.loop)
        self.assertEqual(len(user), 1)
        self.assertEqual(len(user[0]), 1)
        user = user[0][0]
        self.assertEqual(user['name'], self.username)

    def test_get_user_search(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            user = run(self.api.search_async('User', name='{0}'.format(self.username)), loop=self.loop)
        self.assertEqual(len(w), 1)
        self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
        self.assertTrue('search_async()' in str(w[-1].message))
        self.assertEqual(len(user), 1)
        self.assertEqual(len(user[0]), 1)
        user = user[0][0]
        self.assertEqual(user['name'], self.username)

    def test_multi_call(self):
        calls = [
            ['Get', dict(typeName='User', search=dict(name='{0}'.format(self.username)))],
            ['GetVersion']
        ]
        results = run(self.api.multi_call_async(calls), loop=self.loop)
        self.assertEqual(len(results), 1)
        results = results[0]
        self.assertEqual(len(results), 2)
        self.assertIsNotNone(results[0])
        self.assertEqual(len(results[0]), 1)
        self.assertIsNotNone(results[0][0]['name'], self.username)
        self.assertIsNotNone(results[1])
        version_split = results[1].split('.')
        self.assertEqual(len(version_split), 4)

    def test_pythonic_parameters(self):
        users = self.api.get('User')
        count_users = run(self.api.call_async('Get', type_name='User'), loop=self.loop)
        self.assertEqual(len(count_users), 1)
        self.assertGreaterEqual(len(count_users[0]), 1)
        self.assertEqual(len(count_users[0]), len(users))

    def test_api_from_credentials(self):
        new_api = from_credentials(self.api.credentials, loop=self.loop)
        users = run(new_api.get_async('User'), loop=self.loop)
        self.assertGreaterEqual(len(users), 1)

    def test_results_limit(self):
        users = run(self.api.get_async('User', resultsLimit=1), loop=self.loop)
        self.assertEqual(len(users), 1)

    def test_session_expired(self):
        credentials = self.api.credentials
        credentials.password = self.password
        credentials.session_id = 'abc123'
        test_api = from_credentials(credentials, loop=self.loop)
        users = run(test_api.get_async('User'), loop=self.loop)
        self.assertGreaterEqual(len(users), 1)

    def test_missing_method(self):
        with self.assertRaises(Exception):
            run(self.api.call_async(None), loop=self.loop)

    def test_call_without_credentials(self):
        new_api = API(self.username, password=self.password, database=self.database, server=None, loop=self.loop)
        user = run(new_api.get_async('User', name='{0}'.format(self.username)), loop=self.loop)
        self.assertEqual(len(user), 1)
        self.assertEqual(len(user[0]), 1)

    def test_bad_parameters(self):
        with self.assertRaises(MyGeotabException) as cm:
            run(self.api.call_async('NonExistentMethod', not_a_property='abc123'), loop=self.loop)
        self.assertTrue('NonExistentMethod' in str(cm.exception))

    def test_add_edit_remove(self):
        def get_trailer():
            trailers = run(self.api.get_async('Trailer', name=self.trailer_name), loop=self.loop)
            self.assertEqual(len(trailers), 1)
            self.assertEqual(len(trailers[0]), 1)
            return trailers[0][0]
        user = self.api.get('User', name=self.username)[0]
        trailer = {
            'name': self.trailer_name,
            'groups': user['companyGroups']
        }
        trailer_id = run(self.api.add_async('Trailer', trailer), loop=self.loop)
        self.assertEqual(len(trailer_id), 1)
        trailer['id'] = trailer_id[0]
        trailer = get_trailer()
        self.assertEqual(trailer['name'], self.trailer_name)
        comment = 'some comment'
        trailer['comment'] = comment
        run(self.api.set_async('Trailer', trailer), loop=self.loop)
        trailer = get_trailer()
        self.assertEqual(trailer['comment'], comment)
        run(self.api.remove_async('Trailer', trailer), loop=self.loop)
        trailers = run(self.api.get_async('Trailer', name=self.trailer_name), loop=self.loop)
        self.assertEqual(len(trailers), 1)
        self.assertEqual(len(trailers[0]), 0)


class TestAsyncAuthentication(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.get_event_loop() or asyncio.new_event_loop()
        self.username = 'fakeemail@example.com'
        self.database = os.environ.get('MYGEOTAB_DATABASE')
        if not self.database:
            self.skipTest(
                'Can\'t make calls to the API without the MYGEOTAB_DATABASE environment '
                'variable being set')

    def test_invalid_session(self):
        test_api = API(self.username, session_id='abc123', database=self.database)
        self.assertTrue(self.username in str(test_api.credentials))
        self.assertTrue(self.database in str(test_api.credentials))
        with self.assertRaises(AuthenticationException) as cm:
            run(test_api.get('User'), loop=self.loop)
        self.assertTrue('Cannot authenticate' in str(cm.exception))
        self.assertTrue(self.database in str(cm.exception))
        self.assertTrue(self.username in str(cm.exception))


class TestAsyncServerCallApi(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.get_event_loop()

    def test_get_version(self):
        results = run(server_call('GetVersion', server='my.geotab.com', loop=self.loop, verify=False), loop=self.loop)
        version_split = results[0].split('.')
        self.assertEqual(len(version_split), 4)

    def test_invalid_server_call(self):
        with self.assertRaises(Exception) as cm1:
            run(server_call(None, None, loop=self.loop), loop=self.loop)
        with self.assertRaises(Exception) as cm2:
            run(server_call('GetVersion', None, loop=self.loop), loop=self.loop)
        self.assertTrue('method' in str(cm1.exception))
        self.assertTrue('server' in str(cm2.exception))


if __name__ == '__main__':
    unittest.main()
