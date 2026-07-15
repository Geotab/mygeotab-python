# -*- coding: utf-8 -*-

"""
Tests for mygeotab.altitude.wrapper and mygeotab.altitude.daas_definition
server-override behaviour.
"""

from unittest.mock import MagicMock, call, patch

import pytest

from mygeotab import api
from mygeotab.altitude.daas_definition import (
    NOT_FULL_API_CALL_EXCEPTION,
    DaasGetJobStatusResult,
    DaasGetQueryResult,
)
from mygeotab.altitude.wrapper import ALTITUDE_PROXY_SERVER, AltitudeAPI

USERNAME = "test@example.com"
SESSION_ID = "abc123sessionid"
DATABASE = "testdatabase"


# ── Helpers ───────────────────────────────────────────────────────────────────


def make_altitude_api():
    return AltitudeAPI(USERNAME, session_id=SESSION_ID, database=DATABASE)


def make_status_call_result(state="DONE", error_result=None):
    job = {"id": "job-1", "status": {"state": state}}
    if error_result:
        job["status"]["errorResult"] = error_result
    return {
        "errors": [],
        "apiResult": {"results": [job], "errors": [], "errorMessage": None},
    }


def make_query_call_result(rows=None, page_token=None, total_rows=None):
    job = {"id": "job-1"}
    if rows is not None:
        job["rows"] = rows
    if page_token is not None:
        job["pageToken"] = page_token
    if total_rows is not None:
        job["totalRows"] = total_rows
    return {
        "errors": [],
        "apiResult": {"results": [job], "errors": [], "errorMessage": None},
    }


# ── Server override ───────────────────────────────────────────────────────────


class TestAltitudeServer:
    def test_default_server_is_proxy(self):
        altitude_api = AltitudeAPI(USERNAME, session_id=SESSION_ID, database=DATABASE)
        assert altitude_api._server == ALTITUDE_PROXY_SERVER

    def test_passed_server_is_overridden(self):
        altitude_api = AltitudeAPI(
            USERNAME, session_id=SESSION_ID, database=DATABASE, server="my3.geotab.com"
        )
        assert altitude_api._server == ALTITUDE_PROXY_SERVER

    def test_resolved_url_is_proxy_verbatim(self):
        altitude_api = AltitudeAPI(USERNAME, session_id=SESSION_ID, database=DATABASE)
        assert api.get_api_url(altitude_api._server) == ALTITUDE_PROXY_SERVER


# ── _extract_errors ───────────────────────────────────────────────────────────


class TestExtractErrors:
    def test_top_level_errors_returned(self):
        alt = make_altitude_api()
        resp = {"errors": [{"message": "top-level error"}], "apiResult": {}}
        errors = alt._extract_errors(resp)
        assert len(errors) == 1
        assert errors[0]["message"] == "top-level error"

    def test_api_result_errors_returned_when_top_level_empty(self):
        alt = make_altitude_api()
        resp = {"errors": [], "apiResult": {"errors": [{"message": "inner error"}]}}
        errors = alt._extract_errors(resp)
        assert len(errors) == 1
        assert errors[0]["message"] == "inner error"

    def test_empty_when_no_errors(self):
        alt = make_altitude_api()
        resp = {"errors": [], "apiResult": {"errors": []}}
        assert alt._extract_errors(resp) == []

    def test_top_level_takes_priority_over_api_result(self):
        """If top-level errors is non-empty, apiResult errors are not returned (or operator)."""
        alt = make_altitude_api()
        resp = {
            "errors": [{"message": "top"}],
            "apiResult": {"errors": [{"message": "inner"}]},
        }
        errors = alt._extract_errors(resp)
        # The `or` means only top-level is returned when it is truthy
        assert len(errors) == 1
        assert errors[0]["message"] == "top"


# ── call_api ──────────────────────────────────────────────────────────────────


