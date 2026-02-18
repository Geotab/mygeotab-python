# -*- coding: utf-8 -*-

from unittest.mock import AsyncMock, patch

import pytest

from mygeotab import API, server_call_async
from mygeotab.exceptions import AuthenticationException, MyGeotabException, TimeoutException
from tests.test_api_call import (
    DATABASE,
    PASSWORD,
    SERVER,
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
def mock_async_query():
    """Fixture to mock the async _query function."""
    with patch("mygeotab.api_async._query", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_sync_query():
    """Fixture to mock the sync _query function for authentication."""
    with patch("mygeotab.api._query") as mock:
        yield mock


@pytest.fixture
def async_populated_api(mock_sync_query):
    """Create an async API instance with mocked credentials."""
    mock_sync_query.return_value = mock_authenticate_response()
    session = API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
    session.authenticate()
    mock_sync_query.return_value = None
    yield session


@pytest.fixture
def async_populated_api_entity(async_populated_api, mock_async_query):
    """Create an async API instance for entity tests."""
    mock_async_query.return_value = []
    yield async_populated_api
    mock_async_query.return_value = []


class TestAsyncCallApi:
    @pytest.mark.asyncio
    async def test_get_version(self, async_populated_api, mock_async_query):
        mock_async_query.return_value = mock_version_response()
        version = await async_populated_api.call_async("GetVersion")
        version_len = len(version.split("."))
        assert 3 <= version_len <= 4

    @pytest.mark.asyncio
    async def test_get_user(self, async_populated_api, mock_async_query):
        mock_async_query.return_value = mock_user_response()
        user = await async_populated_api.get_async("User", name=USERNAME)
        assert len(user) == 1
        user = user[0]
        assert user["name"] == USERNAME

    @pytest.mark.asyncio
    async def test_multi_call(self, async_populated_api, mock_async_query):
        mock_async_query.return_value = [mock_user_response(), mock_version_response()]
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
    async def test_pythonic_parameters(self, async_populated_api, mock_sync_query, mock_async_query):
        mock_sync_query.return_value = mock_user_response()
        mock_async_query.return_value = mock_user_response()
        users = async_populated_api.get("User")
        count_users = await async_populated_api.call_async("Get", type_name="User")
        assert len(count_users) >= 1
        assert len(count_users) == len(users)

    @pytest.mark.asyncio
    async def test_api_from_credentials(self, async_populated_api, mock_async_query):
        mock_async_query.return_value = mock_user_response()
        new_api = API.from_credentials(async_populated_api.credentials)
        users = await new_api.get_async("User")
        assert len(users) >= 1

    @pytest.mark.asyncio
    async def test_results_limit(self, async_populated_api, mock_async_query):
        mock_async_query.return_value = mock_user_response()
        users = await async_populated_api.get_async("User", resultsLimit=1)
        assert len(users) == 1

    @pytest.mark.asyncio
    async def test_session_expired(self, async_populated_api, mock_async_query):
        credentials = async_populated_api.credentials
        credentials.password = PASSWORD
        credentials.session_id = "abc123"
        test_api = API.from_credentials(credentials)
        mock_async_query.return_value = mock_user_response()
        users = await test_api.get_async("User")
        assert len(users) >= 1

    @pytest.mark.asyncio
    async def test_missing_method(self, async_populated_api):
        with pytest.raises(Exception):
            await async_populated_api.call_async(None)

    @pytest.mark.asyncio
    async def test_call_without_credentials(self, mock_sync_query, mock_async_query):
        mock_sync_query.return_value = mock_authenticate_response()
        new_api = API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        mock_async_query.return_value = mock_user_response()
        user = await new_api.get_async("User", name="{0}".format(USERNAME))
        assert len(user) == 1

    @pytest.mark.asyncio
    async def test_bad_parameters(self, async_populated_api, mock_async_query):
        mock_async_query.side_effect = MyGeotabException(
            {"errors": [{"name": "MissingMethodException", "message": "NonExistentMethod could not be found"}]}
        )
        with pytest.raises(MyGeotabException) as excinfo:
            await async_populated_api.call_async("NonExistentMethod", not_a_property="abc123")
        assert "NonExistentMethod" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_get_search_parameter(self, async_populated_api, mock_async_query):
        mock_async_query.return_value = mock_user_response()
        user = await async_populated_api.get_async("User", search=dict(name=USERNAME))
        assert len(user) == 1
        user = user[0]
        assert user["name"] == USERNAME

    @pytest.mark.asyncio
    async def test_add_edit_remove(self, async_populated_api_entity, mock_sync_query, mock_async_query):
        zonetype_id = "zt123"

        # Get user for company groups (sync)
        mock_sync_query.return_value = [{"id": "u123", "name": USERNAME, "companyGroups": [{"id": "g123"}]}]
        user = async_populated_api_entity.get("User", name=USERNAME)[0]

        # Mock async add
        mock_async_query.return_value = zonetype_id
        zonetype = {"name": ASYNC_ZONETYPE_NAME, "groups": user["companyGroups"]}
        zonetype_id = await async_populated_api_entity.add_async("ZoneType", zonetype)
        zonetype["id"] = zonetype_id

        # Mock async get
        mock_async_query.return_value = [mock_zonetype_response(ASYNC_ZONETYPE_NAME, zonetype_id)]
        zonetypes = await async_populated_api_entity.get_async("ZoneType", name=ASYNC_ZONETYPE_NAME)
        assert len(zonetypes) == 1
        zonetype = zonetypes[0]
        assert zonetype["name"] == ASYNC_ZONETYPE_NAME

        # Mock async set
        comment = "some comment"
        zonetype["comment"] = comment
        mock_async_query.return_value = None
        await async_populated_api_entity.set_async("ZoneType", zonetype)

        # Mock async get after set
        mock_async_query.return_value = [mock_zonetype_response(ASYNC_ZONETYPE_NAME, zonetype_id, comment)]
        zonetype = (await async_populated_api_entity.get_async("ZoneType", name=ASYNC_ZONETYPE_NAME))[0]
        assert zonetype["comment"] == comment

        # Mock async remove
        mock_async_query.return_value = None
        await async_populated_api_entity.remove_async("ZoneType", zonetype)

        # Mock async get after remove
        mock_async_query.return_value = []
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
    async def test_timeout(self, mock_async_query):
        mock_async_query.side_effect = TimeoutException("my36.geotab.com")
        with pytest.raises(TimeoutException) as excinfo:
            await server_call_async("GetVersion", server="my36.geotab.com", timeout=0.01)
        assert "Request timed out @ my36.geotab.com" in str(excinfo.value)


class TestAsyncAuthentication:
    @pytest.mark.asyncio
    async def test_invalid_session(self, mock_async_query):
        fake_credentials = generate_fake_credentials()
        test_api = API(
            fake_credentials["username"],
            session_id=fake_credentials["sessionid"],
            database=fake_credentials["database"],
        )
        assert fake_credentials["username"] in str(test_api.credentials)
        assert fake_credentials["database"] in str(test_api.credentials)

        mock_async_query.side_effect = MyGeotabException(
            {"errors": [{"name": "InvalidUserException", "message": "Invalid user"}]}
        )
        with pytest.raises(AuthenticationException) as excinfo:
            await test_api.get_async("User")
        assert "Cannot authenticate" in str(excinfo.value)
        assert fake_credentials["database"] in str(excinfo.value)
        assert fake_credentials["username"] in str(excinfo.value)
