import pytest
from aioresponses import aioresponses

from mygeotab import api, serializers


@pytest.fixture(scope="session")
def mock_api():
    username = "mockuser"
    session_id = 1234
    database = "testdb"

    yield api.API(username, database=database, session_id=session_id, server="https://example.com")


@pytest.mark.skip("Too slow to run automatically")
class TestApiPerformance:
    def test_timeout_large_json_rapidjson(self, mock_api, datadir, benchmark):
        server = "https://example.com/apiv1"
        json_response = (datadir / "big_nested_date_response.json").read_text()

        mock_api.timeout = 0.0001

        with aioresponses() as m:
            m.post(server, body=json_response, content_type="application/json")

            benchmark(mock_api.get, "Data")

    def test_timeout_large_json(self, mock_api, datadir, benchmark, monkeypatch):
        server = "https://example.com/apiv1"
        json_response = (datadir / "big_nested_date_response.json").read_text()

        mock_api.timeout = 0.0001

        with aioresponses() as m:
            m.post(server, body=json_response, content_type="application/json")

            monkeypatch.setattr(serializers, "use_rapidjson", False)

            benchmark(mock_api.get, "Data")
