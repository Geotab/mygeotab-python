from datetime import date, datetime
from unittest.mock import patch

import pytest
import pytz

from mygeotab import dates
from mygeotab.serializers import json_serialize, json_deserialize, object_deserializer, object_serializer


class TestSerialization:
    def test_top_level_utc_datetime(self):
        data = dict(dateTime=datetime(2015, 6, 5, 2, 3, 44, 87000))
        expected_str = '{"dateTime":"2015-06-05T02:03:44.087Z"}'
        data_str = json_serialize(data)
        assert data_str == expected_str

    def test_top_level_zoned_datetime(self):
        est = pytz.timezone("US/Eastern")
        data = dict(dateTime=est.localize(datetime(2015, 6, 4, 3, 3, 43)))
        expected_str = '{"dateTime":"2015-06-04T07:03:43.000Z"}'
        data_str = json_serialize(data)
        assert data_str == expected_str

    def test_min_datetime(self):
        data = dict(dateTime=dates.MIN_DATE)
        expected_str = '{"dateTime":"0001-01-01T00:00:00.000Z"}'
        data_str = json_serialize(data)
        assert data_str == expected_str

    def test_max_datetime(self):
        data = dict(dateTime=dates.MAX_DATE)
        expected_str = '{"dateTime":"9999-12-31T23:59:59.999Z"}'
        data_str = json_serialize(data)
        assert data_str == expected_str

    def test_only_date(self):
        this_date = date(2016, 2, 22)
        data = dict(date=this_date)
        expected_str = '{"date":"2016-02-22"}'
        data_str = json_serialize(data)
        assert data_str == expected_str

    def test_unparsable_data_throws(self):
        with pytest.raises(TypeError):
            json_serialize({""})


class TestDeserialization:
    def test_top_level_datetime(self):
        data_str = '{"dateTime": "2015-06-04T07:03:43Z"}'
        data = json_deserialize(data_str)
        utc_date = data.get("dateTime")
        assert utc_date is not None
        check_date = datetime(2015, 6, 4, 7, 3, 43)
        assert utc_date.year == check_date.year
        assert utc_date.month == check_date.month
        assert utc_date.day == check_date.day
        assert utc_date.hour == check_date.hour
        assert utc_date.minute == check_date.minute
        assert utc_date.second == check_date.second

    def test_second_level_datetime(self):
        data_str = '[{"group": {"dateTime": "2015-06-04T07:03:43Z"}}]'
        data = json_deserialize(data_str)
        assert len(data) == 1
        group = data[0].get("group")
        assert group is not None
        utc_date = group.get("dateTime")
        assert utc_date is not None
        check_date = datetime(2015, 6, 4, 7, 3, 43)
        assert utc_date.year == check_date.year
        assert utc_date.month == check_date.month
        assert utc_date.day == check_date.day
        assert utc_date.hour == check_date.hour
        assert utc_date.minute == check_date.minute
        assert utc_date.second == check_date.second

    def test_invalid_datetime(self):
        date_str = "2015-06-0407T03:43Z"
        data_str = '{{"dateTime": "{}"}}'.format(date_str)
        data = json_deserialize(data_str)
        utc_date = data.get("dateTime")
        assert utc_date is not None
        assert utc_date == date_str

    def test_only_date(self):
        date_str = "0001-01-01"
        data_str = '{{"dateTime": "{}"}}'.format(date_str)
        data = json_deserialize(data_str)
        utc_date = data.get("dateTime")
        assert utc_date is not None
        check_date = datetime(1, 1, 1, 0, 0)
        assert utc_date.year == check_date.year
        assert utc_date.month == check_date.month
        assert utc_date.day == check_date.day


class TestObjectSerializer:
    def test_isoformat_object(self):
        dt = pytz.utc.localize(datetime(2024, 1, 15, 10, 30, 0))
        result = object_serializer(dt)
        assert result == "2024-01-15T10:30:00.000Z"


class TestObjectDeserializer:
    def test_converts_valid_datetime_string(self):
        obj = {"dateTime": "2024-01-15T10:30:00Z", "name": "test"}
        result = object_deserializer(obj)
        assert isinstance(result["dateTime"], datetime)
        assert result["name"] == "test"

    def test_keeps_invalid_datetime_string(self):
        obj = {"dateTime": "2024-13-45T99:99:99Z"}
        result = object_deserializer(obj)
        assert result["dateTime"] == "2024-13-45T99:99:99Z"

    def test_ignores_non_datetime_strings(self):
        obj = {"name": "hello", "count": 42}
        result = object_deserializer(obj)
        assert result["name"] == "hello"
        assert result["count"] == 42


class TestRapidjsonPaths:
    def test_serialize_with_rapidjson(self):
        data = {"key": "value", "num": 42}
        result = json_serialize(data)
        assert "key" in result
        assert "value" in result

    def test_deserialize_with_rapidjson(self):
        json_str = '{"dateTime": "2024-01-15T10:30:00Z", "name": "test"}'
        result = json_deserialize(json_str)
        assert result["name"] == "test"

    def test_serialize_without_rapidjson(self):
        with patch("mygeotab.serializers.use_rapidjson", False):
            data = {"key": "value", "num": 42}
            result = json_serialize(data)
            assert '"key"' in result
            assert '"value"' in result

    def test_deserialize_without_rapidjson(self):
        with patch("mygeotab.serializers.use_rapidjson", False):
            json_str = '{"dateTime": "2024-01-15T10:30:00Z", "name": "test"}'
            result = json_deserialize(json_str)
            assert result["name"] == "test"
            assert isinstance(result["dateTime"], datetime)
