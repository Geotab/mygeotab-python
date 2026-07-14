# -*- coding: utf-8 -*-

import copy
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from mygeotab.ext.entitylist import API as EntityListAPI
from mygeotab.ext.entitylist import EntityList


class TestEntityList:
    def test_create(self):
        type_name = "Device"
        entitylist = get_entitylist(type_name)
        assert entitylist.type_name == type_name

    def test_get(self):
        entity_name = "Test Device 2"
        entitylist = get_entitylist(second_device_name=entity_name)
        assert entitylist[1]["name"] == entity_name

    def test_get_slice(self):
        entity_name = "Test Device 2"
        entitylist = get_entitylist(second_device_name=entity_name)
        sliced_entitylist = entitylist[1:]
        assert sliced_entitylist[0]["name"] == entity_name
        assert sliced_entitylist.type_name == "Device"

    def test_add_entitylist(self):
        entitylist1 = get_entitylist()
        entitylist2 = get_entitylist()
        combined_entitylist = entitylist1 + entitylist2
        assert len(combined_entitylist) == len(entitylist1) + len(entitylist2)
        assert combined_entitylist.type_name == "Device"

    def test_sort_id(self):
        entitylist = get_entitylist()
        sorted_by_id = entitylist.sort_by("id")
        assert sorted_by_id[0]["id"] == "b456"
        assert sorted_by_id[-1]["id"] == "NoDeviceId"

    def test_sort_id_reverse(self):
        entitylist = get_entitylist()
        sorted_by_id = entitylist.sort_by("id", True)
        assert sorted_by_id[0]["id"] == "NoDeviceId"
        assert sorted_by_id[-1]["id"] == "b456"

    def test_sort_datetime(self):
        entitylist = get_entitylist()
        sorted_by_id = entitylist.sort_by("dateTime")
        assert sorted_by_id[0]["dateTime"] == datetime(2019, 2, 22, 23, 13, 32)
        assert sorted_by_id[-1]["dateTime"] == datetime(2019, 10, 22, 9, 19, 3)

    def test_sort_odometer(self):
        entitylist = get_entitylist()
        sorted_by_id = entitylist.sort_by("odometer")
        assert sorted_by_id[0]["odometer"] == 3303.0
        assert sorted_by_id[-1]["odometer"] == 20333.0

    def test_first_and_last(self):
        entitylist = get_entitylist()
        assert entitylist.first["id"] == "NoDeviceId"
        assert entitylist.last["id"] == "b456"

    def test_single_entity(self):
        entitylist = get_entitylist()
        with pytest.raises(AssertionError):
            assert entitylist.entity["id"] == "NoDeviceId"
        sub_entitylist = entitylist[0:1]
        assert sub_entitylist.entity["id"] == "NoDeviceId"

    def test_to_dataframe(self):
        entitylist = get_entitylist()
        
        # Mock pandas DataFrame
        mock_dataframe = MagicMock()
        mock_dataframe.__len__ = MagicMock(return_value=3)
        mock_dataframe.__getitem__ = MagicMock(return_value=MagicMock(__getitem__=lambda self, key: 123))
        
        # Create mock pandas module
        mock_pandas = MagicMock()
        mock_pandas.DataFrame.from_dict.return_value = mock_dataframe
        mock_pandas.json_normalize.return_value = mock_dataframe
        
        with patch.dict('sys.modules', {'pandas': mock_pandas}):
            dataframe = entitylist.to_dataframe()
            assert len(dataframe) == 3
            mock_pandas.DataFrame.from_dict.assert_called_once()
            
            dataframe = entitylist.to_dataframe(True)
            assert len(dataframe) == 3
            mock_pandas.json_normalize.assert_called_once()
            assert int(dataframe["location.x"][-1:]) == 123


class TestEntityListEdgeCases:
    """Cover branches missed by the original test suite."""

    # ── first / last on empty list ───────────────────────────────────────────

    def test_first_empty_returns_none(self):
        assert EntityList([], "Device").first is None

    def test_last_empty_returns_none(self):
        assert EntityList([], "Device").last is None

    # ── entity with zero items ───────────────────────────────────────────────

    def test_entity_zero_items_raises(self):
        with pytest.raises(AssertionError, match="0 entities"):
            EntityList([], "Device").entity

    # ── __add__ with plain list ──────────────────────────────────────────────

    def test_add_plain_list(self):
        el = EntityList([{"id": "a"}], "Device")
        result = el + [{"id": "b"}]
        assert len(result) == 2
        assert isinstance(result, EntityList)
        assert result.type_name == "Device"

    # ── __radd__ with plain list ─────────────────────────────────────────────

    def test_radd_plain_list(self):
        el = EntityList([{"id": "a"}], "Device")
        result = [{"id": "b"}] + el
        assert len(result) == 2
        assert isinstance(result, EntityList)
        assert result.type_name == "Device"

    # ── __mul__ / __rmul__ ───────────────────────────────────────────────────

    def test_mul(self):
        el = EntityList([{"id": "a"}], "Device")
        result = el * 3
        assert len(result) == 3
        assert isinstance(result, EntityList)
        assert result.type_name == "Device"

    def test_rmul(self):
        el = EntityList([{"id": "a"}], "Device")
        result = 3 * el
        assert len(result) == 3
        assert isinstance(result, EntityList)
        assert result.type_name == "Device"

    # ── __copy__ ─────────────────────────────────────────────────────────────

    def test_copy(self):
        el = EntityList([{"id": "a"}], "Device")
        el2 = copy.copy(el)
        assert el2.type_name == el.type_name
        assert el2.data == el.data
        assert el2.data is not el.data  # independent copy

    # ── to_dataframe — ImportError when pandas not installed ────────────────

    def test_to_dataframe_raises_import_error_when_no_pandas(self):
        el = EntityList([{"id": "b1"}], "Device")
        # Simulate pandas being absent
        with patch.dict(sys.modules, {"pandas": None}):
            with pytest.raises(ImportError, match="pandas"):
                el.to_dataframe()

    # ── EntityList.API.get returns EntityList ────────────────────────────────

    def test_entitylist_api_get_returns_entity_list(self):
        """ext.entitylist.API.get() must wrap the raw result in an EntityList."""
        with patch("mygeotab.api._query") as mock_query:
            # First call: authenticate
            mock_query.return_value = {
                "path": "my3.geotab.com",
                "credentials": {
                    "userName": "test@example.com",
                    "sessionId": "sid123",
                    "database": "db",
                },
            }
            el_api = EntityListAPI(
                "test@example.com",
                password="pw",
                database="db",
                server="my3.geotab.com",
            )
            el_api.authenticate()

            # Second call: get
            mock_query.return_value = [{"id": "b1", "name": "Device A"}]
            result = el_api.get("Device")

        assert isinstance(result, EntityList)
        assert result.type_name == "Device"
        assert result[0]["id"] == "b1"


def get_entitylist(type_name="Device", second_device_name="Test Device"):
    return EntityList(
        [
            {
                "id": "NoDeviceId",
                "dateTime": datetime(2019, 5, 22, 2, 25, 33),
                "odometer": 3303.0,
                "name": "**No Device",
            },
            {
                "id": "b823",
                "dateTime": datetime(2019, 2, 22, 23, 13, 32),
                "odometer": 20333.0,
                "name": second_device_name,
            },
            {
                "id": "b456",
                "dateTime": datetime(2019, 10, 22, 9, 19, 3),
                "odometer": 6032.0,
                "name": "Another device",
                "location": {"x": 123, "y": 456},
            },
        ],
        type_name,
    )
