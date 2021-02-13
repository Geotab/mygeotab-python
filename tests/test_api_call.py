# -*- coding: utf-8 -*-

import os

import pytest

from mygeotab import api
from mygeotab.exceptions import AuthenticationException, TimeoutException

USERNAME = os.environ.get("MYGEOTAB_USERNAME")
PASSWORD = os.environ.get("MYGEOTAB_PASSWORD")
DATABASE = os.environ.get("MYGEOTAB_DATABASE")
SERVER = os.environ.get("MYGEOTAB_SERVER")
TRAILER_NAME = "mygeotab-python test trailer"

FAKE_USERNAME = "fakeusername"
FAKE_PASSWORD = "fakepassword"
FAKE_DATABASE = "fakedatabase"
FAKE_SESSIONID = "3n8943bsdf768"


@pytest.fixture(scope="session")
def populated_api():
    if USERNAME and PASSWORD:
        session = api.API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        try:
            session.authenticate()
        except api.MyGeotabException as exception:
            pytest.fail(exception)
            return
        yield session
    else:
        pytest.skip(
            "Can't make calls to the API without the "
            "MYGEOTAB_USERNAME and MYGEOTAB_PASSWORD "
            "environment variables being set"
        )


@pytest.fixture(scope="session")
def populated_api_entity(populated_api):
    def clean_trailers():
        try:
            trailers = populated_api.get("Trailer", name=TRAILER_NAME)
            for trailer in trailers:
                populated_api.remove("Trailer", trailer)
        except Exception:
            pass

    clean_trailers()
    yield populated_api
    clean_trailers()


class TestCallApi:
    def test_get_version(self, populated_api):
        version = populated_api.call("GetVersion")
        version_split = version.split(".")
        assert len(version_split) == 4

    def test_get_user(self, populated_api):
        user = populated_api.get("User", name=USERNAME)
        assert len(user) == 1
        user = user[0]
        assert user["name"] == USERNAME

    def test_multi_call(self, populated_api):
        calls = [["Get", dict(typeName="User", search=dict(name="{0}".format(USERNAME)))], ["GetVersion"]]
        results = populated_api.multi_call(calls)
        assert len(results) == 2
        assert results[0] is not None
        assert len(results[0]) == 1
        assert results[0][0]["name"] == USERNAME
        assert results[1] is not None
        version_split = results[1].split(".")
        assert len(version_split) == 4

    def test_pythonic_parameters(self, populated_api):
        users = populated_api.get("User")
        count_users = populated_api.call("Get", type_name="User")
        assert len(count_users) >= 1
        assert len(count_users) == len(users)

    def test_api_from_credentials(self, populated_api):
        new_api = api.API.from_credentials(populated_api.credentials)
        users = new_api.get("User")
        assert len(users) >= 1

    def test_results_limit(self, populated_api):
        users = populated_api.get("User", resultsLimit=1)
        assert len(users) == 1

    def test_session_expired(self, populated_api):
        credentials = populated_api.credentials
        credentials.password = PASSWORD
        credentials.session_id = "abc123"
        test_api = api.API.from_credentials(credentials)
        users = test_api.get("User")
        assert len(users) >= 1

    def test_missing_method(self, populated_api):
        with pytest.raises(Exception):
            populated_api.call(None)

    def test_call_without_credentials(self):
        if not (USERNAME and PASSWORD):
            pytest.skip(
                "Can't make calls to the API without the "
                "MYGEOTAB_USERNAME and MYGEOTAB_PASSWORD "
                "environment variables being set"
            )
        new_api = api.API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        user = new_api.get("User", name="{0}".format(USERNAME))
        assert len(user) == 1

    def test_bad_parameters(self, populated_api):
        with pytest.raises(api.MyGeotabException) as excinfo:
            populated_api.call("NonExistentMethod", not_a_property="abc123")
        assert "NonExistentMethod" in str(excinfo.value)

    def test_get_search_parameter(self, populated_api):
        user = populated_api.get("User", search=dict(name=USERNAME))
        assert len(user) == 1
        user = user[0]
        assert user["name"] == USERNAME


class TestEntity:
    def test_add_edit_remove(self, populated_api_entity):
        def get_trailer():
            trailers = populated_api_entity.get("Trailer", name=TRAILER_NAME)
            assert len(trailers) == 1
            return trailers[0]

        user = populated_api_entity.get("User", name=USERNAME)[0]
        trailer = {"name": TRAILER_NAME, "groups": user["companyGroups"]}
        trailer["id"] = populated_api_entity.add("Trailer", trailer)
        assert trailer["id"] is not None
        trailer = get_trailer()
        assert trailer["name"] == TRAILER_NAME
        comment = "some comment"
        trailer["comment"] = comment
        populated_api_entity.set("Trailer", trailer)
        trailer = get_trailer()
        assert trailer["comment"] == comment
        populated_api_entity.remove("Trailer", trailer)
        trailers = populated_api_entity.get("Trailer", name=TRAILER_NAME)
        assert len(trailers) == 0


class TestAuthentication:
    def test_invalid_session(self):
        test_api = api.API(FAKE_USERNAME, session_id=FAKE_SESSIONID, database=FAKE_DATABASE)
        assert FAKE_USERNAME in str(test_api.credentials)
        assert FAKE_DATABASE in str(test_api.credentials)
        with pytest.raises(AuthenticationException) as excinfo:
            test_api.get("User")
        assert "Cannot authenticate" in str(excinfo.value)
        assert FAKE_DATABASE in str(excinfo.value)
        assert FAKE_USERNAME in str(excinfo.value)

    def test_username_password_exists(self):
        with pytest.raises(Exception) as excinfo1:
            api.API(None)
        with pytest.raises(Exception) as excinfo2:
            api.API(FAKE_USERNAME)
        assert "username" in str(excinfo1.value)
        assert "password" in str(excinfo2.value)

    def test_call_authenticate_sessionid(self, populated_api):
        credentials = populated_api.authenticate()
        assert credentials.username == USERNAME
        assert credentials.database == DATABASE
        assert credentials.session_id is not None

    def test_call_authenticate_invalid_sessionid(self):
        test_api = api.API(FAKE_USERNAME, session_id=FAKE_SESSIONID, database=FAKE_DATABASE)
        with pytest.raises(AuthenticationException) as excinfo:
            test_api.authenticate()
        assert "Cannot authenticate" in str(excinfo.value)
        assert FAKE_DATABASE in str(excinfo.value)


class TestServerCallApi:
    def test_get_version(self):
        version = api.server_call("GetVersion", server="my3.geotab.com")
        version_split = version.split(".")
        assert len(version_split) == 4

    def test_invalid_server_call(self):
        with pytest.raises(Exception) as excinfo1:
            api.server_call(None, None)
        with pytest.raises(Exception) as excinfo2:
            api.server_call("GetVersion", None)
        assert "method" in str(excinfo1.value)
        assert "server" in str(excinfo2.value)

    def test_timeout(self):
        with pytest.raises(TimeoutException) as excinfo:
            api.server_call("GetVersion", server="my36.geotab.com", timeout=0.01)
        assert "Request timed out @ my36.geotab.com" in str(excinfo.value)
