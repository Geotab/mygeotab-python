# -*- coding: utf-8 -*-

from six.moves import UserList

from mygeotab.api import EntityList


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


def get_entitylist(type_name="Device", second_device_name="Test Device"):
    return EntityList([
        {"id": "NoDeviceId", "name": "**No Device"},
        {"id": "b123", "name": second_device_name},
        {"id": "b456", "name": "Another device"},
    ], type_name)

