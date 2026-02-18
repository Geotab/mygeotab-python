# -*- coding: utf-8 -*-

import random
import string
from unittest.mock import patch

import pytest

from mygeotab import api
from mygeotab.exceptions import AuthenticationException, TimeoutException

USERNAME = "test@example.com"
PASSWORD = "testpassword"
DATABASE = "testdatabase"
SERVER = "my3.geotab.com"
SESSION_ID = "abc123sessionid"
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


def mock_authenticate_response():
    """Return a mock authentication response."""
    return {
        "path": SERVER,
        "credentials": {
            "userName": USERNAME,
            "sessionId": SESSION_ID,
            "database": DATABASE,
        },
    }


def mock_user_response():
    """Return a mock user response."""
    return [{"id": "b123", "name": USERNAME}]


def mock_version_response():
    """Return a mock version response."""
    return "8.0.1234"


def mock_zonetype_response(name, zonetype_id="zt123", comment=None):
    """Return a mock zonetype response."""
    result = {"id": zonetype_id, "name": name}
    if comment:
        result["comment"] = comment
    return result


@pytest.fixture
def mock_query():
    """Fixture to mock the _query function."""
    with patch("mygeotab.api._query") as mock:
        yield mock


@pytest.fixture
def populated_api(mock_query):
    """Create an API instance with mocked credentials."""
    mock_query.return_value = mock_authenticate_response()
    session = api.API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
    session.authenticate()
    mock_query.return_value = None
    yield session


@pytest.fixture
def populated_api_entity(populated_api, mock_query):
    """Create an API instance for entity tests."""
    mock_query.return_value = []
    yield populated_api
    mock_query.return_value = []


class TestCallApi:
    def test_get_version(self, populated_api, mock_query):
        mock_query.return_value = mock_version_response()
        version = populated_api.call("GetVersion")
        version_len = len(version.split("."))
        assert 3 <= version_len <= 4

    def test_get_user(self, populated_api, mock_query):
        mock_query.return_value = mock_user_response()
        user = populated_api.get("User", name=USERNAME)
        assert len(user) == 1
        user = user[0]
        assert user["name"] == USERNAME

    def test_multi_call(self, populated_api, mock_query):
        mock_query.return_value = [mock_user_response(), mock_version_response()]
        calls = [["Get", dict(typeName="User", search=dict(name="{0}".format(USERNAME)))], ["GetVersion"]]
        results = populated_api.multi_call(calls)
        assert len(results) == 2
        assert results[0] is not None
        assert len(results[0]) == 1
        assert results[0][0]["name"] == USERNAME
        assert results[1] is not None
        version_len = len(results[1].split("."))
        assert 3 <= version_len <= 4

    def test_pythonic_parameters(self, populated_api, mock_query):
        mock_query.return_value = mock_user_response()
        users = populated_api.get("User")
        count_users = populated_api.call("Get", type_name="User")
        assert len(count_users) >= 1
        assert len(count_users) == len(users)

    def test_api_from_credentials(self, populated_api, mock_query):
        mock_query.return_value = mock_user_response()
        new_api = api.API.from_credentials(populated_api.credentials)
        users = new_api.get("User")
        assert len(users) >= 1

    def test_results_limit(self, populated_api, mock_query):
        mock_query.return_value = mock_user_response()
        users = populated_api.get("User", resultsLimit=1)
        assert len(users) == 1

    def test_session_expired(self, populated_api, mock_query):
        credentials = populated_api.credentials
        credentials.password = PASSWORD
        credentials.session_id = "abc123"
        test_api = api.API.from_credentials(credentials)
        mock_query.return_value = mock_user_response()
        users = test_api.get("User")
        assert len(users) >= 1

    def test_missing_method(self, populated_api):
        with pytest.raises(Exception):
            populated_api.call(None)

    def test_call_without_credentials(self, mock_query):
        # Use side_effect to return different values for consecutive calls
        mock_query.side_effect = [
            mock_authenticate_response(),  # First call: authentication
            mock_user_response()           # Second call: get user
        ]
        new_api = api.API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        user = new_api.get("User", name="{0}".format(USERNAME))
        assert len(user) == 1

    def test_bad_parameters(self, populated_api, mock_query):
        mock_query.side_effect = api.MyGeotabException(
            {"errors": [{"name": "MissingMethodException", "message": "NonExistentMethod could not be found"}]}
        )
        with pytest.raises(api.MyGeotabException) as excinfo:
            populated_api.call("NonExistentMethod", not_a_property="abc123")
        assert "NonExistentMethod" in str(excinfo.value)

    def test_get_search_parameter(self, populated_api, mock_query):
        mock_query.return_value = mock_user_response()
        user = populated_api.get("User", search=dict(name=USERNAME))
        assert len(user) == 1
        user = user[0]
        assert user["name"] == USERNAME


