# -*- coding: utf-8 -*-

import os
import warnings

import pytest

from mygeotab import api

USERNAME = os.environ.get('MYGEOTAB_USERNAME')
PASSWORD = os.environ.get('MYGEOTAB_PASSWORD')
DATABASE = os.environ.get('MYGEOTAB_DATABASE')
TRAILER_NAME = 'mygeotab-python test trailer'


@pytest.fixture(scope='session')
def populated_api():
    if USERNAME and PASSWORD:
        session = api.API(USERNAME, password=PASSWORD, database=DATABASE, server=None)
        try:
            session.authenticate()
        except api.MyGeotabException as exception:
            pytest.fail(exception)
            return
        yield session
    else:
        pytest.skip('Can\'t make calls to the API without the '
                    'MYGEOTAB_USERNAME and MYGEOTAB_PASSWORD '
                    'environment variables being set')


@pytest.fixture(scope='session')
def populated_api_entity(populated_api):
    def clean_trailers():
        try:
            trailers = populated_api.get('Trailer', name=TRAILER_NAME)
            for trailer in trailers:
                populated_api.remove('Trailer', trailer)
        except Exception:
            pass
    clean_trailers()
    yield populated_api
    clean_trailers()


class TestAttributes:
    def test_should_verify_ssl(self):
        my_api = api.API('test@example.com', session_id=123, server='my3.geotab.com')
        assert my_api._is_verify_ssl is True
        my_api = api.API('test@example.com', session_id=123, server='127.0.0.1')
        assert my_api._is_verify_ssl is False
        my_api = api.API('test@example.com', session_id=123, server='localhost')
        assert my_api._is_verify_ssl is False
        my_api = api.API('test@example.com', session_id=123, server='my3.geotab.com', verify=False)
        assert my_api._is_verify_ssl is False


class TestProcessParameters:
    def test_camel_case_transformer(self):
        params = dict(search=dict(device_search=dict(id=123),
                                  include_overlapped_trips=True))
        fixed_params = api.process_parameters(params)
        assert fixed_params is not None
        assert 'search' in fixed_params
        assert 'deviceSearch' in fixed_params['search']
        assert 'id' in fixed_params['search']['deviceSearch']
        assert fixed_params['search']['deviceSearch']['id'] == 123
        assert 'includeOverlappedTrips' in fixed_params['search']
        assert fixed_params['search']['includeOverlappedTrips']