class TestCallApi:
    def test_success_returns_result(self):
        alt = make_altitude_api()
        expected = make_status_call_result("DONE")
        with patch.object(alt, "_call_api", return_value=expected):
            result = alt.call_api(
                "getJobStatus",
                {"serviceName": "svc", "functionParameters": {"jobId": "j1"}},
            )
        assert result is expected

    def test_invalid_function_name_raises(self):
        alt = make_altitude_api()
        with pytest.raises(AssertionError):
            alt.call_api(
                "unknownMethod",
                {"serviceName": "svc", "functionParameters": {}},
            )

    def test_valid_function_names_accepted(self):
        alt = make_altitude_api()
        for name in ["getJobStatus", "getQueryResults", "createQueryJob"]:
            with patch.object(alt, "_call_api", return_value=make_status_call_result()):
                result = alt.call_api(name, {"serviceName": "s", "functionParameters": {}})
            assert result is not None

    def test_non_retry_exception_re_raised_immediately(self):
        """Exceptions that are not NOT_FULL_API_CALL_EXCEPTION must propagate instantly."""
        alt = make_altitude_api()
        with patch.object(alt, "_call_api", side_effect=ValueError("network error")):
            with pytest.raises(ValueError, match="network error"):
                alt.call_api("getJobStatus", {"serviceName": "s", "functionParameters": {}})


# ── create_job ────────────────────────────────────────────────────────────────


class TestCreateJob:
    def _make_create_job_result(self, job_id="job-abc"):
        return {
            "errors": [],
            "apiResult": {
                "results": [{"id": job_id}],
                "errors": [],
                "errorMessage": None,
            },
        }

    def test_returns_first_result_on_success(self):
        alt = make_altitude_api()
        with patch.object(alt, "call_api", return_value=self._make_create_job_result("job-abc")):
            job = alt.create_job({"serviceName": "s", "functionParameters": {}})
        assert job["id"] == "job-abc"

    def test_raises_when_errors_present(self):
        alt = make_altitude_api()
        mock_result = {
            "errors": [{"message": "quota exceeded"}],
            "apiResult": {"results": [], "errors": [], "errorMessage": None},
        }
        with patch.object(alt, "call_api", return_value=mock_result):
            with pytest.raises(Exception, match="quota exceeded"):
                alt.create_job({"serviceName": "s", "functionParameters": {}})

    def test_re_raises_call_api_exception(self):
        alt = make_altitude_api()
        with patch.object(alt, "call_api", side_effect=RuntimeError("connection reset")):
            with pytest.raises(RuntimeError, match="connection reset"):
                alt.create_job({"serviceName": "s", "functionParameters": {}})


# ── check_job_status ──────────────────────────────────────────────────────────


class TestCheckJobStatus:
    def test_returns_daas_get_job_status_result(self):
        alt = make_altitude_api()
        with patch.object(alt, "call_api", return_value=make_status_call_result("DONE")):
            result = alt.check_job_status({"serviceName": "s", "functionParameters": {"jobId": "j1"}})
        assert isinstance(result, DaasGetJobStatusResult)
        assert result.state == "DONE"


# ── wait_for_job_to_complete ──────────────────────────────────────────────────


class TestWaitForJobToComplete:
    def test_returns_job_when_done_immediately(self):
        alt = make_altitude_api()
        done_status = DaasGetJobStatusResult(make_status_call_result("DONE"))
        with patch.object(alt, "check_job_status", return_value=done_status):
            with patch("time.sleep"):
                job = alt.wait_for_job_to_complete(
                    {"serviceName": "s", "functionParameters": {"jobId": "j1"}}
                )
        assert job["id"] == "job-1"

    def test_polls_until_done(self):
        alt = make_altitude_api()
        running = DaasGetJobStatusResult(make_status_call_result("RUNNING"))
        done = DaasGetJobStatusResult(make_status_call_result("DONE"))
        with patch.object(alt, "check_job_status", side_effect=[running, running, done]):
            with patch("time.sleep"):
                job = alt.wait_for_job_to_complete(
                    {"serviceName": "s", "functionParameters": {"jobId": "j1"}}
                )
        assert job["id"] == "job-1"

    def test_raises_when_status_has_errors(self):
        alt = make_altitude_api()
        error_result = {"code": 500, "location": "svc", "message": "crashed"}
        failed_status = DaasGetJobStatusResult(
            make_status_call_result("DONE", error_result=error_result)
        )
        with patch.object(alt, "check_job_status", return_value=failed_status):
            with patch("time.sleep"):
                with pytest.raises(Exception):
                    alt.wait_for_job_to_complete(
                        {"serviceName": "s", "functionParameters": {"jobId": "j1"}}
                    )


