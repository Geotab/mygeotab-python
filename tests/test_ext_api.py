"""Tests for the mygeotab.ext API subclass that returns EntityList results."""

from unittest.mock import AsyncMock, patch

import pytest

from mygeotab.ext.entitylist import API, EntityList


@pytest.fixture
def mock_query():
    with patch("mygeotab.api._query_async", new_callable=AsyncMock) as mock:
        yield mock


class TestExtApi:
    def test_get_returns_entitylist(self, mock_query):
        mock_query.side_effect = [
            {
                "path": "my3.geotab.com",
                "credentials": {
                    "userName": "test@example.com",
                    "sessionId": "abc123",
                    "database": "testdb",
                },
            },
            [{"id": "b1", "name": "Device 1"}, {"id": "b2", "name": "Device 2"}],
        ]
        ext_api = API("test@example.com", password="pass", database="testdb", server="my3.geotab.com")
        ext_api.authenticate()

        mock_query.return_value = [{"id": "b1", "name": "Device 1"}, {"id": "b2", "name": "Device 2"}]
        result = ext_api.get("Device")
        assert isinstance(result, EntityList)
        assert len(result) == 2
        assert result.type_name == "Device"
