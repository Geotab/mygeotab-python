from collections import UserList
from copy import copy
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
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


    def test_radd_with_userlist(self):
        el = get_entitylist()
        ul = UserList([{"id": "u1"}])
        combined = ul + el
        assert len(combined) == len(el) + 1
        assert isinstance(combined, EntityList)

    def test_radd_with_plain_list(self):
        el = get_entitylist()
        combined = [{"id": "x1"}] + el
        assert len(combined) == len(el) + 1
        assert isinstance(combined, EntityList)

    def test_add_with_plain_list(self):
        el = get_entitylist()
        combined = el + [{"id": "x1"}]
        assert len(combined) == len(el) + 1
        assert isinstance(combined, EntityList)

    def test_add_with_tuple(self):
        el = get_entitylist()
        combined = el + ({"id": "t1"},)
        assert len(combined) == len(el) + 1
        assert isinstance(combined, EntityList)

    def test_radd_with_tuple(self):
        el = get_entitylist()
        combined = ({"id": "t1"},) + el
        assert len(combined) == len(el) + 1
        assert isinstance(combined, EntityList)

    def test_mul(self):
        el = get_entitylist()
        result = el * 3
        assert len(result) == len(el) * 3
        assert result.type_name == "Device"

    def test_rmul(self):
        el = get_entitylist()
        result = 3 * el
        assert len(result) == len(el) * 3
        assert result.type_name == "Device"

    def test_copy(self):
        el = get_entitylist()
        el_copy = copy(el)
        assert len(el_copy) == len(el)
        assert el_copy.type_name == "Device"
        el_copy.data.append({"id": "new"})
        assert len(el_copy) == len(el) + 1

    def test_first_and_last_empty(self):
        el = EntityList([], "Device")
        assert el.first is None
        assert el.last is None

    def test_repr_pretty_cycle(self):
        el = get_entitylist()
        p = MagicMock()
        el._repr_pretty_(p, cycle=True)
        p.text.assert_called_once_with("Device(...)")

    def test_repr_pretty_no_cycle(self):
        el = get_entitylist()
        p = MagicMock()
        ctx = MagicMock()
        p.group.return_value.__enter__ = MagicMock(return_value=ctx)
        p.group.return_value.__exit__ = MagicMock(return_value=False)
        el._repr_pretty_(p, cycle=False)
        p.group.assert_called_once()

    def test_to_dataframe_no_pandas(self):
        el = get_entitylist()
        with patch.dict("sys.modules", {"pandas": None}):
            with pytest.raises(ImportError, match="pandas"):
                el.to_dataframe()


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
