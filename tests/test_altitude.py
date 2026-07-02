# -*- coding: utf-8 -*-

from mygeotab import api
from mygeotab.altitude.wrapper import AltitudeAPI, ALTITUDE_PROXY_SERVER

USERNAME = "test@example.com"
SESSION_ID = "abc123sessionid"
DATABASE = "testdatabase"


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
