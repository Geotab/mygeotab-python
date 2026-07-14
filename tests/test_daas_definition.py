# -*- coding: utf-8 -*-

"""
Tests for mygeotab.altitude.daas_definition.

This module was previously at 0 % coverage. These tests exercise every
class and every branch in daas_definition.py.
"""

import pytest

from mygeotab.altitude.daas_definition import (
    NOT_FULL_API_CALL_EXCEPTION,
    DaasError,
    DaasGetJobStatusResult,
    DaasGetQueryResult,
    DaasResult,
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def make_job_status_call_result(
    state="DONE",
    error_result=None,
    gateway_errors=None,
    api_result_errors=None,
    error_message=None,
):
    """Build a minimal valid call_result dict for DaasGetJobStatusResult."""
    job = {"id": "job-1", "status": {"state": state}}
    if error_result:
        job["status"]["errorResult"] = error_result
    return {
        "errors": gateway_errors or [],
        "apiResult": {
            "results": [job],
            "errors": api_result_errors or [],
            "errorMessage": error_message,
        },
    }


def make_query_call_result(rows=None, total_rows=None, page_token=None):
    """Build a minimal valid call_result dict for DaasGetQueryResult."""
    job = {"id": "job-1"}
    if rows is not None:
        job["rows"] = rows
    if total_rows is not None:
        job["totalRows"] = total_rows
    if page_token is not None:
        job["pageToken"] = page_token
    return {
        "errors": [],
        "apiResult": {
            "results": [job],
            "errors": [],
            "errorMessage": None,
        },
    }


# ── DaasError ─────────────────────────────────────────────────────────────────


class TestDaasError:
    def test_fields_populated(self):
        err = DaasError({"code": 404, "domain": "altitude", "message": "not found"})
        assert err.code == 404
        assert err.domain == "altitude"
        assert err.message == "not found"

    def test_raw_error_dict_stored(self):
        raw = {"code": 500, "domain": "gateway", "message": "internal error"}
        err = DaasError(raw)
        assert err.error is raw


# ── DaasResult ────────────────────────────────────────────────────────────────


class TestDaasResult:
    # ── Guard: empty / missing call_result ──────────────────────────────────

    def test_none_call_result_raises(self):
        with pytest.raises(Exception) as exc_info:
            DaasResult(None)
        assert exc_info.value is NOT_FULL_API_CALL_EXCEPTION

    def test_empty_dict_raises(self):
        with pytest.raises(Exception) as exc_info:
            DaasResult({})
        assert exc_info.value is NOT_FULL_API_CALL_EXCEPTION

    def test_missing_api_result_key_raises(self):
        with pytest.raises(Exception) as exc_info:
            DaasResult({"errors": []})
        assert exc_info.value is NOT_FULL_API_CALL_EXCEPTION

    # ── Happy path ──────────────────────────────────────────────────────────

    def test_normal_call_result_sets_attributes(self):
        call_result = make_job_status_call_result()
        result = DaasResult(call_result)
        assert result.call_result is call_result
        assert result.api_result is call_result["apiResult"]
        assert result.jobs == call_result["apiResult"]["results"]
        assert result.job == call_result["apiResult"]["results"][0]
        assert len(result.errors) == 0
        assert result.api_result_error is None

    # ── Gateway-level errors ─────────────────────────────────────────────────

    def test_gateway_errors_populate_daas_errors_and_errors(self):
        call_result = make_job_status_call_result(
            gateway_errors=[{"code": 500, "domain": "gw", "message": "gateway error"}]
        )
        result = DaasResult(call_result)
        assert len(result.daas_errors) == 1
        assert result.daas_errors[0].message == "gateway error"
        assert len(result.errors) == 1
        assert "gateway error" in str(result.errors[0])

    # ── apiResult-level errors ───────────────────────────────────────────────

    def test_api_result_errors_list_populated(self):
        call_result = make_job_status_call_result(
            api_result_errors=[{"code": 400, "domain": "altitude", "message": "bad input"}]
        )
        result = DaasResult(call_result)
        assert len(result.api_result_errors) == 1
        assert len(result.errors) == 1
        assert "bad input" in str(result.errors[0])

    def test_api_result_single_error_field(self):
        """The "error" (singular) key in apiResult creates api_result_error."""
        call_result = make_job_status_call_result()
        call_result["apiResult"]["error"] = {"code": 403, "domain": "altitude", "message": "forbidden"}
        result = DaasResult(call_result)
        assert result.api_result_error is not None
        assert result.api_result_error.code == 403
        assert any("forbidden" in str(e) for e in result.errors)

    def test_api_result_error_field_falsy_is_ignored(self):
        """An "error" key that is falsy (empty dict, None) must not be parsed."""
        call_result = make_job_status_call_result()
        call_result["apiResult"]["error"] = None
        result = DaasResult(call_result)
        assert result.api_result_error is None
        assert len(result.errors) == 0

    # ── errorMessage variants ────────────────────────────────────────────────

    def test_error_message_string(self):
        call_result = make_job_status_call_result(error_message="Something went wrong")
        result = DaasResult(call_result)
        assert any("Something went wrong" in str(e) for e in result.errors)

    def test_error_message_dict(self):
        call_result = make_job_status_call_result(
            error_message={"message": "Dict error occurred"}
        )
        result = DaasResult(call_result)
        assert any("Dict error occurred" in str(e) for e in result.errors)

    def test_empty_string_error_message_not_appended(self):
        call_result = make_job_status_call_result(error_message="")
        result = DaasResult(call_result)
        assert len(result.errors) == 0

    def test_none_error_message_not_appended(self):
        call_result = make_job_status_call_result(error_message=None)
        result = DaasResult(call_result)
        assert len(result.errors) == 0


# ── DaasGetJobStatusResult ────────────────────────────────────────────────────


class TestDaasGetJobStatusResult:
    # ── State transitions ────────────────────────────────────────────────────

    def test_done_state(self):
        result = DaasGetJobStatusResult(make_job_status_call_result("DONE"))
        assert result.id == "job-1"
        assert result.state == "DONE"

    def test_running_state(self):
        result = DaasGetJobStatusResult(make_job_status_call_result("RUNNING"))
        assert result.state == "RUNNING"

    def test_failed_state_with_error_result_overrides_state(self):
        """errorResult in the status dict must force state to FAILED."""
        error_result = {"code": 500, "location": "svc", "message": "job crashed"}
        result = DaasGetJobStatusResult(
            make_job_status_call_result("DONE", error_result=error_result)
        )
        assert result.state == "FAILED"
        assert result.api_result_error is not None
        assert result.api_result_error.message == "job crashed"
        assert len(result.errors) >= 1

    def test_missing_status_key_defaults_to_failed(self):
        """A job dict without a 'status' key must default state to FAILED."""
        call_result = {
            "errors": [],
            "apiResult": {
                "results": [{"id": "job-2"}],
                "errors": [],
                "errorMessage": None,
            },
        }
        result = DaasGetJobStatusResult(call_result)
        assert result.state == "FAILED"

    # ── has_finished() ────────────────────────────────────────────────────────

    def test_has_finished_done_returns_true(self):
        result = DaasGetJobStatusResult(make_job_status_call_result("DONE"))
        assert result.has_finished() is True

    def test_has_finished_running_returns_false(self):
        result = DaasGetJobStatusResult(make_job_status_call_result("RUNNING"))
        assert result.has_finished() is False

    def test_has_finished_failed_with_errors_returns_false(self):
        """FAILED state with errors present → has_finished() returns False."""
        error_result = {"code": 500, "location": "svc", "message": "crashed"}
        result = DaasGetJobStatusResult(
            make_job_status_call_result("DONE", error_result=error_result)
        )
        assert result.state == "FAILED"
        assert result.has_finished() is False

    def test_has_finished_failed_no_errors_raises(self):
        """FAILED state with no errors is an unexpected condition → raises."""
        result = DaasGetJobStatusResult(make_job_status_call_result("FAILED"))
        # Manually clear errors to trigger the unhandled-failure branch.
        result.errors = []
        with pytest.raises(Exception, match="got to failed state with no error"):
            result.has_finished()


# ── DaasGetQueryResult ────────────────────────────────────────────────────────


class TestDaasGetQueryResult:
    def test_all_fields_present(self):
        result = DaasGetQueryResult(
            make_query_call_result(rows=[{"col": "val"}], total_rows=42, page_token="tok123")
        )
        assert result.total_rows == 42
        assert result.rows == [{"col": "val"}]
        assert result.page_token == "tok123"

    def test_fields_absent_return_none(self):
        """Missing optional fields must default to None."""
        result = DaasGetQueryResult(make_query_call_result())
        assert result.total_rows is None
        assert result.rows is None
        assert result.page_token is None

    def test_empty_rows_and_zero_total(self):
        result = DaasGetQueryResult(make_query_call_result(rows=[], total_rows=0))
        assert result.total_rows == 0
        assert result.rows == []

    def test_inherits_from_daas_result(self):
        result = DaasGetQueryResult(make_query_call_result(rows=[], total_rows=5))
        assert isinstance(result, DaasResult)
