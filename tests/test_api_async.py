from unittest.mock import AsyncMock, patch

import pytest

from mygeotab import API, server_call_async
from mygeotab.exceptions import AuthenticationException, MyGeotabException, TimeoutException
from tests.test_api_call import (
    DATABASE,
    PASSWORD,
    SERVER,
    SESSION_ID,
    USERNAME,
    ZONETYPE_NAME,
    generate_fake_credentials,
    mock_authenticate_response,
    mock_user_response,
    mock_version_response,
    mock_zonetype_response,
)

ASYNC_ZONETYPE_NAME = "async {name}".format(name=ZONETYPE_NAME)


@pytest.fixture
def mock_query():
    """Fixture to mock the _query_async function where it's used in api.py."""
    with patch("mygeotab.api._query_async", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def async_populated_api(mock_query):
    """Create an async API instance with mocked credentials."""
    mock_query.return_value = mock_authenticate_response()
    session = API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
    session.authenticate()
    mock_query.return_value = None
    yield session


@pytest.fixture
def async_populated_api_entity(async_populated_api, mock_query):
    """Create an async API instance for entity tests."""
    mock_query.return_value = []
    yield async_populated_api
    mock_query.return_value = []


class TestAsyncCallApi:
    @pytest.mark.asyncio
    async def test_get_version(self, async_populated_api, mock_query):
        mock_query.return_value = mock_version_response()
        version = await async_populated_api.call_async("GetVersion")
        version_len = len(version.split("."))
        assert 3 <= version_len <= 4

    @pytest.mark.asyncio
    async def test_get_user(self, async_populated_api, mock_query):
        mock_query.return_value = mock_user_response()
        user = await async_populated_api.get_async("User", name=USERNAME)
        assert len(user) == 1
        user = user[0]
        assert user["name"] == USERNAME

    @pytest.mark.asyncio
    async def test_multi_call(self, async_populated_api, mock_query):
        mock_query.return_value = [mock_user_response(), mock_version_response()]
        calls = [["Get", dict(typeName="User", search=dict(name="{0}".format(USERNAME)))], ["GetVersion"]]
        results = await async_populated_api.multi_call_async(calls)
        assert len(results) == 2
        assert results[0] is not None
        assert len(results[0]) == 1
        assert results[0][0]["name"] == USERNAME
        assert results[1] is not None
        version_len = len(results[1].split("."))
        assert 3 <= version_len <= 4

    @pytest.mark.asyncio
    async def test_pythonic_parameters(self, async_populated_api, mock_query):
        mock_query.return_value = mock_user_response()
        users = async_populated_api.get("User")
        count_users = await async_populated_api.call_async("Get", type_name="User")
        assert len(count_users) >= 1
        assert len(count_users) == len(users)

    @pytest.mark.asyncio
    async def test_api_from_credentials(self, async_populated_api, mock_query):
        mock_query.return_value = mock_user_response()
        new_api = API.from_credentials(async_populated_api.credentials)
        users = await new_api.get_async("User")
        assert len(users) >= 1

    @pytest.mark.asyncio
    async def test_results_limit(self, async_populated_api, mock_query):
        mock_query.return_value = mock_user_response()
        users = await async_populated_api.get_async("User", resultsLimit=1)
        assert len(users) == 1

    @pytest.mark.asyncio
    async def test_session_expired(self, async_populated_api, mock_query):
        credentials = async_populated_api.credentials
        credentials.password = PASSWORD
        credentials.session_id = "abc123"
        test_api = API.from_credentials(credentials)
        mock_query.return_value = mock_user_response()
        users = await test_api.get_async("User")
        assert len(users) >= 1

    @pytest.mark.asyncio
    async def test_missing_method(self, async_populated_api):
        with pytest.raises(Exception):
            await async_populated_api.call_async(None)

    @pytest.mark.asyncio
    async def test_call_without_credentials(self, mock_query):
        # Use side_effect to return different values for consecutive calls
        mock_query.side_effect = [
            mock_authenticate_response(),  # First call: authentication
            mock_user_response()           # Second call: get user
        ]
        new_api = API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        user = await new_api.get_async("User", name="{0}".format(USERNAME))
        assert len(user) == 1

    @pytest.mark.asyncio
    async def test_bad_parameters(self, async_populated_api, mock_query):
        mock_query.side_effect = MyGeotabException(
            {"errors": [{"name": "MissingMethodException", "message": "NonExistentMethod could not be found"}]}
        )
        with pytest.raises(MyGeotabException) as excinfo:
            await async_populated_api.call_async("NonExistentMethod", not_a_property="abc123")
        assert "NonExistentMethod" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_get_search_parameter(self, async_populated_api, mock_query):
        mock_query.return_value = mock_user_response()
        user = await async_populated_api.get_async("User", search=dict(name=USERNAME))
        assert len(user) == 1
        user = user[0]
        assert user["name"] == USERNAME

    @pytest.mark.asyncio
    async def test_add_edit_remove(self, async_populated_api_entity, mock_query):
        zonetype_id = "zt123"

        # Set up side_effect for the sequence of calls
        mock_query.side_effect = [
            [{"id": "u123", "name": USERNAME, "companyGroups": [{"id": "g123"}]}],  # Get user (sync)
            zonetype_id,  # Add zonetype
            [mock_zonetype_response(ASYNC_ZONETYPE_NAME, zonetype_id)],  # Get zonetype
            None,  # Set zonetype
            [mock_zonetype_response(ASYNC_ZONETYPE_NAME, zonetype_id, "some comment")],  # Get zonetype after set
            None,  # Remove zonetype
            [],  # Get zonetype after remove
        ]

        # Get user for company groups (sync)
        user = async_populated_api_entity.get("User", name=USERNAME)[0]

        # Add zonetype
        zonetype = {"name": ASYNC_ZONETYPE_NAME, "groups": user["companyGroups"]}
        zonetype_id = await async_populated_api_entity.add_async("ZoneType", zonetype)
        zonetype["id"] = zonetype_id

        # Get zonetype
        zonetypes = await async_populated_api_entity.get_async("ZoneType", name=ASYNC_ZONETYPE_NAME)
        assert len(zonetypes) == 1
        zonetype = zonetypes[0]
        assert zonetype["name"] == ASYNC_ZONETYPE_NAME

        # Set zonetype
        comment = "some comment"
        zonetype["comment"] = comment
        await async_populated_api_entity.set_async("ZoneType", zonetype)

        # Get zonetype after set
        zonetype = (await async_populated_api_entity.get_async("ZoneType", name=ASYNC_ZONETYPE_NAME))[0]
        assert zonetype["comment"] == comment

        # Remove zonetype
        await async_populated_api_entity.remove_async("ZoneType", zonetype)

        # Get zonetype after remove
        zonetypes = await async_populated_api_entity.get_async("ZoneType", name=ASYNC_ZONETYPE_NAME)
        assert len(zonetypes) == 0


class TestAsyncServerCallApi:
    @pytest.mark.asyncio
    async def test_invalid_server_call(self):
        with pytest.raises(Exception) as excinfo1:
            await server_call_async(None, None)
        with pytest.raises(Exception) as excinfo2:
            await server_call_async("GetVersion", None)
        assert "method" in str(excinfo1.value)
        assert "server" in str(excinfo2.value)

    @pytest.mark.asyncio
    async def test_timeout(self, mock_query):
        mock_query.side_effect = TimeoutException("my36.geotab.com")
        with pytest.raises(TimeoutException) as excinfo:
            await server_call_async("GetVersion", server="my36.geotab.com", timeout=0.01)
        assert "Request timed out @ my36.geotab.com" in str(excinfo.value)


class TestAsyncAuthentication:
    @pytest.mark.asyncio
    async def test_invalid_session(self, mock_query):
        fake_credentials = generate_fake_credentials()
        test_api = API(
            fake_credentials["username"],
            session_id=fake_credentials["sessionid"],
            database=fake_credentials["database"],
        )
        assert fake_credentials["username"] in str(test_api.credentials)
        assert fake_credentials["database"] in str(test_api.credentials)

        mock_query.side_effect = MyGeotabException(
            {"errors": [{"name": "InvalidUserException", "message": "Invalid user"}]}
        )
        with pytest.raises(AuthenticationException) as excinfo:
            await test_api.get_async("User")
        assert "Cannot authenticate" in str(excinfo.value)
        assert fake_credentials["database"] in str(excinfo.value)
        assert fake_credentials["username"] in str(excinfo.value)


class TestAsyncSessionManagement:
    """Tests for async session lifecycle management."""

    @pytest.mark.asyncio
    async def test_async_context_manager_creates_session(self, mock_query):
        """Test that async context manager creates and manages a session."""
        mock_query.side_effect = [
            mock_authenticate_response(),
            mock_user_response(),
        ]
        async with API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER) as session:
            assert session._http_session is not None
            assert session._owns_session is True
            await session.authenticate_async()
            users = await session.get_async("User")
            assert len(users) == 1
        # After exiting context, session should be closed
        assert session._http_session is None
        assert session._owns_session is False

    @pytest.mark.asyncio
    async def test_async_context_manager_multiple_calls_reuse_session(self, mock_query):
        """Test that multiple async calls within context manager reuse the same session."""
        mock_query.side_effect = [
            mock_authenticate_response(),
            mock_user_response(),
            mock_version_response(),
        ]
        async with API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER) as session:
            await session.authenticate_async()
            original_session = session._http_session
            await session.get_async("User")
            await session.call_async("GetVersion")
            # Session should be the same object
            assert session._http_session is original_session

    @pytest.mark.asyncio
    async def test_close_async_method(self, mock_query):
        """Test that close_async() properly cleans up the session."""
        mock_query.return_value = mock_authenticate_response()
        session = API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        # Manually enter async context to create session
        await session.__aenter__()
        assert session._http_session is not None
        assert session._owns_session is True

        # Close should clean up
        await session.close_async()
        assert session._http_session is None
        assert session._owns_session is False

    @pytest.mark.asyncio
    async def test_user_provided_session_async(self, mock_query):
        """Test that user-provided sessions work with async calls."""
        import aiohttp

        mock_query.return_value = mock_user_response()

        # Create a mock session
        mock_session = AsyncMock(spec=aiohttp.ClientSession)

        session = API(
            USERNAME,
            session_id="test_session_id",
            database=DATABASE,
            server=SERVER,
            http_session=mock_session,
        )

        # User-provided session should be used but not owned
        assert session._http_session is mock_session
        assert session._owns_session is False

        # Make a call - it should use the provided session
        users = await session.get_async("User")
        assert len(users) == 1

        # close_async() should not close user-provided session
        await session.close_async()
        assert session._http_session is mock_session  # Still there
        mock_session.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_session_passed_to_query(self, mock_query):
        """Test that the session is passed to _query_async when available."""
        mock_query.side_effect = [
            mock_authenticate_response(),
            mock_user_response(),
        ]
        async with API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER) as session:
            await session.authenticate_async()
            await session.get_async("User")

            # Check that _query_async was called with the session
            # The session parameter should be passed in the calls
            for call in mock_query.call_args_list:
                # session is passed as a keyword argument
                assert "session" in call.kwargs or len(call.args) > 6


