# -*- coding: utf-8 -*-

import pytest
asyncio = pytest.importorskip("asyncio")
import os
import warnings

from mygeotab import AuthenticationException, MyGeotabException
from mygeotab.ext.async import API, run, from_credentials, server_call
from tests.test_api import populated_api, USERNAME, PASSWORD, DATABASE, TRAILER_NAME

USERNAME = os.environ.get('MYGEOTAB_USERNAME_ASYNC', USERNAME)
PASSWORD = os.environ.get('MYGEOTAB_PASSWORD_ASYNC', PASSWORD)


@pytest.fixture(scope='session')
def async_populated_api():
    loop = asyncio.get_event_loop() or asyncio.new_event_loop()
    if USERNAME and PASSWORD:
        session = API(USERNAME, password=PASSWORD, database=DATABASE, server=None, loop=loop)
        try:
            session.authenticate()
        except MyGeotabException as exception:
            pytest.fail(exception)
            return
        yield session
    else:
        pytest.skip('Can\'t make calls to the API without the '
                    'MYGEOTAB_USERNAME and MYGEOTAB_PASSWORD '
                    'environment variables being set')


@pytest.fixture(scope='session')
def async_populated_api_entity(async_populated_api):
    def clean_trailers():
        try:
            trailers = async_populated_api.get('Trailer', name=TRAILER_NAME)
            for trailer in trailers:
                async_populated_api.remove('Trailer', trailer)
        except Exception:
            pass
    clean_trailers()
    yield async_populated_api
    clean_trailers()


class TestAsyncCallApi:
    def test_get_version(self, async_populated_api):
        version = run(async_populated_api.call_async('GetVersion'), loop=async_populated_api.loop)
        assert len(version) == 1
        version_split = version[0].split('.')
        assert len(version_split) == 4

    def test_get_user(self, async_populated_api):
        user = run(async_populated_api.get_async('User', name=USERNAME), loop=async_populated_api.loop)
        assert len(user) == 1
        assert len(user[0]) == 1
        user = user[0][0]
        assert user['name'] == USERNAME

    def test_get_user_search(self, async_populated_api):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            user = run(async_populated_api.search_async('User', name=USERNAME), loop=async_populated_api.loop)
        assert len(w) == 1
        assert issubclass(w[-1].category, DeprecationWarning)
        assert 'search_async()' in str(w[-1].message)
        assert len(user) == 1
        assert len(user[0]) == 1
        user = user[0][0]
        assert user['name'] == USERNAME

    def test_multi_call(self, async_populated_api):
        calls = [
            ['Get', dict(typeName='User', search=dict(name='{0}'.format(USERNAME)))],
            ['GetVersion']
        ]
        results = run(async_populated_api.multi_call_async(calls), loop=async_populated_api.loop)
        assert len(results) == 1
        results = results[0]
        assert len(results) == 2
        assert results[0] is not None
        assert len(results[0]) == 1
        assert results[0][0]['name'] == USERNAME
        assert results[1] is not None
        version_split = results[1].split('.')
        assert len(version_split) == 4

    def test_pythonic_parameters(self, async_populated_api):
        users = async_populated_api.get('User')
        count_users = run(async_populated_api.call_async('Get', type_name='User'), loop=async_populated_api.loop)
        assert len(count_users) == 1
        assert len(count_users[0]) >= 1
        assert len(count_users[0]) == len(users)

    def test_api_from_credentials(self, async_populated_api):
        new_api = from_credentials(async_populated_api.credentials, loop=async_populated_api.loop)
        users = run(new_api.get_async('User'), loop=async_populated_api.loop)
        assert len(users) >= 1

    def test_results_limit(self, async_populated_api):
        users = run(async_populated_api.get_async('User', resultsLimit=1), loop=async_populated_api.loop)
        assert len(users) == 1

    def test_session_expired(self, async_populated_api):
        credentials = async_populated_api.credentials
        credentials.password = PASSWORD
        credentials.session_id = 'abc123'
        test_api = from_credentials(credentials, loop=async_populated_api.loop)
        users = run(test_api.get_async('User'), loop=async_populated_api.loop)
        assert len(users) >= 1

    def test_missing_method(self, async_populated_api):
        with pytest.raises(Exception):
            run(async_populated_api.call_async(None), loop=async_populated_api.loop)

    def test_call_without_credentials(self):
        loop = asyncio.get_event_loop() or asyncio.new_event_loop()
        new_api = API(USERNAME, password=PASSWORD, database=DATABASE, server=None, loop=loop)
        user = run(new_api.get_async('User', name='{0}'.format(USERNAME)), loop=loop)
        assert len(user) == 1
        assert len(user[0]) == 1

    def test_bad_parameters(self, async_populated_api):
        with pytest.raises(MyGeotabException) as excinfo:
            run(async_populated_api.call_async('NonExistentMethod', not_a_property='abc123'), loop=async_populated_api.loop)
        assert 'NonExistentMethod' in str(excinfo.value)

    def test_get_search_parameter(self, async_populated_api):
        user = run(async_populated_api.get_async('User', search=dict(name=USERNAME)), loop=async_populated_api.loop)
        assert len(user) == 1
        assert len(user[0]) == 1
        user = user[0][0]
        assert user['name'] == USERNAME

    def test_add_edit_remove(self, async_populated_api_entity):
        def get_trailer():
            trailers = run(async_populated_api_entity.get_async('Trailer', name=TRAILER_NAME), loop=async_populated_api_entity.loop)
            assert len(trailers) == 1
            assert len(trailers[0]) == 1
            return trailers[0][0]
        user = async_populated_api_entity.get('User', name=USERNAME)[0]
        trailer = {
            'name': TRAILER_NAME,
            'groups': user['companyGroups']
        }
        trailer_id = run(async_populated_api_entity.add_async('Trailer', trailer), loop=async_populated_api_entity.loop)
        assert len(trailer_id) == 1
        trailer['id'] = trailer_id[0]
        trailer = get_trailer()
        assert trailer['name'] == TRAILER_NAME
        comment = 'some comment'
        trailer['comment'] = comment
        run(async_populated_api_entity.set_async('Trailer', trailer), loop=async_populated_api_entity.loop)
        trailer = get_trailer()
        assert trailer['comment'] == comment
        run(async_populated_api_entity.remove_async('Trailer', trailer), loop=async_populated_api_entity.loop)
        trailers = run(async_populated_api_entity.get_async('Trailer', name=TRAILER_NAME), loop=async_populated_api_entity.loop)
        assert len(trailers) == 1
        assert len(trailers[0]) == 0


