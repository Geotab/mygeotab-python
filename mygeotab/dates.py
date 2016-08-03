# -*- coding: utf-8 -*-

from datetime import datetime

import pytz


def format_iso_datetime(dt):
    """
    Formats the given datetime as a UTC-zoned ISO 8601 date string

    :param dt: The datetime object
    :return: The datetime object in 8601 string form
    """
    dt = localize_datetime(dt, pytz.utc)
    return dt.replace(tzinfo=None).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def localize_datetime(dt, tz=pytz.utc):
    """
    Converts a naive or UTC-localized date into the provided timezone

    :rtype: datetime
    :param dt: The datetime object
    :param tz: The timezone. If blank or None, UTC is used
    :return: The localized datetime object
    """
    if not dt.tzinfo:
        return tz.localize(dt)
    else:
        return dt.astimezone(tz)