class TestProcessResults:
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
        with pytest.raises(api.MyGeotabException) as excinfo:
            api._process(exception_response)
        ex = excinfo.value
        assert ex.name == 'MissingMethodException'
        assert ex.message == \
                         ('The method "Get" could not be found. Verify the method name and ensure all method '
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
        assert len(result) == 1
        assert result[0]['name'] == 'test@example.com'
        assert result[0]['id'] == 'b123'

    def test_handle_none(self):
        result = api._process(None)
        assert result is None


class TestCallApi:
    def test_get_version(self, populated_api):
        version = populated_api.call('GetVersion')
        version_split = version.split('.')
        assert len(version_split) == 4

    def test_get_user(self, populated_api):
        user = populated_api.get('User', name=USERNAME)
        assert len(user) == 1
        user = user[0]
        assert user['name'] == USERNAME

    def test_get_user_search(self, populated_api):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            user = populated_api.search('User', name='{0}'.format(USERNAME))
        assert len(w) == 1
        assert issubclass(w[-1].category, DeprecationWarning)
        assert 'search()' in str(w[-1].message)
        assert len(user) == 1
        user = user[0]
        assert user['name'] == USERNAME

    def test_multi_call(self, populated_api):
        calls = [
            ['Get', dict(typeName='User', search=dict(name='{0}'.format(USERNAME)))],
            ['GetVersion']
        ]
        results = populated_api.multi_call(calls)
        assert len(results) == 2
        assert results[0] is not None
        assert len(results[0]) == 1
        assert results[0][0]['name'] == USERNAME
        assert results[1] is not None
        version_split = results[1].split('.')
        assert len(version_split) == 4

    def test_pythonic_parameters(self, populated_api):
        users = populated_api.get('User')
        count_users = populated_api.call('Get', type_name='User')
        assert len(count_users) >= 1
        assert len(count_users) == len(users)

    def test_api_from_credentials(self, populated_api):
        new_api = api.from_credentials(populated_api.credentials)
        users = new_api.get('User')
        assert len(users) >= 1

    def test_results_limit(self, populated_api):
        users = populated_api.get('User', resultsLimit=1)
        assert len(users) == 1

    def test_session_expired(self, populated_api):
        credentials = populated_api.credentials
        credentials.password = PASSWORD
        credentials.session_id = 'abc123'
        test_api = api.from_credentials(credentials)
        users = test_api.get('User')
        assert len(users) >= 1

    def test_missing_method(self, populated_api):
        with pytest.raises(Exception):
            populated_api.call(None)

    def test_call_without_credentials(self):
        if not (USERNAME and PASSWORD):
            pytest.skip('Can\'t make calls to the API without the '
                        'MYGEOTAB_USERNAME and MYGEOTAB_PASSWORD '
                        'environment variables being set')
        new_api = api.API(USERNAME, password=PASSWORD, database=DATABASE, server=None)
        user = new_api.get('User', name='{0}'.format(USERNAME))
        assert len(user) == 1

    def test_bad_parameters(self, populated_api):
        with pytest.raises(api.MyGeotabException) as excinfo:
            populated_api.call('NonExistentMethod', not_a_property='abc123')
        assert 'NonExistentMethod' in str(excinfo.value)

    def test_get_search_parameter(self, populated_api):
        user = populated_api.get('User', search=dict(name=USERNAME))
        assert len(user) == 1
        user = user[0]
        assert user['name'] == USERNAME


class TestEntity:
    def test_add_edit_remove(self, populated_api_entity):
        def get_trailer():
            trailers = populated_api_entity.get('Trailer', name=TRAILER_NAME)
            assert len(trailers) == 1
            return trailers[0]
        user = populated_api_entity.get('User', name=USERNAME)[0]
        trailer = {
            'name': TRAILER_NAME,
            'groups': user['companyGroups']
        }
        trailer['id'] = populated_api_entity.add('Trailer', trailer)
        assert trailer['id'] is not None
        trailer = get_trailer()
        assert trailer['name'] == TRAILER_NAME
        comment = 'some comment'
        trailer['comment'] = comment
        populated_api_entity.set('Trailer', trailer)
        trailer = get_trailer()
        assert trailer['comment'] == comment
        populated_api_entity.remove('Trailer', trailer)
        trailers = populated_api_entity.get('Trailer', name=TRAILER_NAME)
        assert len(trailers) == 0


@pytest.mark.skipif(USERNAME is None or DATABASE is None,
                    reason=('Can\'t make calls to the API without the MYGEOTAB_USERNAME '
                            'and MYGEOTAB_PASSWORD environment variables being set'))
class TestAuthentication:
    def test_invalid_session(self):
        test_api = api.API(USERNAME, session_id='abc123', database=DATABASE)
        assert USERNAME in str(test_api.credentials)
        assert DATABASE in str(test_api.credentials)
        with pytest.raises(api.AuthenticationException) as excinfo:
            test_api.get('User')
        assert 'Cannot authenticate' in str(excinfo.value)
        assert DATABASE in str(excinfo.value)
        assert USERNAME in str(excinfo.value)

    def test_auth_exception(self):
        test_api = api.API(USERNAME, password='abc123', database='this_database_does_not_exist')
        with pytest.raises(api.MyGeotabException) as excinfo:
            test_api.authenticate(False)
        assert excinfo.value.name == 'DbUnavailableException'

    def test_username_password_exists(self):
        with pytest.raises(Exception) as excinfo1:
            api.API(None)
        with pytest.raises(Exception) as excinfo2:
            api.API(USERNAME)
        assert 'username' in str(excinfo1.value)
        assert 'password' in str(excinfo2.value)


class TestServerCallApi:
    def test_get_version(self):
        version = api.server_call('GetVersion', server='my3.geotab.com')
        version_split = version.split('.')
        assert len(version_split) == 4

    def test_invalid_server_call(self):
        with pytest.raises(Exception) as excinfo1:
            api.server_call(None, None)
        with pytest.raises(Exception) as excinfo2:
            api.server_call('GetVersion', None)
        assert 'method' in str(excinfo1.value)
        assert 'server' in str(excinfo2.value)
