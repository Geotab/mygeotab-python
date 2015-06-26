# -*- coding: utf-8 -*-

import unittest
import json
from datetime import datetime

import pytz

from mygeotab import serializers


def json_serialize(data):
    return json.dumps(data, default=serializers.object_serializer)


def json_deserialize(data_str):
    return json.loads(data_str, object_hook=serializers.object_deserializer)


class TestSerialization(unittest.TestCase):
    def setUp(self):
        pass

    def test_top_level_utc_datetime(self):
        data = dict(
            dateTime=datetime(2015, 6, 5, 2, 3, 44)
        )
        expected_str = '{"dateTime": "2015-06-05T02:03:44Z"}'
        data_str = json_serialize(data)
        self.assertEqual(data_str, expected_str)

    def test_top_level_zoned_datetime(self):
        est = pytz.timezone('US/Eastern')
        data = dict(
            dateTime=est.localize(datetime(2015, 6, 4, 3, 3, 43))
        )
        expected_str = '{"dateTime": "2015-06-04T07:03:43Z"}'
        data_str = json_serialize(data)
        self.assertEqual(data_str, expected_str)


class TestDeserialization(unittest.TestCase):
    def setUp(self):
        pass

    def test_top_level_datetime(self):
        data_str = '{"dateTime": "2015-06-04T07:03:43Z"}'
        data = json_deserialize(data_str)
        utc_date = data.get('dateTime')
        self.assertIsNotNone(utc_date)
        check_date = datetime(2015, 6, 4, 7, 3, 43)
        self.assertEqual(utc_date.year, check_date.year)
        self.assertEqual(utc_date.month, check_date.month)
        self.assertEqual(utc_date.day, check_date.day)
        self.assertEqual(utc_date.hour, check_date.hour)
        self.assertEqual(utc_date.minute, check_date.minute)
        self.assertEqual(utc_date.second, check_date.second)

    def test_second_level_datetime(self):
        data_str = '[{"group": {"dateTime": "2015-06-04T07:03:43Z"}}]'
        data = json_deserialize(data_str)
        self.assertEqual(len(data), 1)
        group = data[0].get('group')
        self.assertIsNotNone(group)
        utc_date = group.get('dateTime')
        self.assertIsNotNone(utc_date)
        check_date = datetime(2015, 6, 4, 7, 3, 43)
        self.assertEqual(utc_date.year, check_date.year)
        self.assertEqual(utc_date.month, check_date.month)
        self.assertEqual(utc_date.day, check_date.day)
        self.assertEqual(utc_date.hour, check_date.hour)
        self.assertEqual(utc_date.minute, check_date.minute)
        self.assertEqual(utc_date.second, check_date.second)


if __name__ == '__main__':
    unittest.main()
