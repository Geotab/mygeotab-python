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


class TestAuthenticateEdgeCases:
    """Cover authenticate() paths missed by the existing suite."""

    def test_extend_session_when_session_id_no_password(self, mock_query):
        """authenticate() with session_id and no password must call ExtendSession
        and return the *same* Credentials object unchanged."""
        mock_query.return_value = None  # ExtendSession returns None
        session = api.API(
            USERNAME,
            session_id=SESSION_ID,
            database=DATABASE,
            server=SERVER,
        )
        original_credentials = session.credentials
        result = session.authenticate()

        assert result is original_credentials
        assert result.session_id == SESSION_ID
        # Verify the method name passed to _query was ExtendSession
        called_method = mock_query.call_args[0][1]
        assert called_method == "ExtendSession"
        called_data = mock_query.call_args[0][2]
        assert called_data["sessionId"] == SESSION_ID
        assert called_data["userName"] == USERNAME

    def test_authenticate_this_server_keeps_current_server(self, mock_query):
        """When the server responds with path='ThisServer', the client's server
        must not change."""
        mock_query.return_value = {
            "path": "ThisServer",
            "credentials": {
                "userName": USERNAME,
                "sessionId": "new-session-id",
                "database": DATABASE,
            },
        }
        session = api.API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        creds = session.authenticate()

        assert creds.server == SERVER  # unchanged
        assert creds.session_id == "new-session-id"

    def test_authenticate_no_path_in_result_returns_existing_credentials(self, mock_query):
        """When the server returns a result with no 'path' key but a session_id
        is already present, the existing Credentials object is returned as-is."""
        # Seed a valid session_id so the code reaches the 'path' check
        session = api.API(
            USERNAME,
            password=PASSWORD,
            session_id=SESSION_ID,
            database=DATABASE,
            server=SERVER,
        )
        original = session.credentials
        mock_query.return_value = {
            # No 'path' key
            "credentials": {"userName": USERNAME, "sessionId": SESSION_ID, "database": DATABASE}
        }
        result = session.authenticate()
        assert result is original

    @pytest.mark.parametrize("message", ["Initializing", "UnknownDatabase"])
    def test_authenticate_db_unavailable_raises_auth_exception(self, mock_query, message):
        """DbUnavailableException with 'Initializing' or 'UnknownDatabase' in
        the message must be converted to AuthenticationException."""
        mock_query.side_effect = api.MyGeotabException(
            {"errors": [{"name": "DbUnavailableException", "message": message}]}
        )
        session = api.API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        with pytest.raises(AuthenticationException):
            session.authenticate()

    def test_authenticate_other_mygeotab_exception_re_raised(self, mock_query):
        """A MyGeotabException that is not InvalidUser/DbUnavailable must
        propagate without conversion."""
        mock_query.side_effect = api.MyGeotabException(
            {"errors": [{"name": "SomeOtherException", "message": "unexpected"}]}
        )
        session = api.API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        with pytest.raises(api.MyGeotabException):
            session.authenticate()


class TestCallReauth:
    """Cover call() re-authentication paths."""

    def test_reauth_on_invalid_user_when_password_present(self, mock_query):
        """When InvalidUserException is raised and the API object has a password,
        it must re-authenticate and retry the original call transparently."""
        # Sequence:
        #   1. Initial call → InvalidUserException (session expired)
        #   2. Re-authenticate → returns new credentials
        #   3. Retry call → success
        mock_query.side_effect = [
            api.MyGeotabException(
                {"errors": [{"name": "InvalidUserException", "message": "Session expired"}]}
            ),
            mock_authenticate_response(),  # authenticate() response
            mock_user_response(),           # retried get()
        ]
        session = api.API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        # Give the session a pre-existing session_id so it skips initial auth
        session.credentials.session_id = SESSION_ID

        result = session.get("User", name=USERNAME)
        assert len(result) == 1
        # Three _query calls: original + auth + retry
        assert mock_query.call_count == 3

    def test_no_infinite_reauth_loop(self, mock_query):
        """If InvalidUserException recurs after a re-auth attempt, the client
        must raise AuthenticationException instead of looping again."""
        session = api.API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        session.credentials.session_id = SESSION_ID
        # Artificially set the guard counter to 1, simulating a re-auth already done.
        session._API__reauthorize_count = 1

        mock_query.side_effect = api.MyGeotabException(
            {"errors": [{"name": "InvalidUserException", "message": "Invalid user"}]}
        )
        with pytest.raises(AuthenticationException):
            session.call("GetVersion")


class TestMiscAttributes:
    """Cover miscellaneous API utility paths requiring mock_query."""

    def test_multi_call_single_element_no_params(self, mock_query):
        """multi_call with a single-method entry (no params dict) must use an
        empty params dict rather than crash."""
        mock_query.return_value = mock_authenticate_response()
        session = api.API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        session.authenticate()

        mock_query.return_value = ["8.0.1234"]
        results = session.multi_call([["GetVersion"]])  # no params element
        assert results is not None


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
