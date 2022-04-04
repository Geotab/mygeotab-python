# -*- coding: utf-8 -*-

import os
import random
import string

import pytest

from mygeotab import api
from mygeotab.exceptions import AuthenticationException, TimeoutException

USERNAME = os.environ.get("MYGEOTAB_USERNAME")
PASSWORD = os.environ.get("MYGEOTAB_PASSWORD")
DATABASE = os.environ.get("MYGEOTAB_DATABASE")
SERVER = os.environ.get("MYGEOTAB_SERVER")
CER_FILE = os.environ.get("MYGEOTAB_CERTIFICATE_CER")
KEY_FILE = os.environ.get("MYGEOTAB_CERTIFICATE_KEY")
PEM_FILE = os.environ.get("MYGEOTAB_CERTIFICATE_PEM")
ZONETYPE_NAME = "mygeotab-python test zonetype"

FAKE_USERNAME = "fakeusername"
FAKE_PASSWORD = "fakepassword"
FAKE_DATABASE = "fakedatabase"
FAKE_SESSIONID = "3n8943bsdf768"


def get_random_str(str_length):
    return "".join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(str_length))


def generate_fake_credentials():
    return dict(
        username=FAKE_USERNAME + get_random_str(20),
        password=FAKE_PASSWORD + get_random_str(20),
        database=FAKE_DATABASE + get_random_str(20),
        sessionid=FAKE_SESSIONID + get_random_str(30),
    )


@pytest.fixture(scope="session")
def populated_api():
    cert = None
    if CER_FILE and KEY_FILE:
        cert = (CER_FILE, KEY_FILE)
    elif PEM_FILE:
        cert = PEM_FILE
    if USERNAME and PASSWORD:
        session = api.API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER, cert=cert)
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
    def clean_zonetypes():
        zonetypes = populated_api.get("ZoneType", name=ZONETYPE_NAME)
        for zonetype in zonetypes:
            populated_api.remove("ZoneType", zonetype)

    clean_zonetypes()
    yield populated_api
    clean_zonetypes()


class TestCallApi:
    def test_get_version(self, populated_api):
        version = populated_api.call("GetVersion")
        version_len = len(version.split("."))
        assert 3 <= version_len <= 4

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
        version_len = len(results[1].split("."))
        assert 3 <= version_len <= 4

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
        def get_zonetype():
            zonetypes = populated_api_entity.get("ZoneType", name=ZONETYPE_NAME)
            assert len(zonetypes) == 1
            return zonetypes[0]

        zonetype = {"name": ZONETYPE_NAME}
        zonetype["id"] = populated_api_entity.add("ZoneType", zonetype)
        assert zonetype["id"] is not None
        zonetype = get_zonetype()
        assert zonetype["name"] == ZONETYPE_NAME
        comment = "some comment"
        zonetype["comment"] = comment
        populated_api_entity.set("ZoneType", zonetype)
        zonetype = get_zonetype()
        assert zonetype["comment"] == comment
        populated_api_entity.remove("ZoneType", zonetype)
        zonetypes = populated_api_entity.get("ZoneType", name=ZONETYPE_NAME)
        assert len(zonetypes) == 0


class TestAuthentication:
    def test_invalid_session(self):
        fake_credentials = generate_fake_credentials()
        test_api = api.API(
            fake_credentials["username"],
            session_id=fake_credentials["sessionid"],
            database=fake_credentials["database"],
        )
        assert fake_credentials["username"] in str(test_api.credentials)
        assert fake_credentials["database"] in str(test_api.credentials)
        with pytest.raises(AuthenticationException) as excinfo:
            test_api.get("User")
        assert "Cannot authenticate" in str(excinfo.value)
        assert fake_credentials["database"] in str(excinfo.value)
        assert fake_credentials["username"] in str(excinfo.value)

    def test_username_password_exists(self):
        fake_credentials = generate_fake_credentials()
        with pytest.raises(Exception) as excinfo1:
            api.API(None)
        with pytest.raises(Exception) as excinfo2:
            api.API(fake_credentials["username"])
        assert "username" in str(excinfo1.value)
        assert "password" in str(excinfo2.value)

    def test_call_authenticate_sessionid(self, populated_api):
        credentials = populated_api.authenticate()
        assert credentials.username == USERNAME
        assert credentials.database == DATABASE
        assert credentials.session_id is not None

    def test_call_authenticate_invalid_sessionid(self):
        fake_credentials = generate_fake_credentials()
        test_api = api.API(
            fake_credentials["username"],
            session_id=fake_credentials["sessionid"],
            database=fake_credentials["database"],
        )
        with pytest.raises(AuthenticationException) as excinfo:
            test_api.authenticate()
        assert "Cannot authenticate" in str(excinfo.value)
        assert fake_credentials["database"] in str(excinfo.value)


class TestServerCallApi:
    def test_get_version(self):
        version = api.server_call("GetVersion", server="my3.geotab.com")
        version_split = version.split(".")
        assert len(version_split) == 3

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
