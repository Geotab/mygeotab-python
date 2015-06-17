# -*- coding: utf-8 -*-

import unittest
from datetime import datetime

import pytz

from mygeotab import utils


class TestGetUtcDate(unittest.TestCase):
    def setUp(self):
        pass

    def test_naive_datetime_to_utc(self):
        date = datetime(2015, 3, 12, 2, 45, 34)
        utc_date = utils.get_utc_date(date)
        self.assertIsNotNone(utc_date.tzinfo)
        self.assertIs(utc_date.tzinfo, pytz.utc)
        self.assertEqual(utc_date.year, date.year)
        self.assertEqual(utc_date.month, date.month)
        self.assertEqual(utc_date.day, date.day)
        self.assertEqual(utc_date.hour, date.hour)

    def test_utc_datetime_to_utc(self):
        date = datetime(2015, 3, 12, 2, 45, 34, tzinfo=pytz.utc)
        utc_date = utils.get_utc_date(date)
        self.assertIsNotNone(utc_date.tzinfo)
        self.assertIs(utc_date.tzinfo, pytz.utc)
        self.assertEqual(utc_date.year, date.year)
        self.assertEqual(utc_date.month, date.month)
        self.assertEqual(utc_date.day, date.day)
        self.assertEqual(utc_date.hour, date.hour)

    def test_zoned_datetime_to_utc(self):
        tz = pytz.timezone('US/Eastern')
        date = tz.localize(datetime(2015, 3, 12, 2, 45, 34))
        utc_date = utils.get_utc_date(date)
        check_date = date.astimezone(pytz.utc)
        self.assertIsNotNone(utc_date.tzinfo)
        self.assertIs(utc_date.tzinfo, pytz.utc)
        self.assertEqual(utc_date.year, check_date.year)
        self.assertEqual(utc_date.month, check_date.month)
        self.assertEqual(utc_date.day, check_date.day)
        self.assertEqual(utc_date.hour, check_date.hour)


if __name__ == '__main__':
    unittest.main()