class TestEntity:
    def test_add_edit_remove(self, populated_api_entity, mock_query):
        zonetype_id = "zt123"

        # Mock add
        mock_query.return_value = zonetype_id
        zonetype = {"name": ZONETYPE_NAME}
        zonetype["id"] = populated_api_entity.add("ZoneType", zonetype)
        assert zonetype["id"] is not None

        # Mock get after add
        mock_query.return_value = [mock_zonetype_response(ZONETYPE_NAME, zonetype_id)]
        zonetypes = populated_api_entity.get("ZoneType", name=ZONETYPE_NAME)
        assert len(zonetypes) == 1
        zonetype = zonetypes[0]
        assert zonetype["name"] == ZONETYPE_NAME

        # Mock set
        comment = "some comment"
        zonetype["comment"] = comment
        mock_query.return_value = None
        populated_api_entity.set("ZoneType", zonetype)

        # Mock get after set
        mock_query.return_value = [mock_zonetype_response(ZONETYPE_NAME, zonetype_id, comment)]
        zonetype = populated_api_entity.get("ZoneType", name=ZONETYPE_NAME)[0]
        assert zonetype["comment"] == comment

        # Mock remove
        mock_query.return_value = None
        populated_api_entity.remove("ZoneType", zonetype)

        # Mock get after remove
        mock_query.return_value = []
        zonetypes = populated_api_entity.get("ZoneType", name=ZONETYPE_NAME)
        assert len(zonetypes) == 0


class TestAuthentication:
    def test_invalid_session(self, mock_query):
        fake_credentials = generate_fake_credentials()
        test_api = api.API(
            fake_credentials["username"],
            session_id=fake_credentials["sessionid"],
            database=fake_credentials["database"],
        )
        assert fake_credentials["username"] in str(test_api.credentials)
        assert fake_credentials["database"] in str(test_api.credentials)

        mock_query.side_effect = api.MyGeotabException(
            {"errors": [{"name": "InvalidUserException", "message": "Invalid user"}]}
        )
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

    def test_call_authenticate_sessionid(self, mock_query):
        mock_query.return_value = mock_authenticate_response()
        session = api.API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        credentials = session.authenticate()
        assert credentials.username == USERNAME
        assert credentials.database == DATABASE
        assert credentials.session_id is not None

    def test_call_authenticate_invalid_sessionid(self, mock_query):
        fake_credentials = generate_fake_credentials()
        test_api = api.API(
            fake_credentials["username"],
            session_id=fake_credentials["sessionid"],
            database=fake_credentials["database"],
        )
        mock_query.side_effect = api.MyGeotabException(
            {"errors": [{"name": "InvalidUserException", "message": "Invalid user"}]}
        )
        with pytest.raises(AuthenticationException) as excinfo:
            test_api.authenticate()
        assert "Cannot authenticate" in str(excinfo.value)
        assert fake_credentials["database"] in str(excinfo.value)


class TestServerCallApi:
    def test_invalid_server_call(self):
        with pytest.raises(Exception) as excinfo1:
            api.server_call(None, None)
        with pytest.raises(Exception) as excinfo2:
            api.server_call("GetVersion", None)
        assert "method" in str(excinfo1.value)
        assert "server" in str(excinfo2.value)

    def test_timeout(self, mock_query):
        mock_query.side_effect = TimeoutException("my36.geotab.com")
        with pytest.raises(TimeoutException) as excinfo:
            api.server_call("GetVersion", server="my36.geotab.com", timeout=0.01)
        assert "Request timed out @ my36.geotab.com" in str(excinfo.value)
