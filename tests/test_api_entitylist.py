# -*- coding: utf-8 -*-

from datetime import datetime

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
        dataframe = entitylist.to_dataframe()
        assert len(dataframe) == 3
        dataframe = entitylist.to_dataframe(True)
        assert len(dataframe) == 3
        assert int(dataframe["location.x"][-1:]) == 123


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
