# -*- coding: utf-8 -*-

import pytest

from mygeotab import api


class TestAttributes:
    def test_should_verify_ssl(self):
        my_api = api.API("test@example.com", session_id=123, server="my3.geotab.com")
        assert my_api._is_verify_ssl is True
        my_api = api.API("test@example.com", session_id=123, server="127.0.0.1")
        assert my_api._is_verify_ssl is False
        my_api = api.API("test@example.com", session_id=123, server="localhost")
        assert my_api._is_verify_ssl is False


class TestProcessParameters:
    def test_camel_case_transformer(self):
        params = dict(search=dict(device_search=dict(id=123), include_overlapped_trips=True))
        fixed_params = api.process_parameters(params)
        assert fixed_params is not None
        assert "search" in fixed_params
        assert "deviceSearch" in fixed_params["search"]
        assert "id" in fixed_params["search"]["deviceSearch"]
        assert fixed_params["search"]["deviceSearch"]["id"] == 123
        assert "includeOverlappedTrips" in fixed_params["search"]
        assert fixed_params["search"]["includeOverlappedTrips"]


class TestProcessResults:
    def test_handle_server_exception(self):
        exception_response = dict(
            error=dict(
                errors=[
                    dict(
                        message=(
                            'The method "Get" could not be found. Verify the method name and ensure all method '
                            'parameters are included. Request Json: {"params": {"typeName": "Passwords", '
                            '"credentials": {"userName": "test@example.com", "sessionId": "12345678901234567890", '
                            '"database": "my_company"}}, "method": "Get", "id": -1}'
                        ),
                        name="MissingMethodException",
                        stackTrace=(
                            "   at Geotab.Checkmate.Web.APIV1.ProcessRequest(IHttpRequest httpRequest, HttpResponse "
                            "httpResponse, String methodName, Dictionary`2 parameters, "
                            "Action`2 parametersJSONToTokens, Action`1 handleException, IProfiler profile, Credentials "
                            "credentials, Int32 requestIndex, Object requestJsonOrHashMap, Boolean& isAsync) in "
                            "c:\\ProgramData\\GEOTAB\\Checkmate\\BuildServer\\master\\WorkingDirectory\\Checkmate\\"
                            " CheckmateServer\\Geotab\\Checkmate\\Web\\APIV1.cs:line 813\r\n   "
                            "at Geotab.Checkmate.Web.APIV1.<>c__DisplayClass13.<ProcessRequest>b__b() "
                            "in c:\\ProgramData\\GEOTAB\\Checkmate\\BuildServer\\master\\WorkingDirectory\\Checkmate\\"
                            "CheckmateServer\\Geotab\\Checkmate\\Web\\APIV1.cs:line 558\r\n   "
                            "at Geotab.Checkmate.Web.APIV1.ExecuteHandleException(Action action) in "
                            "c:\\ProgramData\\GEOTAB\\Checkmate\\BuildServer\\master\\WorkingDirectory\\Checkmate\\"
                            "CheckmateServer\\Geotab\\Checkmate\\Web\\APIV1.cs:line 632"
                        ),
                    )
                ],
                message=(
                    'The method "Get" could not be found. Verify the method name and ensure all method parameters are '
                    'included. Request Json: {"params": {"typeName": "Passwords", "credentials": {"userName": '
                    '"test@example.com", "sessionId": "12345678901234567890", "database": "my_company"}}, "method": '
                    '"Get", "id": -1}'
                ),
                name="JSONRPCError",
            ),
            requestIndex=0,
        )
        with pytest.raises(api.MyGeotabException) as excinfo:
            api._process(exception_response)
        ex = excinfo.value
        assert ex.name == "MissingMethodException"
        assert ex.message == (
            'The method "Get" could not be found. Verify the method name and ensure all method '
            'parameters are included. Request Json: {"params": {"typeName": "Passwords", '
            '"credentials": {"userName": "test@example.com", "sessionId": "12345678901234567890", '
            '"database": "my_company"}}, "method": "Get", "id": -1}'
        )

    def test_handle_server_results(self):
        results_response = {"result": [dict(id="b123", name="test@example.com")]}
        result = api._process(results_response)
        assert len(result) == 1
        assert result[0]["name"] == "test@example.com"
        assert result[0]["id"] == "b123"

    def test_handle_none(self):
        result = api._process(None)
        assert result is None
