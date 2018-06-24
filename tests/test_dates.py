# -*- coding: utf-8 -*-

from datetime import datetime

import pytz

from mygeotab import dates


class TestGetUtcDate:
    def test_naive_datetime_to_utc(self):
        date = datetime(2015, 3, 12, 2, 45, 34)
        utc_date = dates.localize_datetime(date, pytz.utc)
        assert utc_date.tzinfo is not None
        assert utc_date.tzinfo is pytz.utc
        assert utc_date.year == date.year
        assert utc_date.month == date.month
        assert utc_date.day == date.day
        assert utc_date.hour == date.hour

    def test_utc_datetime_to_utc(self):
        date = pytz.utc.localize(datetime(2015, 3, 12, 2, 45, 34))
        utc_date = dates.localize_datetime(date, pytz.utc)
        assert utc_date.tzinfo is not None
        assert utc_date.tzinfo is pytz.utc
        assert utc_date.year == date.year
        assert utc_date.month == date.month
        assert utc_date.day == date.day
        assert utc_date.hour == date.hour

    def test_zoned_datetime_to_utc(self):
        tz = pytz.timezone('US/Eastern')
        date = tz.localize(datetime(2015, 3, 12, 2, 45, 34))
        utc_date = dates.localize_datetime(date, pytz.utc)
        check_date = date.astimezone(pytz.utc)
        assert utc_date.tzinfo is not None
        assert utc_date.tzinfo is pytz.utc
        assert utc_date.year == check_date.year
        assert utc_date.month == check_date.month
        assert utc_date.day == check_date.day
        assert utc_date.hour == check_date.hour

    def test_zoned_min_datetime(self):
        tz_aus = pytz.timezone('Australia/Sydney')
        tz_est = pytz.timezone('America/Toronto')
        date = datetime(1, 1, 1, tzinfo=tz_aus)
        est_date = dates.localize_datetime(date, tz_est)
        check_date = dates.MIN_DATE.astimezone(tz_est)
        assert est_date.tzinfo is not None
        assert est_date.year == check_date.year
        assert est_date.month == check_date.month
        assert est_date.day == check_date.day
        assert est_date.hour == check_date.hour

    def test_zoned_min_datetime(self):
        tz_aus = pytz.timezone('Australia/Sydney')
        tz_est = pytz.timezone('America/Toronto')
        date = datetime(9999, 12, 31, 23, 59,59, 999, tzinfo=tz_est)
        est_date = dates.localize_datetime(date, tz_aus)
        check_date = dates.MAX_DATE.astimezone(tz_aus)
        assert est_date.tzinfo is not None
        assert est_date.year == check_date.year
        assert est_date.month == check_date.month
        assert est_date.day == check_date.day
        assert est_date.hour == check_date.hour

class TestFormatIsoDate:
    def test_format_naive_datetime(self):
        date = datetime(2015, 3, 12, 2, 45, 34)
        check_fmt = '2015-03-12T02:45:34.000Z'
        fmt_date = dates.format_iso_datetime(date)
        assert fmt_date == check_fmt

    def test_format_utc_datetime(self):
        date = pytz.utc.localize(datetime(2015, 3, 12, 2, 45, 34))
        check_fmt = '2015-03-12T02:45:34.000Z'
        fmt_date = dates.format_iso_datetime(date)
        assert fmt_date == check_fmt

    def test_format_local_datetime(self):
        est = pytz.timezone('US/Eastern')
        date = est.localize(datetime(2015, 3, 12, 2, 45, 34, 987000))
        check_fmt = '2015-03-12T06:45:34.987Z'
        fmt_date = dates.format_iso_datetime(date)
        assert fmt_date == check_fmt

    def test_format_outside_min_date(self):
        date = datetime(1, 1, 1, 1, 45, 34, 987000, tzinfo=pytz.utc)
        date_unzoned = datetime(1, 1, 1, 1, 45, 34, 987000)
        check_fmt = '1950-01-01T00:00:00.000Z'
        fmt_date = dates.format_iso_datetime(date)
        fmt_date_unzoned = dates.format_iso_datetime(date_unzoned)
        assert fmt_date == check_fmt
        assert fmt_date_unzoned == check_fmt

    def test_format_outside_max_date(self):
        date = datetime(2800, 1, 1, 1, 45, 34, 987000, tzinfo=pytz.utc)
        date_unzoned = datetime(2800, 1, 1, 1, 45, 34, 987000)
        check_fmt = '2050-01-01T00:00:00.000Z'
        fmt_date = dates.format_iso_datetime(date)
        fmt_date_unzoned = dates.format_iso_datetime(date_unzoned)
        assert fmt_date == check_fmt
        assert fmt_date_unzoned == check_fmt