@pytest.mark.skipif(USERNAME is None or DATABASE is None,
                    reason=('Can\'t make calls to the API without the MYGEOTAB_USERNAME '
                            'and MYGEOTAB_PASSWORD environment variables being set'))
class TestAuthentication:
    def test_invalid_session(self):
        test_api = API(USERNAME, session_id='abc123', database=DATABASE)
        assert USERNAME in str(test_api.credentials)
        assert DATABASE in str(test_api.credentials)
        with pytest.raises(AuthenticationException) as excinfo:
            test_api.get('User')
        assert 'Cannot authenticate' in str(excinfo.value)
        assert DATABASE in str(excinfo.value)
        assert USERNAME in str(excinfo.value)

    def test_auth_exception(self):
        test_api = API(USERNAME, password='abc123', database='this_database_does_not_exist')
        with pytest.raises(MyGeotabException) as excinfo:
            test_api.authenticate(False)
        assert excinfo.value.name == 'DbUnavailableException'

    def test_username_password_exists(self):
        with pytest.raises(Exception) as excinfo1:
            API(None)
        with pytest.raises(Exception) as excinfo2:
            API(USERNAME)
        assert 'username' in str(excinfo1.value)
        assert 'password' in str(excinfo2.value)


class TestAsyncServerCallApi:
    def test_get_version(self):
        loop = asyncio.get_event_loop()
        version = run(server_call('GetVersion', server='my3.geotab.com'), loop=loop)
        version_split = version[0].split('.')
        assert len(version_split) == 4

    def test_invalid_server_call(self):
        loop = asyncio.get_event_loop()
        with pytest.raises(Exception) as excinfo1:
            run(server_call(None, None), loop=loop)
        with pytest.raises(Exception) as excinfo2:
            run(server_call('GetVersion', None), loop=loop)
        assert 'method' in str(excinfo1.value)
        assert 'server' in str(excinfo2.value)
