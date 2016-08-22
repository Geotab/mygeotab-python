import sys
import unittest
if sys.version_info < (3, 5):
    raise unittest.SkipTest('Python 3.5+ is required to run the async API tests.')
import os
import asyncio

from mygeotab.ext.async import API, get_all


class TestAsyncCallApi(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)
        self.username = os.environ.get('MYGEOTAB_USERNAME')
        password = os.environ.get('MYGEOTAB_PASSWORD')
        self.database = os.environ.get('MYGEOTAB_DATABASE')
        if self.username and password:
            self.api = API(self.username, password=password, database=self.database, loop=self.loop)
            self.api.authenticate()
            del password
        else:
            self.skipTest(
                'Can\'t make calls to the API without the MYGEOTAB_USERNAME and MYGEOTAB_PASSWORD environment '
                'variables being set')

    def test_get_version(self):
        version = get_all([self.api.call_async('GetVersion')], loop=self.loop)
        self.assertEqual(len(version), 1)
        version_split = version[0].split('.')
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

    def test_pythonic_parameters(self):
        users = self.api.get('User')
        count_users = self.api.call('GetCountOf', type_name='User')
        self.assertGreaterEqual(count_users, 1)
        self.assertEqual(count_users, len(users))


if __name__ == '__main__':
    unittest.main()