# ── fetch_data ────────────────────────────────────────────────────────────────


class TestFetchData:
    def test_single_page_no_page_token(self):
        alt = make_altitude_api()
        done_status = DaasGetJobStatusResult(make_status_call_result("DONE"))
        page = make_query_call_result(rows=[{"a": 1}], total_rows=1, page_token=None)

        with patch.object(alt, "check_job_status", return_value=done_status):
            with patch.object(alt, "call_api", return_value=page):
                pages = list(alt.fetch_data({"serviceName": "s", "functionParameters": {"jobId": "j1"}}))

        # Generator yields one data page then a final None sentinel
        assert pages[0] is not None
        assert pages[0]["data"][0] == [{"a": 1}]
        assert pages[1] is None  # sentinel

    def test_raises_before_job_finished(self):
        alt = make_altitude_api()
        running_status = DaasGetJobStatusResult(make_status_call_result("RUNNING"))
        with patch.object(alt, "check_job_status", return_value=running_status):
            with pytest.raises(Exception, match="before job had finished"):
                list(alt.fetch_data({"serviceName": "s", "functionParameters": {"jobId": "j1"}}))

    def test_multi_page_follows_page_token(self):
        alt = make_altitude_api()
        done_status = DaasGetJobStatusResult(make_status_call_result("DONE"))
        page1 = make_query_call_result(rows=[{"a": 1}], total_rows=2, page_token="tok2")
        page2 = make_query_call_result(rows=[{"a": 2}], total_rows=2, page_token=None)

        with patch.object(alt, "check_job_status", return_value=done_status):
            with patch.object(alt, "call_api", side_effect=[page1, page2]):
                pages = list(alt.fetch_data({"serviceName": "s", "functionParameters": {"jobId": "j1"}}))

        data_pages = [p for p in pages if p is not None]
        assert len(data_pages) == 2
        assert data_pages[0]["data"][0] == [{"a": 1}]
        assert data_pages[1]["data"][0] == [{"a": 2}]


# ── get_data ──────────────────────────────────────────────────────────────────


class TestGetData:
    def test_combines_pages_into_flat_list(self):
        alt = make_altitude_api()
        done_status = DaasGetJobStatusResult(make_status_call_result("DONE"))
        page1 = make_query_call_result(rows=[{"a": 1}], total_rows=2, page_token="tok2")
        page2 = make_query_call_result(rows=[{"a": 2}], total_rows=2, page_token=None)

        with patch.object(alt, "check_job_status", return_value=done_status):
            with patch.object(alt, "call_api", side_effect=[page1, page2]):
                data = alt.get_data({"serviceName": "s", "functionParameters": {"jobId": "j1"}})

        assert data == [{"a": 1}, {"a": 2}]

    def test_empty_result_returns_empty_list(self):
        alt = make_altitude_api()
        done_status = DaasGetJobStatusResult(make_status_call_result("DONE"))
        page = make_query_call_result(rows=[], total_rows=0, page_token=None)

        with patch.object(alt, "check_job_status", return_value=done_status):
            with patch.object(alt, "call_api", return_value=page):
                data = alt.get_data({"serviceName": "s", "functionParameters": {"jobId": "j1"}})

        assert data == []


# ── do ────────────────────────────────────────────────────────────────────────


class TestDo:
    def test_orchestrates_create_wait_fetch(self):
        alt = make_altitude_api()
        params = {"serviceName": "svc", "functionParameters": {}}

        with patch.object(alt, "create_job", return_value={"id": "job-xyz"}) as mock_create:
            with patch.object(alt, "wait_for_job_to_complete", return_value={"id": "job-xyz"}) as mock_wait:
                with patch.object(alt, "get_data", return_value=[{"row": 1}]) as mock_get:
                    result = alt.do(params)

        assert result == [{"row": 1}]
        mock_create.assert_called_once_with(params)
        # jobId must have been injected into functionParameters before wait
        assert params["functionParameters"]["jobId"] == "job-xyz"
        mock_wait.assert_called_once_with(params)
        mock_get.assert_called_once_with(params)
