# -*- coding: utf-8 -*-

"""
mygeotab.dates
~~~~~~~~~~~~~~

Date helper objects for timezone shifting and date formatting for the MyGeotab API.
"""

from datetime import datetime

import pytz


def format_iso_datetime(datetime_obj):
    """Formats the given datetime as a UTC-zoned ISO 8601 date string.

    :param datetime_obj: The datetime object.
    :return: The datetime object in 8601 string form.
    """
    datetime_obj = localize_datetime(datetime_obj, pytz.utc)
    return datetime_obj.replace(tzinfo=None).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def localize_datetime(datetime_obj, tz=pytz.utc):
    """Converts a naive or UTC-localized date into the provided timezone.

    :rtype: datetime
    :param datetime_obj: The datetime object.
    :param tz: The timezone. If blank or None, UTC is used.
    :return: The localized datetime object.
    """
    if not datetime_obj.tzinfo:
        return tz.localize(datetime_obj)
    else:
        return datetime_obj.astimezone(tz)
