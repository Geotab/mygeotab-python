# -*- coding: utf-8 -*-

import pytest

asyncio = pytest.importorskip("asyncio")

from mygeotab import AsyncAPI, server_call_async
from mygeotab.exceptions import AuthenticationException, MyGeotabException, TimeoutException

from .test_api_call import DATABASE, PASSWORD, SERVER, TRAILER_NAME, USERNAME

ASYNC_TRAILER_NAME = f"async {TRAILER_NAME}"
FAKE_USERNAME = "fakeusername"
FAKE_PASSWORD = "fakepassword"
FAKE_DATABASE = "fakedatabase"
FAKE_SESSIONID = "3n8943bsdf768"


@pytest.fixture(scope="session")
def event_loop():
    """Change event_loop fixture to module level."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def async_populated_api(event_loop):
    if USERNAME and PASSWORD:
        session = AsyncAPI(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        try:
            await session.authenticate()
        except MyGeotabException as exception:
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
async def async_populated_api_entity(async_populated_api: AsyncAPI, event_loop):
    async def clean_trailers():
        try:
            trailers = await async_populated_api.get("Trailer", name=ASYNC_TRAILER_NAME)
            for trailer in trailers:
                await async_populated_api.remove("Trailer", trailer)
        except Exception:
            pass

    await clean_trailers()
    yield async_populated_api
    await clean_trailers()


class TestAsyncAuthentication:
    @pytest.mark.asyncio
    async def test_invalid_session(self):
        test_api = AsyncAPI(FAKE_USERNAME, session_id=FAKE_SESSIONID, database=FAKE_DATABASE)
        assert FAKE_USERNAME in str(test_api.credentials)
        assert FAKE_DATABASE in str(test_api.credentials)
        with pytest.raises(AuthenticationException) as excinfo:
            await test_api.get("User")
        assert "Cannot authenticate" in str(excinfo.value)
        assert FAKE_DATABASE in str(excinfo.value)
        assert FAKE_USERNAME in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_username_password_exists(self):
        with pytest.raises(Exception) as excinfo1:
            AsyncAPI(None)
        with pytest.raises(Exception) as excinfo2:
            AsyncAPI(FAKE_USERNAME)
        assert "username" in str(excinfo1.value)
        assert "password" in str(excinfo2.value)

    @pytest.mark.asyncio
    async def test_call_authenticate_sessionid(self, async_populated_api: AsyncAPI):
        credentials = await async_populated_api.authenticate()
        assert credentials is not None
        assert credentials.username == USERNAME
        assert credentials.database == DATABASE
        assert credentials.session_id is not None

    @pytest.mark.asyncio
    async def test_call_authenticate_invalid_sessionid(self):
        test_api = AsyncAPI(FAKE_USERNAME, session_id=FAKE_SESSIONID, database=FAKE_DATABASE)
        with pytest.raises(AuthenticationException) as excinfo:
            await test_api.authenticate()
        assert "Cannot authenticate" in str(excinfo.value)
        assert FAKE_DATABASE in str(excinfo.value)


class TestAsyncCallApi:
    @pytest.mark.asyncio
    async def test_get_version(self, async_populated_api: AsyncAPI):
        version = await async_populated_api.call("GetVersion")
        version_split = version.split(".")
        assert len(version_split) == 4

    @pytest.mark.asyncio
    async def test_get_user(self, async_populated_api: AsyncAPI):
        user = await async_populated_api.get("User", name=USERNAME)
        assert len(user) == 1
        user = user[0]
        assert user["name"] == USERNAME

    @pytest.mark.asyncio
    async def test_multi_call(self, async_populated_api: AsyncAPI):
        calls = [["Get", dict(typeName="User", search=dict(name="{0}".format(USERNAME)))], ["GetVersion"]]
        results = await async_populated_api.multi_call(calls)
        assert len(results) == 2
        assert results[0] is not None
        assert len(results[0]) == 1
        assert results[0][0]["name"] == USERNAME
        assert results[1] is not None
        version_split = results[1].split(".")
        assert len(version_split) == 4

    @pytest.mark.asyncio
    async def test_pythonic_parameters(self, async_populated_api: AsyncAPI):
        users = await async_populated_api.get("User")
        count_users = await async_populated_api.call("Get", type_name="User")
        assert len(count_users) >= 1
        assert len(count_users) == len(users)

    @pytest.mark.asyncio
    async def test_api_from_credentials(self, async_populated_api: AsyncAPI):
        new_api = AsyncAPI.from_credentials(async_populated_api.credentials)
        users = await new_api.get("User")
        assert len(users) >= 1

    @pytest.mark.asyncio
    async def test_results_limit(self, async_populated_api: AsyncAPI):
        users = await async_populated_api.get("User", resultsLimit=1)
        assert len(users) == 1

    @pytest.mark.asyncio
    async def test_session_expired(self, async_populated_api: AsyncAPI):
        credentials = async_populated_api.credentials
        credentials.password = PASSWORD
        credentials.session_id = "abc123"
        test_api = AsyncAPI.from_credentials(credentials)
        users = await test_api.get("User")
        assert len(users) >= 1

    @pytest.mark.asyncio
    async def test_missing_method(self, async_populated_api: AsyncAPI):
        with pytest.raises(Exception):
            await async_populated_api.call(None)

    @pytest.mark.asyncio
    async def test_call_without_credentials(self):
        new_api = AsyncAPI(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        user = await new_api.get("User", name="{0}".format(USERNAME))
        assert len(user) == 1

    @pytest.mark.asyncio
    async def test_bad_parameters(self, async_populated_api: AsyncAPI):
        with pytest.raises(MyGeotabException) as excinfo:
            await async_populated_api.call("NonExistentMethod", not_a_property="abc123")
        assert "NonExistentMethod" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_get_search_parameter(self, async_populated_api: AsyncAPI):
        user = await async_populated_api.get("User", search=dict(name=USERNAME))
        assert len(user) == 1
        user = user[0]
        assert user["name"] == USERNAME

    @pytest.mark.asyncio
    async def test_add_edit_remove(self, async_populated_api_entity: AsyncAPI):
        async def get_trailer():
            trailers = await async_populated_api_entity.get("Trailer", name=ASYNC_TRAILER_NAME)
            assert len(trailers) == 1
            return trailers[0]

        user = (await async_populated_api_entity.get("User", name=USERNAME))[0]
        trailer = {"name": ASYNC_TRAILER_NAME, "groups": user["companyGroups"]}
        trailer_id = await async_populated_api_entity.add("Trailer", trailer)
        trailer["id"] = trailer_id
        trailer = await get_trailer()
        assert trailer["name"] == ASYNC_TRAILER_NAME
        comment = "some comment"
        trailer["comment"] = comment
        await async_populated_api_entity.set("Trailer", trailer)
        trailer = await get_trailer()
        assert trailer["comment"] == comment
        await async_populated_api_entity.remove("Trailer", trailer)
        trailers = await async_populated_api_entity.get("Trailer", name=ASYNC_TRAILER_NAME)
        assert len(trailers) == 0


class TestAsyncServerCallApi:
    @pytest.mark.asyncio
    async def test_get_version(self):
        version = await server_call_async("GetVersion", server="my3.geotab.com")
        version_split = version.split(".")
        assert len(version_split) == 4

    @pytest.mark.asyncio
    async def test_invalid_server_call(self):
        with pytest.raises(Exception) as excinfo1:
            await server_call_async(None, None)
        with pytest.raises(Exception) as excinfo2:
            await server_call_async("GetVersion", None)
        assert "method" in str(excinfo1.value)
        assert "server" in str(excinfo2.value)

    @pytest.mark.asyncio
    @pytest.mark.skip("No longer times out")
    async def test_timeout(self):
        with pytest.raises(TimeoutException) as excinfo:
            await server_call_async("GetVersion", server="my36.geotab.com", timeout=0.01)
        assert "Request timed out @ my36.geotab.com" in str(excinfo.value)