class TestAsyncAuthenticateEdgeCases:
    @pytest.mark.asyncio
    async def test_extend_session_without_password(self, mock_query):
        """When session_id is set but password is not, authenticate calls ExtendSession."""
        mock_query.return_value = None
        my_api = API(USERNAME, session_id=SESSION_ID, database=DATABASE, server=SERVER)
        result = await my_api.authenticate_async()
        assert result is my_api.credentials
        mock_query.assert_called_once()
        assert mock_query.call_args[0][1] == "ExtendSession"

    @pytest.mark.asyncio
    async def test_this_server_keeps_original(self, mock_query):
        """When auth returns 'ThisServer', keep the original server."""
        mock_query.return_value = {
            "path": "ThisServer",
            "credentials": {
                "userName": USERNAME,
                "sessionId": SESSION_ID,
                "database": DATABASE,
            },
        }
        my_api = API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        creds = await my_api.authenticate_async()
        assert creds.server == SERVER

    @pytest.mark.asyncio
    async def test_session_extended_no_path(self, mock_query):
        """When auth result has no 'path' key and session_id exists, session was extended."""
        mock_query.return_value = {
            "credentials": {
                "userName": USERNAME,
                "sessionId": "new_session",
                "database": DATABASE,
            },
        }
        my_api = API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER, session_id=SESSION_ID)
        result = await my_api.authenticate_async()
        assert result is my_api.credentials

    @pytest.mark.asyncio
    async def test_authenticate_returns_none_on_falsy_result(self, mock_query):
        """When authenticate gets a falsy result from the server, returns None."""
        mock_query.return_value = None
        my_api = API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        result = await my_api.authenticate_async()
        assert result is None

    @pytest.mark.asyncio
    async def test_db_unavailable_initializing_raises_auth_exception(self, mock_query):
        """DbUnavailableException with 'Initializing' raises AuthenticationException."""
        mock_query.side_effect = MyGeotabException(
            {"errors": [{"name": "DbUnavailableException", "message": "Initializing database"}]}
        )
        my_api = API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER, session_id=SESSION_ID)
        with pytest.raises(AuthenticationException):
            await my_api.authenticate_async()

    @pytest.mark.asyncio
    async def test_db_unavailable_unknown_database_raises_auth_exception(self, mock_query):
        """DbUnavailableException with 'UnknownDatabase' raises AuthenticationException."""
        mock_query.side_effect = MyGeotabException(
            {"errors": [{"name": "DbUnavailableException", "message": "UnknownDatabase foo"}]}
        )
        my_api = API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER, session_id=SESSION_ID)
        with pytest.raises(AuthenticationException):
            await my_api.authenticate_async()

    @pytest.mark.asyncio
    async def test_other_exception_during_auth_re_raises(self, mock_query):
        """Non-auth exceptions during authenticate should re-raise as-is."""
        mock_query.side_effect = MyGeotabException(
            {"errors": [{"name": "SomeOtherException", "message": "Something else went wrong"}]}
        )
        my_api = API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        with pytest.raises(MyGeotabException) as excinfo:
            await my_api.authenticate_async()
        assert excinfo.value.name == "SomeOtherException"

    @pytest.mark.asyncio
    async def test_async_exit_without_owning_session(self):
        """__aexit__ when API doesn't own the session should be a no-op."""
        my_api = API(USERNAME, session_id=SESSION_ID, database=DATABASE, server=SERVER)
        my_api._http_session = "fake_session"
        my_api._owns_session = False
        await my_api.__aexit__(None, None, None)
        assert my_api._http_session == "fake_session"


