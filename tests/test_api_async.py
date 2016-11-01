import sys
import unittest
if sys.version_info < (3, 5):
    raise unittest.SkipTest('Python 3.5+ is required to run the async API tests.')
import os
import asyncio

from mygeotab.ext.async import API, run


class TestAsyncCallApi(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)
        self.username = os.environ.get('MYGEOTAB_USERNAME')
        password = os.environ.get('MYGEOTAB_PASSWORD')
        self.database = os.environ.get('MYGEOTAB_DATABASE')
        if self.username and password:
            self.api = API(self.username, password=password, database=self.database, loop=self.loop, verify=False)
            self.api.authenticate()
            del password
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

    def test_pythonic_parameters(self):
        users = self.api.get('User')
        count_users = run(self.api.call_async('Get', type_name='User'), loop=self.loop)
        self.assertEqual(len(count_users), 1)
        self.assertGreaterEqual(len(count_users[0]), 1)
        self.assertEqual(len(count_users[0]), len(users))


if __name__ == '__main__':
    unittest.main()