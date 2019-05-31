# -*- coding: utf-8 -*-

"""
mygeotab.dates
~~~~~~~~~~~~~~

Date helper objects for timezone shifting and date formatting for the MyGeotab API.
"""

from datetime import datetime

import pytz

MIN_DATE = pytz.utc.localize(datetime(1, 1, 1))
MAX_DATE = pytz.utc.localize(datetime(9999, 12, 31, 23, 59, 59, 999999))


def format_iso_datetime(datetime_obj):
    """Formats the given datetime as a UTC-zoned ISO 8601 date string.

    :param datetime_obj: The datetime object.
    :type datetime_obj: datetime
    :return: The datetime object in 8601 string form.
    :rtype: datetime
    """
    datetime_obj = localize_datetime(datetime_obj, pytz.utc)
    if datetime_obj < MIN_DATE:
        datetime_obj = MIN_DATE
    elif datetime_obj > MAX_DATE:
        datetime_obj = MAX_DATE
    return datetime_obj.replace(tzinfo=None).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def localize_datetime(datetime_obj, tz=pytz.utc):
    """Converts a naive or UTC-localized date into the provided timezone.

    :param datetime_obj: The datetime object.
    :type datetime_obj: datetime
    :param tz: The timezone. If blank or None, UTC is used.
    :type tz: datetime.tzinfo
    :return: The localized datetime object.
    :rtype: datetime
    """
    if not datetime_obj.tzinfo:
        return tz.localize(datetime_obj)
    else:
        try:
            return datetime_obj.astimezone(tz)
        except OverflowError:
            if datetime_obj < datetime(2, 1, 1, tzinfo=pytz.utc):
                return MIN_DATE.astimezone(pytz.utc)
            return MAX_DATE.astimezone(pytz.utc)