class TestAsyncCallReauthentication:
    @pytest.mark.asyncio
    async def test_reauthenticate_on_invalid_user(self, mock_query):
        """On InvalidUserException during call, re-authenticate and retry once."""
        mock_query.return_value = mock_authenticate_response()
        my_api = API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        await my_api.authenticate_async()
        my_api.credentials.password = PASSWORD

        mock_query.side_effect = [
            MyGeotabException({"errors": [{"name": "InvalidUserException", "message": "Invalid user"}]}),
            mock_authenticate_response(),
            [{"id": "b1"}],
        ]
        result = await my_api.call_async("Get", type_name="User")
        assert result == [{"id": "b1"}]
        assert my_api._reauthorize_count == 0

    @pytest.mark.asyncio
    async def test_reauthenticate_on_db_unavailable_initializing(self, mock_query):
        """On DbUnavailableException with Initializing, re-authenticate and retry."""
        mock_query.return_value = mock_authenticate_response()
        my_api = API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        await my_api.authenticate_async()
        my_api.credentials.password = PASSWORD

        mock_query.side_effect = [
            MyGeotabException(
                {"errors": [{"name": "DbUnavailableException", "message": "Initializing database"}]}
            ),
            mock_authenticate_response(),
            [{"id": "b2"}],
        ]
        result = await my_api.call_async("Get", type_name="User")
        assert result == [{"id": "b2"}]

    @pytest.mark.asyncio
    async def test_no_reauthenticate_without_password(self, mock_query):
        """Without password, InvalidUserException should raise AuthenticationException."""
        my_api = API(USERNAME, session_id=SESSION_ID, database=DATABASE, server=SERVER)
        mock_query.side_effect = MyGeotabException(
            {"errors": [{"name": "InvalidUserException", "message": "Invalid user"}]}
        )
        with pytest.raises(AuthenticationException):
            await my_api.call_async("Get", type_name="User")

    @pytest.mark.asyncio
    async def test_non_auth_exception_re_raises(self, mock_query):
        """Non-auth MyGeotabExceptions during call should re-raise directly."""
        mock_query.return_value = mock_authenticate_response()
        my_api = API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        await my_api.authenticate_async()

        mock_query.side_effect = MyGeotabException(
            {"errors": [{"name": "SomeOtherException", "message": "Something went wrong"}]}
        )
        with pytest.raises(MyGeotabException) as excinfo:
            await my_api.call_async("Get", type_name="User")
        assert excinfo.value.name == "SomeOtherException"
