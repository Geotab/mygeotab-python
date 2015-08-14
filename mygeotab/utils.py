# -*- coding: utf-8 -*-

from datetime import datetime

import pytz
from tzlocal import get_localzone


def datetime_to_iso8601(dt):
    """
    Formats the given datetime as a UTC-zoned ISO 8601 date string

    :param dt: The datetime object
    :return: The datetime object in 8601 string form
    """
    dt = localize_datetime(dt, pytz.utc)
    return dt.replace(tzinfo=None).isoformat() + 'Z'


def parse_iso8601_datetime(iso_date):
    """
    Parses an ISO 8601 date string into a datetime object

    :param iso_date: The date string
    :return: The datetime object which represents the ISO 8601 string
    """
    return datetime.strptime(iso_date, "%Y-%m-%dT%H:%M:%S.%fZ")


def localize_datetime(dt, tz=None):
    """
    Converts a naive or UTC-localized date into the provided timezone or current machine's timezone

    :param dt: The datetime object
    :param tz: The timezone. If blank or None, the user's native timezone is used
    :return: The localized datetime object
    """
    tz = tz or get_localzone()
    if not dt.tzinfo:
        return tz.localize(dt)
    else:
        return dt.astimezone(tz)
