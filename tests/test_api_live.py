# -*- coding: utf-8 -*-

"""
Live API tests - only unauthenticated GetVersion calls.

These tests actually hit the MyGeotab API servers and require network access.
"""

import pytest

from mygeotab import api, server_call_async


class TestLiveServerCall:
    """Test unauthenticated server_call to live API."""

    def test_get_version(self):
        """Test GetVersion call using sync server_call."""
        version = api.server_call("GetVersion", server="my.geotab.com")
        version_split = version.split(".")
        assert len(version_split) == 3


class TestLiveServerCallAsync:
    """Test unauthenticated server_call_async to live API."""

    @pytest.mark.asyncio
    async def test_get_version(self):
        """Test GetVersion call using async server_call_async."""
        version = await server_call_async("GetVersion", server="my.geotab.com")
        version_split = version.split(".")
        assert len(version_split) == 3
