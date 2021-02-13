# -*- coding: utf-8 -*-

import pytest

asyncio = pytest.importorskip("asyncio")
import os
import sys

from mygeotab import API, server_call_async
from mygeotab.exceptions import MyGeotabException, TimeoutException
from tests.test_api_call import SERVER, USERNAME, PASSWORD, DATABASE, TRAILER_NAME

ASYNC_TRAILER_NAME = "async {name}".format(name=TRAILER_NAME)

USERNAME = os.environ.get("MYGEOTAB_USERNAME_ASYNC", USERNAME)
PASSWORD = os.environ.get("MYGEOTAB_PASSWORD_ASYNC", PASSWORD)

pytestmark = pytest.mark.skipif(sys.version_info < (3, 5), reason="Only testing API on Python 3.5")


@pytest.fixture(scope="session")
def async_populated_api():
    if USERNAME and PASSWORD:
        session = API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        try:
            session.authenticate()
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
def async_populated_api_entity(async_populated_api):
    def clean_trailers():
        try:
            trailers = async_populated_api.get("Trailer", name=ASYNC_TRAILER_NAME)
            for trailer in trailers:
                async_populated_api.remove("Trailer", trailer)
        except Exception:
            pass

    clean_trailers()
    yield async_populated_api
    clean_trailers()


class TestAsyncCallApi:
    @pytest.mark.asyncio
    async def test_get_version(self, async_populated_api):
        version = await async_populated_api.call_async("GetVersion")
        version_split = version.split(".")
        assert len(version_split) == 4

    @pytest.mark.asyncio
    async def test_get_user(self, async_populated_api):
        user = await async_populated_api.get_async("User", name=USERNAME)
        assert len(user) == 1
        user = user[0]
        assert user["name"] == USERNAME

    @pytest.mark.asyncio
    async def test_multi_call(self, async_populated_api):
        calls = [["Get", dict(typeName="User", search=dict(name="{0}".format(USERNAME)))], ["GetVersion"]]
        results = await async_populated_api.multi_call_async(calls)
        assert len(results) == 2
        assert results[0] is not None
        assert len(results[0]) == 1
        assert results[0][0]["name"] == USERNAME
        assert results[1] is not None
        version_split = results[1].split(".")
        assert len(version_split) == 4

    @pytest.mark.asyncio
    async def test_pythonic_parameters(self, async_populated_api):
        users = async_populated_api.get("User")
        count_users = await async_populated_api.call_async("Get", type_name="User")
        assert len(count_users) >= 1
        assert len(count_users) == len(users)

    @pytest.mark.asyncio
    async def test_api_from_credentials(self, async_populated_api):
        new_api = API.from_credentials(async_populated_api.credentials)
        users = await new_api.get_async("User")
        assert len(users) >= 1

    @pytest.mark.asyncio
    async def test_results_limit(self, async_populated_api):
        users = await async_populated_api.get_async("User", resultsLimit=1)
        assert len(users) == 1

    @pytest.mark.asyncio
    async def test_session_expired(self, async_populated_api):
        credentials = async_populated_api.credentials
        credentials.password = PASSWORD
        credentials.session_id = "abc123"
        test_api = API.from_credentials(credentials)
        users = await test_api.get_async("User")
        assert len(users) >= 1

    @pytest.mark.asyncio
    async def test_missing_method(self, async_populated_api):
        with pytest.raises(Exception):
            await async_populated_api.call_async(None)

    @pytest.mark.asyncio
    async def test_call_without_credentials(self):
        new_api = API(USERNAME, password=PASSWORD, database=DATABASE, server=SERVER)
        user = await new_api.get_async("User", name="{0}".format(USERNAME))
        assert len(user) == 1

    @pytest.mark.asyncio
    async def test_bad_parameters(self, async_populated_api):
        with pytest.raises(MyGeotabException) as excinfo:
            await async_populated_api.call_async("NonExistentMethod", not_a_property="abc123")
        assert "NonExistentMethod" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_get_search_parameter(self, async_populated_api):
        user = await async_populated_api.get_async("User", search=dict(name=USERNAME))
        assert len(user) == 1
        user = user[0]
        assert user["name"] == USERNAME

    @pytest.mark.asyncio
    async def test_add_edit_remove(self, async_populated_api_entity):
        async def get_trailer():
            trailers = await async_populated_api_entity.get_async("Trailer", name=ASYNC_TRAILER_NAME)
            assert len(trailers) == 1
            return trailers[0]

        user = async_populated_api_entity.get("User", name=USERNAME)[0]
        trailer = {"name": ASYNC_TRAILER_NAME, "groups": user["companyGroups"]}
        trailer_id = await async_populated_api_entity.add_async("Trailer", trailer)
        trailer["id"] = trailer_id
        trailer = await get_trailer()
        assert trailer["name"] == ASYNC_TRAILER_NAME
        comment = "some comment"
        trailer["comment"] = comment
        await async_populated_api_entity.set_async("Trailer", trailer)
        trailer = await get_trailer()
        assert trailer["comment"] == comment
        await async_populated_api_entity.remove_async("Trailer", trailer)
        trailers = await async_populated_api_entity.get_async("Trailer", name=ASYNC_TRAILER_NAME)
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
    async def test_timeout(self):
        with pytest.raises(TimeoutException) as excinfo:
            await server_call_async("GetVersion", server="my36.geotab.com", timeout=0.01)
        assert "Request timed out @ my36.geotab.com" in str(excinfo.value)
