# -*- coding: utf-8 -*-

import sys
import unittest
if sys.version_info < (3, 5):
    raise unittest.SkipTest('Python 3.5+ is required to run the async API tests.')
import os
import asyncio

from mygeotab.ext.async import API, run, from_credentials, server_call


class TestAsyncCallApi(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)
        self.username = os.environ.get('MYGEOTAB_USERNAME')
        self.password = os.environ.get('MYGEOTAB_PASSWORD')
        self.database = os.environ.get('MYGEOTAB_DATABASE')
        if self.username and self.password:
            self.api = API(self.username, password=self.password, database=self.database, loop=self.loop)
            self.api.authenticate()
        else:
            self.skipTest(
                'Can\'t make calls to the API without the MYGEOTAB_USERNAME and MYGEOTAB_PASSWORD environment '
                'variables being set')

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
        user = run(self.api.search_async('User', name='{0}'.format(self.username)), loop=self.loop)
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


class TestAsyncServerCallApi(unittest.TestCase):
    def test_get_version(self):
        version = run(server_call('GetVersion', server='my3.geotab.com'))
        version_split = version.split('.')
        self.assertEqual(len(version_split), 4)

    def test_invalid_server_call(self):
        with self.assertRaises(Exception) as cm1:
            run(server_call(None, None))
        with self.assertRaises(Exception) as cm2:
            run(server_call('GetVersion', None))
        self.assertTrue('method' in str(cm1.exception))
        self.assertTrue('server' in str(cm2.exception))


if __name__ == '__main__':
    unittest.main()
